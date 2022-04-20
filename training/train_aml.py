import argparse
import json
import os

import onnxmltools
from azureml.core import Dataset, Datastore, Workspace
from azureml.core.run import Run

from train import *


def main():
    print("Running train_aml.py")

    parser = argparse.ArgumentParser("train")
    parser.add_argument(
        "--model_name",
        type=str,
        help="Name of the Model",
        default="anomaly_predict.onnx",
    )

    try:
        with open("dataset_config.json") as f:
            pars = json.load(f)
    except Exception as e:
        print(e)
        
    dataset_name = pars["dataset_name"]

    args = parser.parse_args()
    model_name = args.model_name

    run = Run.get_context()

    print("Getting training parameters")

    # Load the training parameters from the parameters file
    with open("parameters.json") as f:
        pars = json.load(f)
    try:
        train_args = pars["training"]
    except KeyError:
        print("Could not load training values from file")
        train_args = {}

    # Log the training parameters
    print(f"Parameters: {train_args}")
    for (k, v) in train_args.items():
        run.log(k, v)
        #run.parent.log(k, v)

    # Get the dataset by name
    dataset = Dataset.get_by_name(run.experiment.workspace, dataset_name)  # NOQA: E402, E501

    # Link dataset to the step run so it is trackable in the UI
    run.input_datasets['training_data'] = dataset
    #run.parent.tag("dataset_id", value=dataset.id)

    # Split the data into test/train
    df = dataset.to_pandas_dataframe()

    # Select the features
    with open("feature_dict.json") as f:
        features = json.load(f)
    processed_dataset = df.drop(df.columns.difference(features["features"]), 1)
    # processed_dataset = feature_selection(df, features["features"])
    data = split_data(processed_dataset,test_size=0.2, features=features["key_feature"])

    # Train the model
    model = train_model(data, train_args)
    # convert to onnx format
    onnx_model = onnxmltools.convert_keras(model) 

    # Evaluate and log the metrics returned from the train function
    metrics = get_model_metrics(model, data)
    for (k, v) in metrics.items():
        run.log(k, v)
        #run.parent.log(k, v)

    # Also upload model file to run outputs for history
    os.makedirs('outputs', exist_ok=True)
    output_path = os.path.join('outputs', model_name)
    
    # Saving the trained model
    onnxmltools.utils.save_model(onnx_model, output_path)

    run.tag("run_type", value="train")
    print(f"tags now present for run: {run.tags}")

    # upload the model file explicitly into artifacts
    print("Uploading the model into run artifacts...")
    run.upload_file(name="./outputs/models/" + model_name, path_or_stream=output_path)
    print("Uploaded the model {} to experiment {}".format(model_name, run.experiment.name))
    dirpath = os.getcwd()
    print(dirpath)
    print("Following files are uploaded ")
    print(run.get_file_names())

    run.complete()


if __name__ == '__main__':
    main()
