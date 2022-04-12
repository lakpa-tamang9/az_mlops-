from azureml.core import Workspace, Environment
from azureml.core.model import Model, InferenceConfig
from azureml.core.webservice import AciWebservice

ws = Workspace(subscription_id="7cd27cfd-2ba5-4907-a46b-b0eb4b992636", resource_group="hsd_resource_group", workspace_name="hsd_ml_workspace")

# Register the model
try:
    latest_registered_model = Model.list(ws)[-1]    
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
with open("configuration.json") as f:
    pars = json.load(f)

# Deploy the service
service = Model.deploy(
    ws,
    pars["configs"]["service_name_staging"],
    [latest_registered_model],
    inference_config,
    deployment_config,
    overwrite=True,
)
service.wait_for_deployment(show_output=True)
key, _ = service.get_keys()
print(f"Deployment is completed. The service key = {key}")


