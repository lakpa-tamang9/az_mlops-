import json
import onnxruntime
import numpy as np
import os
from azureml.core.model import Model

def init():
    global session
    print("The init methoed for file")
    model_path = Model.get_model_path(model_name = "anomaly_onnx")
    session = onnxruntime.InferenceSession(model_path)

def run(data):
    data = json.loads(data)
    data = data["input"]
    test_data = np.expand_dims(np.array(data), axis = 1).astype('float32').reshape(1, -1)
    test = session.run(None, {"dense_input": test_data})
    output = {"predicated": test[0].tolist()[0][0]}
    # predicted_value = json.dumps(output)
    return output