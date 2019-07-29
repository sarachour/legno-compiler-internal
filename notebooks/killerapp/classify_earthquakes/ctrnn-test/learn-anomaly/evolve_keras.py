
import numpy
import matplotlib.pyplot as plt
import pandas
import math

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

import util
import anomaly
import json

DATAGEN = anomaly.HeartRNNAnomaly(8)

def create_dataset(gendata,look_back=3):
  dataX, dataY = [], []
  for seq,clazz in gendata:
    for i in range(len(seq)-look_back-1):
      subseq = seq[i:(i+look_back)]
      dataX.append(subseq)
      dataY.append(clazz)

  return numpy.array(dataX),numpy.array(dataY)

look_back=3
trainX,trainY = create_dataset(DATAGEN.generate_train_dataset(), \
                               look_back=look_back)
testX,testY = create_dataset(DATAGEN.generate_test_dataset(), \
                               look_back=look_back)

trainX = numpy.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

model = Sequential()
model.add(LSTM(4, input_shape=(1, look_back)))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2)

print(model)
testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

trainPredict = model.predict(trainX)
testPredict = model.predict(testX)
# invert predictions
trainPredict = scaler.inverse_transform(trainPredict)
trainY = scaler.inverse_transform([trainY])
testPredict = scaler.inverse_transform(testPredict)
testY = scaler.inverse_transform([testY])
# calculate root mean squared error
trainScore = math.sqrt(mean_squared_error(trainY[0], trainPredict[:,0]))
print('Train Score: %.2f RMSE' % (trainScore))
testScore = math.sqrt(mean_squared_error(testY[0], testPredict[:,0]))
print('Test Score: %.2f RMSE' % (testScore))

# shift train predictions for plotting
trainPredictPlot = numpy.empty_like(dataset)
trainPredictPlot[:, :] = numpy.nan
trainPredictPlot[look_back:len(trainPredict)+look_back, :] = trainPredict
# shift test predictions for plotting
testPredictPlot = numpy.empty_like(dataset)
testPredictPlot[:, :] = numpy.nan
testPredictPlot[len(trainPredict)+(look_back*2)+1:len(dataset)-1, :] = testPredict
# plot baseline and predictions
plt.plot(scaler.inverse_transform(dataset))
plt.plot(trainPredictPlot)
plt.plot(testPredictPlot)
plt.savefig("prediction.png")
