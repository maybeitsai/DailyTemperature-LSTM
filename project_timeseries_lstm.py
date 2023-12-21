# -*- coding: utf-8 -*-
"""project-timeseries-LSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lE02LjtcxiQmchKujqR89TrfdYexhLbH
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,LSTM,Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import mean_absolute_error

from google.colab import drive
drive.mount('/content/drive')

df= pd.read_csv('/content/drive/MyDrive/city_temperature.csv')

df.shape

df.info()

df['Region'].unique()

df['Country'].unique()

"""## Jepang"""

df_japan = df[df['Country']=='Japan']

df_japan.shape

df_japan.describe()

avg_temp = 'AvgTemperature'

sns.boxplot(data=df_japan[[avg_temp]])
plt.title(f'Boxplot for {avg_temp}')
plt.show()

def clean_outliner(data,start_quantile,end_quantile) :
  data = data.copy()
  Q1 = data.quantile(start_quantile)
  Q3 = data.quantile(end_quantile)
  IQR = Q3 - Q1
  return(data >= Q1 - 1.5 * IQR) & (data <= Q3 + 1.5 *IQR)

df_clean = df_japan.loc[clean_outliner(df_japan[avg_temp],0.25,0.75)]

sns.boxplot(data=df_clean[[avg_temp]])
plt.title(f'Boxplot without outliers for {avg_temp}')
plt.show()

new_df = df_clean.copy()
new_df['Date'] = pd.to_datetime(df_clean[['Year', 'Month', 'Day']])
new_df.head()

final_df = new_df.drop(['Region', 'Country', 'State', 'City', 'Month', 'Day', 'Year'], axis=1)
final_df = final_df[['Date', 'AvgTemperature']]
final_df.head()

fig=plt.figure(figsize=(15,8))
ax=sns.lineplot(data=final_df ,x="Date",y="AvgTemperature")
plt.title("Average Temperature in Japan",size=20,weight="bold")

X = final_df['AvgTemperature'].values.reshape(-1, 1)

train, data_test= train_test_split(X,test_size=0.2,shuffle=False)
data_train,data_val=train_test_split(train,test_size=0.2,shuffle=False)

sc = MinMaxScaler(feature_range = (0, 1))
train_scaled = sc.fit_transform(data_train)
val_scaled = sc.fit_transform(data_val)
test_scaled = sc.fit_transform(data_test)

import numpy as np
input_size = 100
def prepare_data(data, input_size):
    X, y = [], []
    for i in range(input_size, len(data)):
        X.append(data[i - input_size:i, 0])
        y.append(data[i, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y

# Training Data
X_train, y_train = prepare_data(train_scaled, input_size)

# Validation Data
X_val, y_val = prepare_data(val_scaled, input_size)

# Test Data
X_test, y_test = prepare_data(test_scaled, input_size)

model=Sequential([
    LSTM(64, return_sequences= True ,input_shape =(X_train.shape[1],1)),
    Dropout(0.25),
    LSTM(128, return_sequences= True),
    Dropout(0.25),
    LSTM(256, return_sequences= True),
    Dropout(0.25),
    LSTM(128, return_sequences= True),
    Dropout(0.25),
    LSTM(64),
    Dropout(0.25),
    Dense(1)
])
model.summary()

callbacks = [
    EarlyStopping(monitor='mae', patience=10, verbose=1, restore_best_weights=True),
    ModelCheckpoint(filepath='best_model.h5', monitor='mae', save_best_only=True, verbose=1),
    ReduceLROnPlateau(factor=0.5, patience=10, min_lr=0.000001, verbose=1)
]

model.compile(loss=tf.keras.losses.Huber(),optimizer=Adam(learning_rate=0.0001),metrics= ["mae"])

history = model.fit(
    X_train,y_train,
    validation_data=(X_val,y_val),
    epochs=100,
    callbacks=callbacks,
    batch_size=32
)

# Plot MAE (Mean Absolute Error)
plt.figure(figsize=(12, 6))
plt.plot(history.history['mae'], label='Training MAE')
plt.plot(history.history['val_mae'], label='Validation MAE')
plt.title('Model Mean Absolute Error (MAE)')
plt.xlabel('Epoch')
plt.ylabel('MAE')
plt.legend()
plt.show()

# Plot Loss
plt.figure(figsize=(12, 6))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()