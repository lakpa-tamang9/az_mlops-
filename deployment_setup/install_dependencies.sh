#!/bin/bash
python --version
pip install --upgrade azure-cli
pip install --upgrade azureml-sdk
pip install azureml-core

pip install azureml-defaults
# Scoring deps
pip install inference-schema[numpy-support]

# MLOps with R
pip install azure-storage-blob

# onnx converter for model
pip install onnxmltools
pip install tf2onnx
pip install onnxruntime
pip install azureml-core
pip install azure-identity
pip install azure-keyvault
pip install azure-keyvault-secrets
