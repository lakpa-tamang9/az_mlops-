from azureml.core import Workspace, Environment
from azureml.core.model import Model, InferenceConfig
from azureml.core.webservice import AciWebservice
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
from azureml.core.authentication import ServicePrincipalAuthentication
import argparse


def main():
    # Get key vault name from the variable group as argument.
    parser = argparse.ArgumentParser(description="Argument for key vault name")
    parser.add_argument("--kv_name", type=str, help="Name of the key vault")
    parser.add_argument("--az_client_secret", type=str, help="Client secret")
    parser.add_argument("--az_tenant_ID", type=str, help="Tenant ID")
    parser.add_argument("--az_client_ID", type=str, help="Client ID")
    parser.add_argument("--resource_group", type=str, help="Resource group")
    parser.add_argument("--workspace", type=str, help="ML workspace name")
    args = parser.parse_args()

    # Access key vault token using default azure credentials
    key_vault_uri = f"https://{args.kv_name}.vault.azure.net"
    credential = DefaultAzureCredential()

    # Create client to get secrets from key vault
    client = SecretClient(vault_url=key_vault_uri, credential=credential)

    # Retrieve secrets from the key vault
    subscription_id = client.get_secret("SUB-ID").value
    service_name_staging = client.get_secret("SERVICE-NAME").value

    # Setting up a ML workflow as an automated process via service principal authentication
    service_principal = ServicePrincipalAuthentication(
        tenant_id=args.az_tenant_ID,
        service_principal_id=args.az_client_ID,
        service_principal_password=args.az_client_secret,
    )

    # Create workspace by authenticating with service principal
    try:
        workspace = Workspace(
            subscription_id=subscription_id,
            resource_group=args.resource_group,
            workspace_name=args.workspace,
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


if __name__ == "__main__":
    main()
