import json
from urllib import response
import onnxruntime
import numpy as np
import os
from azureml.core.model import Model

def init():
    global session
    print("The init methoed for file")
    model_path = Model.get_model_path(model_name = "anomaly_predict")
    session = onnxruntime.InferenceSession(model_path)

def run(data):
    min_data = json.loads(data)
    result = {
        "predicated":[]
    }
    # TODO: Validate the input data before sending it for predication
    # Validation using length of input,and value of input
    # TODO: Use algorithm to avoid predication for each value
    for feature in min_data["features"]:
        feature = np.expand_dims(np.array(feature), axis = 1).astype('float32').reshape(1, -1)
        predication = session.run(None, {"dense_input": feature})
        result["predicated"].append(predication)
    return result