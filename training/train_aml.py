from azureml.core.run import Run
from azureml.core import Dataset, Datastore, Workspace
import os
import argparse
import json
from train import split_data, train_model, get_model_metrics
from prepare_dataset import PrepareDataset
import onnxmltools


def register_dataset(
    aml_workspace: Workspace,
    dataset_name: str,
    datastore_name: str,
    file_path: str
) -> Dataset:
    datastore = Datastore.get(aml_workspace, datastore_name)
    dataset = Dataset.Tabular.from_delimited_files(path=(datastore, file_path))
    dataset = dataset.register(workspace=aml_workspace,
                               name=dataset_name,
                               create_new_version=True)

    return dataset


def main():
    preparedataset = PrepareDataset()
    print("Running train_aml.py")

    parser = argparse.ArgumentParser("train")
    parser.add_argument(
        "--model_name",
        type=str,
        help="Name of the Model",
        default="anomaly_predict.onnx",
    )

    parser.add_argument(
        "--data_file_path",
        type=str,
        help=("data file path, if specified,a new version of the dataset will be registered"),
        default="anomaly",
    )

    parser.add_argument(
        "--dataset_name",
        type=str,
        help="Dataset name",
        default="anomaly_dataset",
    )

    args = parser.parse_args()

    print("Argument [model_name]: %s" % args.model_name)
    print("Argument [data_file_path]: %s" % args.data_file_path)
    print("Argument [dataset_name]: %s" % args.dataset_name)

    model_name = args.model_name
    data_file_path = args.data_file_path
    dataset_name = args.dataset_name

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
      
    # Get dataset from datalake
    try:
        dataset = preparedataset.create_dataset()
    except Exception as error:
        print(error)
    print(dataset)

    # Get the dataset
    # if (dataset_name):
    #     if (data_file_path == 'none'):
    #         dataset = Dataset.get_by_name(run.experiment.workspace, dataset_name)  # NOQA: E402, E501
    #     else:
    #         dataset = register_dataset(run.experiment.workspace,
    #                                    dataset_name,
    #                                    "workspaceblobstore",
    #                                    data_file_path)
    # else:
    #     e = ("No dataset provided")
    #     print(e)
    #     raise Exception(e)

    # Link dataset to the step run so it is trackable in the UI
    run.input_datasets['training_data'] = dataset
    #run.parent.tag("dataset_id", value=dataset.id)

    # Split the data into test/train
    df = dataset.to_pandas_dataframe()
    data = split_data(df)

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