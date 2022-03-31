import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.model_selection import train_test_split
from tensorflow import keras
import matplotlib.pyplot as plt

# Split the dataframe into test and train data

def prepare_data(data_df):
    # Define columns to dump
    COL_DUM = ['SHUTDOWN_SELECTED','ALARM_SELECTED','WARNING_SELECTED',
            'BU2700_RUN','FD2791_IN','IGT2793_ON',
            'BL2501_RUN']
    data_df.drop('MNT_DAT_PK',axis=1,inplace=True) # removing the columns feature
    data_df.drop('DATA_TIME',axis=1,inplace=True)

    # Replace the boolean values with the binary values.
    for v in COL_DUM:
        dummies = pd.get_dummies(data_df[v], prefix=v)
        data=pd.concat([data_df,dummies],axis=1) # concatenating two data frames horizontally
        data.drop(v,axis=1,inplace=True)    # dropping the original columns, inplace is set true in order if dont need to reassign df again.

    return data

def split_data(df, target = 'T1101', test_size = 0.2):
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
    model.compile(loss = args["training"]["loss"], optimizer = args["training"]["optimizer"])
    model.fit(x_train, y_train, epochs = args["training"]["epochs"])
    return model

def get_model_metrics(model, data):
    x_test, y_test = data["test"]["X"], data["test"]["y"]

    # Predict using the trained model
    pred_arr = model.predict(x_test)
    arr = y_test.values()

    fig=plt.figure(facecolor='white',figsize=(14,14))
    ax=fig.add_subplot(1,1,1)
    # ax.set(xlim=[0,44052],ylim=[-10000,10000],title='Temperature Prediction',xlabel='time',ylabel='Temperature')
    ax.set(xlim=[0,int(data.shape[0]*0.2)],ylim=[0,400],title='Temperature Prediction',xlabel='time',ylabel='Temperature')
    ax.plot(arr,'r',label='True')
    ax.plot(pred_arr,'b',label='Prediction')
    ax.legend()
    plt.show()

    y_test_arr=arr.reshape((data.shape[0]+1,1))
    # Get the error value between predicted and real data
    error=((y_test_arr-pred_arr)/y_test_arr)*100
    model_metrics = {"error" : error}
    return model_metrics