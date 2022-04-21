from azureml.core import Workspace, Environment
from azureml.core.model import Model, InferenceConfig
from azureml.core.webservice import AciWebservice
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
from azureml.core.authentication import ServicePrincipalAuthentication

key_vault_name = os.environ["KEY_VAULT_NAME"]
azure_client_secret = os.environ["AZURE_CLIENT_SECRET"]
azure_tenanat_id = os.environ["AZURE_TENANT_ID"]
azure_client_id = os.environ["AZURE_CLIENT_ID"]
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

service_principal = ServicePrincipalAuthentication(
    tenant_id=azure_tenanat_id,
    service_principal_id=azure_client_id,
    service_principal_password=azure_client_secret,
)

try:
    workspace = Workspace(
        subscription_id=subscription_id,
        resource_group=resource_group_name,
        workspace_name=workspace_name,
        auth=service_principal,
    )
    print("The workspace is created successfully")

except Exception as e:
    print(e)

# Register the model
try:
    latest_registered_model = Model.list(workspace)[0]
except Exception:
    print("No registered model found")
env = Environment(name="project_environment")

# Specify the python packages for installing
python_packages = ["numpy", "onnxruntime"]
for package in python_packages:
    env.python.conda_dependencies.add_pip_package(package)

# Specify the inference configuration
inference_config = InferenceConfig(
    environment=env,
    entry_script="score.py",
)

# Specify the deployment configuration
deployment_config = AciWebservice.deploy_configuration(
    cpu_cores=1, memory_gb=1, auth_enabled=True
)

# Deploy the service
service = Model.deploy(
    workspace,
    service_name_staging,
    [latest_registered_model],
    inference_config,
    deployment_config,
    overwrite=True,
)
service.wait_for_deployment(show_output=True)
key, _ = service.get_keys()
print(f"Deployment is completed. The service key = {key}")
