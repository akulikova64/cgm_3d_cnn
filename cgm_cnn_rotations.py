# course grained cnn on 38 proteins (small practice dataset)

import numpy as np
import os
import sys
import math
import random
from matplotlib import pyplot as plt

try:
  import keras
  from keras.models import Sequential
  from keras.layers import Dense, Dropout, Activation, Flatten
  from keras.layers import Convolution3D
  from keras.optimizers import Adam
  from keras.callbacks import Callback
  from keras.models import load_model
  from keras.utils import multi_gpu_model
  from keras.utils import np_utils

except ImportError:
  import tensorflow
  from tensorflow.keras.models import Sequential
  from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
  from tensorflow.keras.layers import Convolution3D
  from tensorflow.keras.callbacks import Callback
  from tensorflow.keras.optimizers import Adam
  from tensorflow.keras.models import load_model
  from tensorflow.keras.utils import multi_gpu_model
  from tensorflow.keras.utils import np_utils
  from tensorflow.keras.utils import to_categorical
  

'''
# Raghav's class (records loss after each batch (100,000))
class NBatchLogger(Callback):
    def __init__(self, display, samples=10000, batch_size=20, nparts=160):
        super(NBatchLogger, self).__init__()
        self.step = 0
        self.display = display
        self.metric_cache = {}
        self.epoch = 0
        self.iteration = 0
        self.i_per_part = samples/batch_size
        self.nparts = nparts

    def on_epoch_end(self, epoch, logs=None):
        self.epoch += 1

    def on_batch_end(self, batch, logs={}):
        self.step += 1
        for k in self.params['metrics']:
            if k in logs:
                self.metric_cache[k] = self.metric_cache.get(k, 0) + logs[k]
        if self.step % self.display == 0:
            metrics_log = ''
            for (k, v) in self.metric_cache.items():
                val = v / self.display
                if abs(val) > 1e-3:
                    metrics_log += ' - %s: %.4f' % (k, val)
                else:
                    metrics_log += ' - %s: %.4e' % (k, val)
            outline = 'iter: %d, epoch: %d, part: %d, batch: %d, acc: %0.2f, loss: %0.4f, lr: %0.4f' % (self.iteration, self.epoch, (self.iteration / self.i_per_part) % self.nparts, logs['batch'], logs['acc'], logs['loss'], K.eval(self.model.optimizer.lr))
            log_file = open('log.txt','a')
            log_file.write(outline+'\n')
            print(outline)
            self.metric_cache.clear()
            self.iteration += 1

# Raghav's class
class WeightsSaver(Callback):
    def __init__(self, N):
        self.N = N
        self.batch = 1

    def on_batch_end(self, batch, logs={}):
        if self.batch % self.N == 0:
            name = 'weights/weights%08d.h5' % (self.batch)
            self.model.save_weights(name)
        self.batch += 1
'''
# fill a box
def make_one_box(pre_box):
  box = np.zeros([9, 9, 9, 20]) # 4D array filled with 0
  for ind_set in pre_box:
    box[ind_set[0]][ind_set[1]][ind_set[2]][ind_set[3]] += 1
  return box

# axis is the axis across which the rotation occurs
# rot_num is the number of 90 degree rotations needed (1, 2 or 3)
def rotate_box(pre_box, axis, rot_num):
  dict = {"x":[1, 2], "y":[0, 2], "z":[0, 1]} # lists the axes to be changed if rotated around key
  new_pre_box = []

  for ind_set in pre_box:
    a_1, a_2 = dict[axis][0], dict[axis][1]
    
    if rot_num == 1:
      ind_set[a_1] = 8 - ind_set[a_2]
      ind_set[a_2] = ind_set[a_1]
    if rot_num == 2:
      ind_set[a_1] = 8 - ind_set[a_1]
      ind_set[a_2] = 8 - ind_set[a_2]
    if rot_num == 3:
      ind_set[a_1] = ind_set[a_2]
      ind_set[a_2] = 8 - ind_set[a_1]

    new_pre_box.append(ind_set)

  return new_pre_box

def rotation_combo(pre_box):
  final_preboxes = []
  rot_list = random.sample(range(0, 24), 4)

  for i in rot_list:
    # rotate along z
    prebox_1 = rotate_box(pre_box, "z", i%4)

    # rotate along x or y
    rot_num = math.floor(i/4) # 0-5
    if rot_num < 4:
      prebox_2 = rotate_box(prebox_1, "y", rot_num)
    elif rot_num == 4:
      prebox_2 = rotate_box(prebox_1, "x", 1)
    elif rot_num == 5:
      prebox_2 = rotate_box(prebox_1, "x", 3)
    final_preboxes.append(prebox_2)

  return final_preboxes

