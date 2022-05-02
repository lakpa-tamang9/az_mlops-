import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azureml.core import Dataset, Datastore, Workspace
import json
import argparse
from azureml.core.authentication import ServicePrincipalAuthentication


class PrepareDataset:
    """
    Prepare dataset by connecting workspace to azure data lake.
        - Create data store by registering the blob container into the workspace
        - From the datastore, retrive name and path of the data and convert into
        tabular dataset form within the workspace.
    """

    def __init__(self) -> None:
        # Add arguments for executing the scripts
        # These arguments are directly loaded from the variable groups
        # and called in CI yaml pipeline.
        parser = argparse.ArgumentParser(description="Argument for key vault name")
        parser.add_argument("--kv_name", type=str, help="Name of the key vault")
        parser.add_argument("--az_client_secret", type=str, help="Client secret")
        parser.add_argument("--az_tenant_ID", type=str, help="Tenant ID")
        parser.add_argument("--az_client_ID", type=str, help="Client ID")
        parser.add_argument("--resource_group", type=str, help="Resource group")
        parser.add_argument("--workspace", type=str, help="ML workspace name")
        parser.add_argument("--location", type=str, help="Resource group location")
        parser.add_argument(
            "--storage_account_name", type=str, help="Name of the storage account"
        )
        parser.add_argument("--container_name", type=str, help="Name of the container")
        args = parser.parse_args()

        # Parse the values
        self.key_vault_name = args.kv_name
        self.azure_client_secret = args.az_client_secret
        self.azure_tenanat_id = args.az_tenant_ID
        self.azure_client_id = args.az_client_ID
        self.resource_group = args.resource_group
        self.w_space = args.workspace
        self.location = args.location
        self.storage_account_name = args.storage_account_name
        self.container_name = args.container_name

        # Access key vault token using default azure credentials
        key_vault_uri = f"https://{self.key_vault_name}.vault.azure.net"
        credential = DefaultAzureCredential()

        # Create client to get secrets from key vault
        client = SecretClient(vault_url=key_vault_uri, credential=credential)

        # Retrieve subscription ID and account key from key vault
        self.subscription_id = client.get_secret("SUB-ID").value
        self.storage_account_key = client.get_secret("ACCOUNT-KEY").value

        # Load dataset configuration
        try:
            with open("./training/dataset_config.json") as f:
                self.dataset_config = json.load(f)
        except Exception:
            print("Cannot load dataset configuration.")

        # Setting up a ML workflow as an automated process via service principal authentication
        service_principal = ServicePrincipalAuthentication(
            tenant_id=self.azure_tenanat_id,
            service_principal_id=self.azure_client_id,
            service_principal_password=self.azure_client_secret,
        )

        # Create workspace by authenticating with service principal
        self.workspace = Workspace(
            workspace_name=self.w_space,
            subscription_id=self.subscription_id,
            resource_group=self.resource_group,
            auth=service_principal,
        )

    def create_dataset(self):
        """
        - Link datastore with data lake gen 2 as a blob storage
        - Create dataset using datastore and register it into the same ws.
        """
        try:
            Datastore.register_azure_blob_container(
                workspace=self.workspace,
                datastore_name=self.dataset_config["datastore_name"],
                container_name=self.container_name,
                account_name=self.storage_account_name,
                account_key=self.storage_account_key,
            )
        except Exception as e:
            print(e)

        try:
            datastore = Datastore.get(
                self.workspace, self.dataset_config["datastore_name"]
            )

            datastore_path = [(datastore, self.dataset_config["data_path"])]
            dataset = Dataset.Tabular.from_delimited_files(datastore_path)

            dataset = dataset.register(
                workspace=self.workspace,
                name=self.dataset_config["dataset_name"],
                description=self.dataset_config["dataset_desc"],
                create_new_version=True,
            )
        except Exception as e:
            print(f"Error while registering the dataset because of {e}")


preparedataset = PrepareDataset()
preparedataset.create_dataset()
