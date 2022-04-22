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
        # Retrieve keyvault client
        parser = argparse.ArgumentParser(description="Argument for key vault name")
        parser.add_argument("--kv_name", type=str, help="Name of the key vault")
        parser.add_argument("--az_client_secret", type=str, help="Client secret")
        parser.add_argument("--az_tenant_ID", type=str, help="Tenant ID")
        parser.add_argument("--az_client_ID", type=str, help="Client ID")
        args = parser.parse_args()

        # Parse the values
        key_vault_name = args.kv_name
        azure_client_secret = args.az_client_secret
        azure_tenanat_id = args.az_tenant_ID
        azure_client_id = args.az_client_ID

        print(
            f"{key_vault_name}, \n{azure_client_secret}, \n{azure_tenanat_id}, \n{azure_client_id}"
        )
        key_vault_uri = f"https://{key_vault_name}.vault.azure.net"
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_uri, credential=credential)

        # Retrieve account and storage details
        self.rg = client.get_secret("RESOURCE-GROUP").value
        self.subscription_id = client.get_secret("SUB-ID").value
        self.location = client.get_secret("LOCATION").value
        ws = client.get_secret("WORKSPACE").value

        # Datalake information
        self.storage_account_name = client.get_secret("ACCOUNT-NAME").value
        self.container_name = client.get_secret("CONTAINER-NAME").value
        self.storage_account_key = client.get_secret("ACCOUNT-KEY").value

        try:
            with open("./training/dataset_config.json") as f:
                self.dataset_config = json.load(f)
        except Exception:
            print("Cannot load dataset configuration.")

        # Define service principal
        service_principal = ServicePrincipalAuthentication(
            tenant_id=azure_tenanat_id,
            service_principal_id=azure_client_id,
            service_principal_password=azure_client_secret,
        )

        # Create workspace by authenticating with service principal
        self.ws = Workspace(
            workspace_name=ws,
            subscription_id=self.subscription_id,
            resource_group=self.rg,
            auth=service_principal,
        )
        print(
            "Found workspace {} at location {}".format(self.ws.name, self.ws.location)
        )

    def create_dataset(self):
        """
        - Link datastore with data lake gen 2 as a blob storage
        - Create dataset using datastore and register it into the same ws.
        """
        try:
            Datastore.register_azure_blob_container(
                workspace=self.ws,
                datastore_name=self.dataset_config["datastore_name"],
                container_name=self.container_name,
                account_name=self.storage_account_name,
                account_key=self.storage_account_key,
            )
        except Exception as e:
            print(e)

        try:
            datastore = Datastore.get(self.ws, self.dataset_config["datastore_name"])

            datastore_path = [(datastore, self.dataset_config["data_path"])]
            dataset = Dataset.Tabular.from_delimited_files(datastore_path)

            dataset = dataset.register(
                workspace=self.ws,
                name=self.dataset_config["dataset_name"],
                description=self.dataset_config["dataset_desc"],
                create_new_version=True,
            )
        except Exception as e:
            print(e)
            print("Error while registering the dataset")


preparedataset = PrepareDataset()
preparedataset.create_dataset()