def get_box_list(path): 
  fileList = os.listdir(path)
  pre_box_list = []
  center_aa_list = []

  for file in fileList:
    if "boxes" in file:
      pdb_id = file[-8:-4]

      pre_boxes = np.load(path + file, allow_pickle = True)
      for pre_box in pre_boxes:
        pre_box_list.append(pre_box)

      centers = np.load(path + "centers_" + pdb_id + ".npy", allow_pickle = True) # list of center aa's in one file
      for center in centers:
        center_aa_list.append(center)
  
  return pre_box_list, center_aa_list

# generator for validation data
def dataGenerator_1(pre_boxes, center_aa_list, batch_size):
  while True:
      for i in range(0, len(pre_boxes) - batch_size, batch_size):
        box_list = []
        center_list = []
        for j in range(i, i + batch_size): 
          box = make_one_box(pre_boxes[j])
          box_list.append(box)
          center_list.append(center_aa_list[j])

        yield np.asarray(box_list), np_utils.to_categorical(center_list, 20)

# generator for training data
def dataGenerator_2(pre_boxes, center_aa_list, batch_size):
  zip_lists = list(zip(pre_boxes, center_aa_list))
  random.shuffle(zip_lists)
  pre_boxes, center_aa_list = list(zip(*zip_lists))

  while True:
      quarter_batch = int(batch_size/4)
      for i in range(0, len(pre_boxes) - quarter_batch, quarter_batch):
        box_list = []
        center_list = []
        for j in range(i, i + quarter_batch): 
          rotated_boxes = rotation_combo(pre_boxes[j])
          for rotated_box in rotated_boxes:
            box_list.append(make_one_box(rotated_box))
          for z in range(0, 4):
            center_list.append(center_aa_list[j])

        yield np.asarray(box_list), np_utils.to_categorical(center_list, 20)

# preparing training data
x_train, y_train = get_box_list(path = "./boxes/")

# preparing validation data
x_val, y_val = get_box_list(path = "./boxes_38/")

# preparing testing data
x_test = np.load("./testing/boxes_test.npy", allow_pickle = True)
y_test = np.load("./testing/centers_test.npy", allow_pickle = True)

y_data_test = np_utils.to_categorical(y_test, 20)
x_data_test = []

for index_set  in x_test:
  box = make_one_box(index_set)
  x_data_test.append(box)
x_data_test = np.asarray(x_data_test)


# cnn model
model = Sequential()
model.add(Convolution3D(32, kernel_size = (3, 3, 3), strides = (1, 1, 1), activation = 'relu', input_shape = (9, 9, 9, 20))) # 32 output nodes, kernel_size is your moving window, activation function, input shape = auto calculated
model.add(Convolution3D(32, (3, 3, 3), activation = 'relu'))
model.add(Convolution3D(32, (3, 3, 3), activation = 'relu'))
model.add(Flatten()) # now our layers have been combined to one
model.add(Dense(500, activation = 'relu')) # 500 nodes in the last hidden layer
model.add(Dense(20, activation = 'softmax')) # output layer has 20 possible classes (amino acids 0 - 19)

model = multi_gpu_model(model, gpus=4)

'''
model.compile(loss ='categorical_crossentropy',
              optimizer = Adam(lr = .001),
              metrics = ['accuracy'],
              callbacks=[WeightsSaver(10000), NBatchLogger(1)])'''

model.compile(loss ='categorical_crossentropy',
              optimizer = Adam(lr = .001),
              metrics = ['accuracy'])

# batch_size must divide by 4
batch_size = 20

history = model.fit_generator(
          generator = dataGenerator_2(x_train, y_train, batch_size),
          # change to x_val and y_val data (not seen before)
          validation_data = dataGenerator_1(x_val, y_val, batch_size),
          validation_steps = 20,
          steps_per_epoch = len(x_train)/batch_size, 
          epochs = 1, 
          verbose = 1,
         )

score = model.evaluate(x_data_test, y_data_test, verbose = 1, steps = int(len(x_data_test)/batch_size))  
#score = model.evaluate_generator(x_test, y_test, verbose = 1, steps = int(len(x_test)/batch_size))
model.save('model.h5')

print('Test loss:', score[0])
print('Test accuracy:', score[1])

#graphing the accuracy and loss for both the training and test data
#summarize history for accuracy 

# change to CSV file
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['training', 'validation'], loc = 'upper left')
plt.savefig("Accuracy_cgm_flips.pdf")
plt.clf()

# summarize history for loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['training', 'validaton'], loc = 'upper left')
plt.savefig("Loss_cgm_flips.pdf")
