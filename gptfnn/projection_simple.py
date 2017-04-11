import tensorflow as tf
import numpy as np
import os

from gp import GP
from covariance import SE
from projectors import LinearProjector
from gp_runner import GPRunner

# TODO: this line doesn't work
#os.system('export CUDA_VISIBLE_DEVICES=""')

data_basedir1 = "/Users/IzmailovPavel/Documents/Education/Programming/DataSets/"
data_basedir2 = "/Users/IzmailovPavel/Documents/Education/Projects/GPtf/data/"

with tf.Graph().as_default():
    data_dir = data_basedir2 + "projection_simple(300,3[2])/"
    n_inputs = 10
    mu_ranks = 5
    D, d = 3, 2
    projector = LinearProjector(d=d, D=D)
    cov = SE(0.7, 0.2, 0.1, projector)
    lr = 0.01
    n_epoch = 15
    batch_size = 50
    data_type = 'numpy'
    log_dir = 'log'
    save_dir = 'models/proj_simple.ckpt'
    model_dir = None
    load_model = None
    
    
    runner=GPRunner(data_dir, n_inputs, mu_ranks, cov,
                lr=lr, n_epoch=n_epoch, batch_size=batch_size,
                data_type=data_type, log_dir=log_dir, save_dir=save_dir,
                model_dir=model_dir, load_model=load_model)
    runner.run_experiment()
