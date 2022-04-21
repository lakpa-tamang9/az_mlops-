#!/usr/bin/python3
import os

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azureml.core import Dataset, Datastore, Workspace
import json
import argparse


class PrepareDataset:
    """
    Prepare dataset by connecting workspace to azure data lake.
        - Create data store by registering the blob container into the workspace
        - From the datastore, retrive name and path of the data and convert into 
        tabular dataset form within the workspace.
    """

    def __init__(self) -> None:
        # Retrieve keyvault client
        # try:
        #     # user_assigned_identity = "18557749-e8fa-437a-aa40-dc46986b022b"
        #     key_vault_name = os.environ["KEY_VAULT_NAME"]
        #     # client_ID = os.environ["AZURE_CLIENT_ID"]
        #     key_vault_uri = f"https://{key_vault_name}.vault.azure.net"
        #     # key_vault_uri = f"https://hsdsecrets.vault.azure.net"
        #     credential = DefaultAzureCredential()
        #     # credential = ClientSecretCredential(tenant_id = '3417d36b-fa61-4b84-b95e-8414a4e5753f',
        #     # client_id = '3e43fe3e-52da-4f55-b82d-5f549747aebc', client_secret = 'he28Q~aWF3BYYBiO-RkQp9GHEZ_vuUrOCHgbLbFW')
        #     client = SecretClient(vault_url=key_vault_uri, credential=credential)
        # except Exception as error:
        #     print(error)
        parser = argparse.ArgumentParser(description="Add secrets from key vault")
        parser.add_argument("--location", type=str, help="Location")
        parser.add_argument("--account_key", type=str, help="Account key")
        parser.add_argument("--account_name", type=str, help="Name of the account")
        parser.add_argument("--container_name", type=str, help="Name of the container")
        parser.add_argument("--resource_group", type=str, help="Resource group name")
        parser.add_argument("--service_name", type=str, help="Service name for staging in ACI")
        parser.add_argument("--sub_id", type=str, help="Subscription ID")
        parser.add_argument("--workspace", type=str, help="Name of the workspace")

        args = parser.parse_args()


        # Retrieve account and storage details
        # self.rg = client.get_secret("RESOURCE-GROUP").value
        # self.subscription_id = client.get_secret("SUB-ID").value
        # self.location = client.get_secret("LOCATION").value
        # ws = client.get_secret("WORKSPACE").value

        # # Datalake information
        # self.storage_account_name = client.get_secret("ACCOUNT-NAME").value
        # self.container_name = client.get_secret("CONTAINER-NAME").value
        # self.storage_account_key = client.get_secret("ACCOUNT-KEY").value

        self.rg = args.resource_group
        self.subscription_id = args.sub_id
        self.location = args.location
        ws = args.workspace

        # Datalake information
        self.storage_account_name = args.account_name
        self.container_name = args.container_name
        self.storage_account_key = args.account_key
        try:
            with open("./training/dataset_config.json") as f:
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

            dataset = dataset.register(
                workspace=self.ws,
                name=self.dataset_config["dataset_name"],
                description=self.dataset_config["dataset_desc"],
                create_new_version=True
            )
        except Exception as e:
            print(e)
            print("Error while registering the dataset")


preparedataset = PrepareDataset()
preparedataset.create_dataset()
