"""
Module implementing the TT-GPstruct, a model for structured prediction based on
GP framework.
"""

import tensorflow as tf
import numpy as np

import t3f
import t3f.kronecker as kron
from t3f import ops, TensorTrain, TensorTrainBatch, batch_ops
from tf.contrib import crf

from gptt_embed.misc import _kron_tril, _kron_logdet, pairwise_quadratic_form

class TTGPstruct:

  def __init__(self, cov, inputs, x_init, y_init, mu_ranks):
    """Creates a `TTGPstruct` object for structured GP prediction.

    Args:
      cov:
      inputs: `InputsGrid` object.
      x_init: features for initialization.
      y_init: target values for initialization.
      mu_ranks: TT-ranks of means of the proceses at inducing inputs mu.
    """
    self.inputs = inputs
    self.inputs_dists = inputs.kron_dists()
    self.n_labels = cov.ndim
    self.cov = cov
    self.sigma_ls = self._get_sigma_ls()
    self.mus = self._get_mus(mu_ranks, x_init, y_init)
    self.N = 0 # Size of the training set
    self.bin_mu, self.bin_sigma_l = self._get_bin_vars()

  def _get_bin_vars(self):
    """Initializes binary potential variational parameters.
    """
    # TODO: check 
    init_mu = tf.zeros([self.n_labels])
    init_sigma_l = tf.eye(self.n_labels) # Should this be diagonal?
    bin_mu = tf.get_variable('bin_mu', initializee=init_mu, dtype=tf.float64)
    bin_sigma_l = tf.get_variable('bin_sigma_l', initializee=init_sigma_l, 
        dtype=tf.float64)
    return bin_mu, bin_sigma_l

  def _get_mus(self, ranks, x_init, y_init):
    """Initialization of mus.
    """
    # TODO: check 
    w = self.inputs.interpolate_on_batch(self.cov.project(x_init))
    Sigma = ops.tt_tt_matmul(self.sigma_ls[0], ops.transpose(self.sigma_ls[0]))
    temp = ops.tt_tt_matmul(w, y_init)        
    anc = ops.tt_tt_matmul(Sigma, temp) 
    res = TensorTrain([core[0, :, :, :, :] for core in anc.tt_cores], 
            tt_ranks=[1]*(anc.ndims()+1))
    res = res
    for i in range(1, anc.get_shape()[0]):
        elem = TensorTrain([core[i, :, :, :, :] for core in anc.tt_cores],
                tt_ranks=[1]*(anc.ndims()+1))
        res = ops.add(res, elem)
    mu_ranks = [1] + [ranks] * (res.ndims() - 1) + [1]
    mu_cores = []
    for core in res.tt_cores:
        mu_cores.append(tf.tile(core[None, ...], [self.n_class, 1, 1, 1, 1]))
    return t3f.get_variable('tt_mus', 
        initializer=TensorTrainBatch(mu_cores, res.get_raw_shape(), mu_ranks))

  def _get_sigma_ls(self):
    """Initialization of sigmas.
    """
    # TODO: check 
    cov = self.cov
    inputs_dists = self.inputs_dists
    K_mm = cov.kron_cov(inputs_dists)    
    return t3f.get_variable('sigma_ls', initializer=kron.cholesky(K_mm))

  def initialize(self, sess):
    """Initializes variational and covariance parameters.

    Args:
        sess: a `Session` instance
    """
    self.cov.initialize(sess)
    sess.run(tf.variables_initializer(self.sigma_ls.tt_cores))
    sess.run(tf.variables_initializer(self.mus.tt_cores))
    sess.run(tf.variables_initializer([self.bin_mu, self.bin_sigma]))

  def get_params(self):
    """Returns a list of all the parameters of the model.
    """
    bin_var_params = list(self.bin_mu_l + self.bin_sigma_l)
    un_var_params = list(self.mus.tt_cores + self.sigma_ls.tt_cores)
    var_params = bin_var_params + un_var_params
    cov_params = self.cov.get_params()
    return cov_params + gp_var_params

  def _K_mms(self, eig_correction=1e-2):
    """Returns covariance matrices computed at inducing inputs for all labels. 
    """
    return self.cov.kron_cov(self.inputs_dists, eig_correction)

  def _sample_f(self, mus, sigmas):
    """Samples a value from all the processes.
    """
    # TODO: implement 
    #eps = tf.random_normal([self.nlabels])
    pass

  def _binary_complexity_penalty(self):
    """Computes the complexity penalty for binary potentials.

    This function computes negative KL-divergence between variational 
    distribution and prior over binary potentials.
    Returns:
      A scalar `tf.Tensor` containing the complexity penalty for the variational
      distribution over binary potentials.
    """
    # TODO: should we use other kernels for binary potentials?
    K_bin = tf.eye(self.n_labels * self.n_labels)
    K_bin_log_det = tf.zeros([1])
    K_bin_inv = tf.eye(self.n_labels * self.n_labels)

    S_bin_l = self.bin_sigma_l
    S_bin = tf.matmul(S_bin_l, tf.transpose(S_bin_l))
    S_bin_logdet = _kron_logdet(S_bin_l)
    mu_bin = self.bin_mu
    
    KL = K_bin_logdet - S_bin_logdet
    KL += tf.einsum('ij,ji->i', K_bin_inv, S_bin)
    KL += tf.matmul(mu_bin, tf.transpose(tf.matmul(K_bin_inv, mu_bin))
    KL = KL / 2
    return -KL

  def _unary_complexity_inducing_inputs(self):
    """Computes the complexity penalty for unary potentials.

    This function computes KL-divergence between prior and variational 
    distribution over the values of GPs at inducing inputs.

    Returns:
      A scalar `tf.Tensor` containing the complexity penalty for GPs 
      determining unary potentials.
    """
    mus = self.mus
    sigma_ls = _kron_tril(self.sigma_ls)
    sigmas = ops.tt_tt_matmul(sigma_ls, ops.transpose(sigma_ls))
    sigmas_logdet = _kron_logdet(sigma_ls)

    K_mms = self._K_mms()
    K_mms_inv = kron.inv(K_mms)
    K_mms_logdet = kron.slog_determinant(K_mms)[1]

    penalty = 0
    penalty += - K_mms_logdet
    penalty += sigmas_logdet
    penalty += - ops.tt_tt_flat_inner(sigmas, K_mms_inv)
    penalty += - ops.tt_tt_flat_inner(mus, 
                           ops.tt_tt_matmul(K_mms_inv, mus))
    return tf.reduce_sum(penalty) / 2
      
  @staticmethod
  def _compute_pairwise_dists(x):
    """Computes pairwise distances in feature space for a batch of sequences.

    Args:
      x: `tf.Tensor` of shape `batch_size` x `max_seq_len` x d; 
      sequences of features for the current batch.

    Returns:
      A `tf.Tensor` of shape `batch_size` x `max_seq_len` x `max_seq_len`; for
      each sequence in the batch it contains a matrix of pairwise distances
      between it's elements in the feature space.
    """
    x_norms = tf.reduce_sum(x**2, axis=2)[:, :, None]
    x_norms = x_norms + tf.transpose(x_norms, [0, 2, 1])
    batch_size, max_len, d = x.get_shape()
    print('_compute_pairwise_dists/x_norms', x_norms.get_shape(), '=', 
      batch_size, max_len, max_len)
    scalar_products = tf.einsum('bid,bjd->bij', x, x)
    print('_compute_pairwise_dists/scalar_products', 
        scalar_products.get_shape(), '=', batch_size, max_len, max_len)
    dists = 2 * x_norms - scalar_products
    return dists

#  def _latent_vars_distribution(self, x, seq_lens):
#    """Computes the parameters of the variational distribution over potentials.
#
#    Args:
#      x: `tf.Tensor` of shape `batch_size` x `max_seq_len` x d; 
#      sequences of features for the current batch.
#      seq_lens: `tf.Tensor` of shape `bach_size`; lenghts of input sequences.
#
#    Returns:
#      A tuple containing 4 `tf.Tensors`.
#      `m_un`: a `tf.Tensor` of shape `batch_size` x `max_seq_len` x `n_labels`;
#        the expectations of the unary potentials.
#      `K_un`: a `tf.Tensor` of shape 
#        `batch_size` x `max_seq_len` x `max_seq_len` x `n_labels`; the
#        covariance matrix of unary potentials.
#      `m_bin`: a `tf.Tensor` of shape `max_seq_len`^2; the expectations
#        of binary potentials.
#      `K_bin`: a `tf.Tensor` of shape `max_seq_len`^2 x `max_seq_len`^2; the
#        covariance matrix of binary potentials.
#    """
#    # TODO: add max_seq_len 
#    d, max_len, batch_size  = x.get_shape()
#    mask = tf.sequence_mask(seq_lens)
#    indices = tf.where(sequence_mask)
#    
#    x_flat = tf.gather_nd(x, indices)
#    print('_latent_vars_distribution/x_flat', x_flat.get_shape(), '=',
#        '?', 'x', d)
#
#    w = self.inputs.interpolate_on_batch(self.cov.project(x_flat))
#    m_un_flat = batch_ops.pairwise_flat_inner(w, self.mu_s)
#    print('_latent_vars_distribution/m_un_flat', m_un_flat.get_shape(), '=',
#        '?', 'x', n_labels)
#    m_un = tf.scatter_nd(indices, m_un_flat)
#
#    K_un = 

#  def _predict_process_values(self, x, with_variance=False, test=False):
#    """Computes the parameters of the distributions of the latent variables.
#
#    Args:
#      x: `tf.Tensor` of shape `batch_size` x `max_seq_len` x D; 
#      sequences of features for the current batch.
#      seq_lens: `tf.Tensor` of shape `bach_size`; lenghts of input sequences.
#    """
#    w = self.inputs.interpolate_on_batch(self.cov.project(x, test=test))
#
#    mean = batch_ops.pairwise_flat_inner(w, self.mus)
#    if not with_variance:
#        return mean
#    K_mms = self._K_mms()
#
#    sigma_ls = _kron_tril(self.sigma_ls)
#    variances = []
#    sigmas = ops.tt_tt_matmul(sigma_ls, ops.transpose(sigma_ls))
#    variances = pairwise_quadratic_form(sigmas, w, w)
#    variances -= pairwise_quadratic_form(K_mms, w, w)
#    variances += self.cov.cov_0()[None, :]
#    return mean, variances

  def elbo(self, x, y, seq_lens, name=None):
    '''Evidence lower bound.
    
    A doubly stochastic procedure based on reparametrization trick is used to 
    approximate the gradients of the ELBO with respect to the variational
    parameters.
    Args:
      x: `tf.Tensor` of shape `batch_size` x `max_seq_len` x D; 
      sequences of features for the current batch.
      y: `tf.Tensor` of shape `batch_size` x `max_seq_len`; target values for 
      the current batch.
      seq_lens: `tf.Tensor` of shape `bach_size`; lenghts of input sequences.

    Returns:
      A scalar `tf.Tensor` containing a stochastic approximation of the evidence
      lower bound.
    '''
    # TODO: implement 
    means, variances = self._predict_process_values(x, with_variance=True)

    l = tf.cast(tf.shape(y)[0], tf.float64) # batch size
    N = tf.cast(self.N, dtype=tf.float64) 

    y = tf.reshape(y, [-1, 1])
    indices = tf.concat([tf.range(tf.cast(l, tf.int64))[:, None], y], axis=1)

    # means for true classes
    means_c = tf.gather_nd(means, indices)
    print('GPC/elbo/means_c', means_c.get_shape())
    
    # Likelihood
    elbo = 0
    elbo += tf.reduce_sum(means_c)

    # Log-partition function expectation estimate
    sample_unary, sample_binary = self.sample_potentials(x)
    log_Z = crf.crf_log_norm(sample_unary, seq_lens, sample_binary)

    log_sum_exp_bound = tf.log(tf.reduce_sum(tf.exp(means + variances/2),
                                                                axis=1))
    print('GPC/elbo/log_sum_exp_bound', log_sum_exp_bound.get_shape())
    elbo -= tf.reduce_sum(log_sum_exp_bound)
    elbo /= l
    
    print('GPC/elbo/complexity_penalty', self._unary_complexity_penalty().get_shape())
    print('GPC/elbo/complexity_penalty', self._complexity_penalty_inducing_inputs().get_shape())
    elbo += self._unary_complexity_penalty() / N #is this right?
    elbo += self._complexity_penalty_inducing_inputs() / N
    return -elbo
  
  def fit(self, x, y, seq_lens, N, lr, global_step):
    """Fit the model.

    Args:
      x: `tf.Tensor` of shape `batch_size` x `max_seq_len` x D; 
      sequences of features for the current batch.
      y: `tf.Tensor` of shape `batch_size` x `max_seq_len`; target values for 
      the current batch.
      seq_lens: `tf.Tensor` of shape `bach_size`; lenghts of input sequences.
      N: number of training instances.
      lr: learning rate for the optimization method.
      global_step: global step tensor.
    """
    # TODO: check 
    self.N = N
    fun = self.elbo(x, y)
    optimizer = tf.train.AdamOptimizer(learning_rate=lr)
    return fun, optimizer.minimize(fun, global_step=global_step)

  def predict(self, x, seq_lens, n_samples, test=False):
    '''Predicts the labels for the given sequences.

    Approximately finds the configuration of the graphical model which has
    the lowest expected energy based on sampling.
    Args:
      x: `tf.Tensor` of shape `batch_size` x `max_seq_len` x D; 
      sequences of features for the current batch.
      y: `tf.Tensor` of shape `batch_size` x `max_seq_len`; target values for 
      the current batch.
      seq_lens: `tf.Tensor` of shape `bach_size`; lenghts of input sequences.
      n_samples: number of samples used to estimate the optimal labels.
    '''
    # TODO: implement 
    pass
