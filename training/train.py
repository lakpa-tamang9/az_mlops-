import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.model_selection import train_test_split
from tensorflow import keras
import matplotlib.pyplot as plt
import json

# Split the dataframe into test and train data

def prepare_data(data_df):
    # Define columns to dump
    col_dum = ['SHUTDOWN_SELECTED','ALARM_SELECTED','WARNING_SELECTED',
            'BU2700_RUN','FD2791_IN','IGT2793_ON',
            'BL2501_RUN']
    my_frame = data_df.drop('MNT_DAT_PK',axis=1) # removing the columns feature
    data = my_frame.drop('DATA_TIME',axis=1)

# Replace the boolean values with the binary values.
    for v in col_dum:
        # print(data[v].shape)
        dummies = pd.get_dummies(data[v], prefix=v)
        # print(dummies)
        data=pd.concat([data,dummies],axis=1) # concatenating two data frames horizontally
        # print(dummies.shape)
        # print(modified_data.shape)
        data.drop(v,axis=1,inplace=True)    # dropping the original columns, inplace is set true in order if dont need to reassign df again.
        # print(data[v])
    return data

def split_data(df, test_size, target):
    # df = prepare_data(data_df)
    x = df.drop(target,axis=1)
    y = df.loc[:, target]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = test_size,shuffle = False)
    dataset = {"train" : {"X" : x_train, "y" : y_train},
    "test" : {"X" : x_test, "y" : y_test}}
    return dataset

def train_model(dataset, args):
    # ② 모델 정의
    x_train, y_train = dataset["train"]["X"], dataset["train"]["y"]
    model = keras.models.Sequential()
    # ③ 블록 준비
    model.add(keras.layers.Dense(100, input_shape = (x_train.shape[1],), activation='relu'))
    model.add(keras.layers.Dense(40, input_shape = (100,), activation='relu'))
    model.add(keras.layers.Dense(20, input_shape = (40,), activation='relu'))
    model.add(keras.layers.Dense(1))

    # ⑤ Compile
    model.compile(loss = args["loss"], optimizer = args["optimizer"])
    model.fit(x_train, y_train, epochs = args["epochs"])
    return model

def feature_selection(dataframe):
    with open("feature_dict.json") as f:
        features = json.load(f)
    selected_features = []
    for feats in features["features"]:
        if feats not in dataframe.columns.tolist():
            white_space_removed = feats.split(" ")[-1]
            if white_space_removed != "IGT2793_ON":
                selected_features.append(white_space_removed)
    return dataframe[selected_features]

def get_model_metrics(model, data):
    x_test, y_test = data["test"]["X"], data["test"]["y"]
    x_train, y_train = data["train"]["X"], data["train"]["y"]
    data_shape = x_train.shape[0] + x_test.shape[0]

    # Predict using the trained model
    pred_arr = model.predict(x_test)
    # abb = y_train.values()
    y_test_arr = np.expand_dims(y_test, axis = 1)
    # print(y_test_arr)
    # arr = y_test.values()

    fig=plt.figure(facecolor='white',figsize=(14,14))
    ax=fig.add_subplot(1,1,1)
    # ax.set(xlim=[0,44052],ylim=[-10000,10000],title='Temperature Prediction',xlabel='time',ylabel='Temperature')
    ax.set(xlim=[0,int(data_shape*0.2)],ylim=[0,400],title='Temperature Prediction',xlabel='time',ylabel='Temperature')
    ax.plot(y_test_arr,'r',label='True')
    ax.plot(pred_arr,'b',label='Prediction')
    ax.legend()
    plt.show()

    y_test_arr_final=y_test_arr.reshape((x_test.shape[0],1))
    # Get the error value between predicted and real data
    error=((y_test_arr_final-pred_arr)/y_test_arr_final)*100
    model_metrics = {"error" : error}
    return model_metrics