import tensorflow as tf
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle
from sklearn.datasets import load_svmlight_file

data_name = 'cpu_small'
path = '/Users/IzmailovPavel/Documents/Education/Programming/DataSets/Regression/cpusmall(8192, 12).txt'
#data_name = 'mg'
#path = '/Users/IzmailovPavel/Documents/Education/Programming/DataSets/Regression/mg(1385, 6).txt'
#data_name = 'abalone'
#path = '/Users/IzmailovPavel/Documents/Education/Programming/DataSets/Regression/abalone(4177, 8).txt'
NUM_FEATURES = 12

def prepare_data():
    """
    Prepares the dataset
    """
    print('Preparing Data')
    x_, y_ = load_svmlight_file(path)
    if not isinstance(x_, np.ndarray):
        x_ = x_.toarray()
    if not isinstance(y_, np.ndarray):
        y_ = y_.toarray()
    x_, y_ = shuffle(x_, y_, random_state=241)
    train_num = int(x_.shape[0] * 0.8)
    x_tr = x_[:train_num, :]
    x_te = x_[train_num:, :]
    y_tr = y_[:train_num]
    y_te = y_[train_num:]
    #x_tr = x_tr[:1000]
    #y_tr = y_tr[:1000]
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    x_tr = scaler_x.fit_transform(x_tr)
    x_te = scaler_x.transform(x_te)
    y_tr = scaler_y.fit_transform(y_tr)
    y_te = scaler_y.transform(y_te)
    return x_tr, y_tr, x_te, y_te

def make_tensor(array, name):
    init = tf.constant(array)
    return tf.Variable(init, name=name, trainable=False)

def get_batch(x_tr, y_tr, batch_size):
    """
    Iterator, returning bathces
    """
    print('\tIn get_batch...')
    x_example, y_example = tf.train.slice_input_producer([x_tr, y_tr])
    capacity = 32#3 * batch_size#min_after_dequeue  + 3 * batch_size
    print('\tMaking the batch')
    x_batch, y_batch = tf.train.batch([x_example, y_example], batch_size=batch_size, capacity=capacity)
    return x_batch, y_batch
