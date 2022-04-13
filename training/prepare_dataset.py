import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azureml.core import Dataset, Datastore, Workspace
import json


class PrepareDataset:
    """_summary_
    """
    def __init__(self) -> None:
        # Retrieve keyvault client
        try:
            key_vault_name = os.environ["KEY_VAULT_NAME"]
            key_vault_uri = f"https://{key_vault_name}.vault.azure.net"
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_uri, credential=credential)
        except Exception as error:
            print(error)

        # Retrieve account and storage details
        self.rg = client.get_secret("RESOURCE-GROUP").value
        self.subscription_id = client.get_secret("SUB-ID").value
        self.location = client.get_secret("LOCATION").value
        ws = client.get_secret("WORKSPACE").value
        self.storage_account_name = client.get_secret("ACCOUNT-NAME").value
        self.container_name = client.get_secret("CONTAINER-NAME").value
        self.storage_account_key = client.get_secret("ACCOUNT-KEY").value
        try:
            with open("dataset_config.json") as f:
                self.dataset_config = json.load(f)
        except Exception:
            print("Cannot load dataset configuration.")

        self.ws = Workspace.get(
            name=ws,
            subscription_id=self.subscription_id,
            resource_group=self.rg,
            location=self.location,
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

            dataset.register(
                workspace=self.ws,
                name=self.dataset_config["dataset_name"],
                description=self.dataset_config["dataset_desc"],
            )
        except Exception as e:
            print(e)
            print("Could not register dataset")
