import random
import numpy as np
from rotations import rotation_combo
from box_maker import make_one_box
from box_maker import make_blurred_box

try:
  from keras.utils import to_categorical
except ImportError:
  from tensorflow.keras.utils import to_categorical

# data generators:

# generator for validation data
def test_val_dataGenerator(pre_boxes, center_aa_list, batch_size, BLUR, center_prob, box_size):
  """ data generator for testing and validation in batches data without rotations """
  while True:
    for i in range(0, len(pre_boxes) - batch_size, batch_size):
      box_list = []
      center_list = []
      for j in range(i, i + batch_size): 
        if BLUR == False:
          box = make_one_box(pre_boxes[j], box_size)
        else:
          box = make_blurred_box(pre_boxes[j], center_prob, box_size)
        
        box_list.append(box)
        center_list.append(center_aa_list[j])

      yield np.asarray(box_list), to_categorical(center_list, 20)

# generator for training data
def train_dataGenerator(pre_boxes, center_aa_list, batch_size, rotations, BLUR, center_prob, box_size):
  """ generates data for training in batches with rotations """
  zip_lists = list(zip(pre_boxes, center_aa_list))
  random.shuffle(zip_lists)
  pre_boxes, center_aa_list = list(zip(*zip_lists))

  while True:
    batch_fraction = int(batch_size/rotations)
    for i in range(0, len(pre_boxes) - batch_fraction, batch_fraction):
      box_list = []
      center_list = []
      for j in range(i, i + batch_fraction): 
        rotated_boxes = rotation_combo(pre_boxes[j], rotations, box_size)
        for rotated_box in rotated_boxes:
          if BLUR == False:
            box_list.append(make_one_box(rotated_box, box_size))
          else:
            box_list.append(make_blurred_box(rotated_box, center_prob, box_size))
        for z in range(0, rotations):
          center_list.append(center_aa_list[j])

      yield np.asarray(box_list), to_categorical(center_list, 20)