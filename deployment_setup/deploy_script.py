from azureml.core import Workspace, Environment
from azureml.core.model import Model, InferenceConfig
from azureml.core.webservice import AciWebservice
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import json
import os

key_vault_name = os.environ["KEY_VAULT_NAME"]
key_vault_uri = f"https://{key_vault_name}.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_uri, credential=credential)

# Retrieve account and storage details
resource_group_name = client.get_secret("RESOURCE-GROUP").value
subscription_id = client.get_secret("SUB-ID").value
location = client.get_secret("LOCATION").value
workspace_name = client.get_secret("WORKSPACE").value
storage_account_name = client.get_secret("ACCOUNT-NAME").value
container_name = client.get_secret("CONTAINER-NAME").value
storage_account_key = client.get_secret("ACCOUNT-KEY").value
service_name_staging = client.get_secret("SERVICE-NAME").value


# Create the workspace with loaded deployment configs
try: 
    ws = Workspace(subscription_id = subscription_id, 
    resource_group = resource_group_name, 
    workspace_name = workspace_name)
    print("The workspace is created successfully")

except Exception:
    print("Cannot create workspace. Please check the configuration settings.")

# Register the model
try:
    latest_registered_model = Model.list(ws)[0]   
except Exception:
    print("No registered model found")
env = Environment(name="project_environment")

# Specify the python packages for installing
python_packages = ['numpy', 'onnxruntime']
for package in python_packages:
    env.python.conda_dependencies.add_pip_package(package)

# Specify the inference configuration
inference_config = InferenceConfig(
    environment=env,
    entry_script="score.py",)

# Specify the deployment configuration
deployment_config = AciWebservice.deploy_configuration(
cpu_cores=1, memory_gb=1, auth_enabled=True
)

# Load the configs containing name for the service name staging

# Deploy the service
service = Model.deploy(
    ws,
    service_name_staging,
    [latest_registered_model],
    inference_config,
    deployment_config,
    overwrite=True,
)
service.wait_for_deployment(show_output=True)
key, _ = service.get_keys()
print(f"Deployment is completed. The service key = {key}")


