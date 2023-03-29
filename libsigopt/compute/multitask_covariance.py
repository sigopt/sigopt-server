# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.compute.covariance_base import DifferentiableCovariance


"""
This covariance kernel contains the tensor product of two covariance kernels.
  K((x,t), (z,s)) = K_x(x, z) K_t(t, s)

There are two ways to organize this -- either manage the passing of the 1D task information
separately or compress the data into a d+1 dimensional format on the outside and peel it apart
in here.  Here we assume that the data is joined into a single object to match the calling
sequence elsewhere ... other strategies could become available if we decide to invest in
untunables long term.

Also two ways to create this object.  It's possible for us to also pass around the covariance
objects rather than the classes.  Might be better, might be worse.

TODO(RTL-60): Eventually, I will need to consider a more complicated hyperparameter passing structure.
"""


class MultitaskTensorCovariance(DifferentiableCovariance):
  covariance_type = "multitask_tensor"

  def __init__(self, hyperparameters, physical_covariance_class, task_covariance_class):
    """
        The hyperparameters in this function are organized in the following way:
            [process_variance, length_scale_1, ..., length_scale_d, length_scale_task]
        TODO(RTL-61): Consider the implications of treating tasks as categorical rather than continuous.

        """
    assert issubclass(physical_covariance_class, DifferentiableCovariance)
    assert issubclass(task_covariance_class, DifferentiableCovariance)
    self.physical_covariance_class = physical_covariance_class
    self.task_covariance_class = task_covariance_class

    self.physical_covariance = None
    self.task_covariance = None
    self.set_hyperparameters(hyperparameters)

  def __repr__(self):
    return (
      f"Multitask[{self.process_variance}]\n"
      f"\t[{self.physical_covariance.covariance_type}({self.physical_covariance.hyperparameters[1:]})]\n"
      f"\t[{self.task_covariance.covariance_type}({self.task_covariance.hyperparameters[1:]})]"
    )

  def separate_physical_task_components(self, points_sampled, points_to_sample=None):
    x_phys = points_sampled[:, :-1]
    x_task = points_sampled[:, -1:]
    z_phys = None if points_to_sample is None else points_to_sample[:, :-1]
    z_task = None if points_to_sample is None else points_to_sample[:, -1:]
    return x_phys, x_task, z_phys, z_task

  @property
  def num_hyperparameters(self):
    return len(self.hyperparameters)

  @property
  def dim(self):  # This is the physical dimension, which I think is probably the appropriate interpretation
    return len(self.hyperparameters) - 1

  @property
  def translation_invariant(self):
    return self.physical_covariance.translation_invariant and self.task_covariance.translation_invariant

  def get_hyperparameters(self):
    physical_hyperparameters = self.physical_covariance.hyperparameters
    hyperparameters = numpy.empty(len(physical_hyperparameters) + 1)
    hyperparameters[0] = self.process_variance
    hyperparameters[1:-1] = physical_hyperparameters[1:]
    hyperparameters[-1] = self.task_covariance.hyperparameters[-1]
    return hyperparameters

  def set_hyperparameters(self, hyperparameters):
    """We choose to deal with the process_variance as part of the full kernel, not the component kernels."""
    hyperparameters = numpy.copy(hyperparameters)
    assert len(hyperparameters.shape) == 1 and len(hyperparameters) >= 3

    self.process_variance = hyperparameters[0]

    physical_hyperparameters = hyperparameters[:-1]
    physical_hyperparameters[0] = 1.0
    self.physical_covariance = self.physical_covariance_class(physical_hyperparameters)

    task_hyperparameters = numpy.array([1.0, hyperparameters[-1]])
    self.task_covariance = self.task_covariance_class(task_hyperparameters)

  hyperparameters = property(get_hyperparameters, set_hyperparameters)

  # pylint: disable=protected-access
  def _covariance(self, x, z):
    x_phys, x_task, z_phys, z_task = self.separate_physical_task_components(x, z)
    physical_component = self.physical_covariance._covariance(x_phys, z_phys)
    task_component = self.task_covariance._covariance(x_task, z_task)
    return physical_component * task_component

  def _build_kernel_matrix(self, points_sampled, points_to_sample=None):
    x_phys, x_task, z_phys, z_task = self.separate_physical_task_components(points_sampled, points_to_sample)
    physical_component = self.physical_covariance._build_kernel_matrix(x_phys, z_phys)
    task_component = self.task_covariance._build_kernel_matrix(x_task, z_task)
    return physical_component * task_component

  def _grad_covariance(self, x, z):
    x_phys, x_task, z_phys, z_task = self.separate_physical_task_components(x, z)
    physical_covariance_vector = self.physical_covariance._covariance(x_phys, z_phys)
    task_covariance_vector = self.task_covariance._covariance(x_task, z_task)
    physical_covariance_grad_tensor = self.physical_covariance._grad_covariance(x_phys, z_phys)
    task_covariance_grad_tensor = self.task_covariance._grad_covariance(x_task, z_task)

    grad_covariance_tensor = numpy.empty((len(x), self.dim))
    grad_covariance_tensor[:, :-1] = physical_covariance_grad_tensor * task_covariance_vector[:, None]
    grad_covariance_tensor[:, -1:] = task_covariance_grad_tensor * physical_covariance_vector[:, None]
    return grad_covariance_tensor

  def _hyperparameter_grad_covariance_without_process_variance(self, x, z):
    x_phys, x_task, z_phys, z_task = self.separate_physical_task_components(x, z)
    physical_covariance_vector = self.physical_covariance._covariance(x_phys, z_phys)
    task_covariance_vector = self.task_covariance._covariance(x_task, z_task)
    phys_hgc = self.physical_covariance._hyperparameter_grad_covariance_without_process_variance(x_phys, z_phys)
    task_hgc = self.task_covariance._hyperparameter_grad_covariance_without_process_variance(x_task, z_task)

    hparam_grad_covariance_tensor = numpy.empty((len(x), self.num_hyperparameters - 1))
    hparam_grad_covariance_tensor[:, :-1] = phys_hgc * task_covariance_vector[:, None]
    hparam_grad_covariance_tensor[:, -1:] = task_hgc * physical_covariance_vector[:, None]
    return hparam_grad_covariance_tensor

  def _build_kernel_grad_tensor(self, points_sampled, points_to_sample=None):
    x_phys, x_task, z_phys, z_task = self.separate_physical_task_components(points_sampled, points_to_sample)
    phys_matrix = self.physical_covariance._build_kernel_matrix(x_phys, z_phys)
    task_matrix = self.task_covariance._build_kernel_matrix(x_task, z_task)
    phys_kgt = self.physical_covariance._build_kernel_grad_tensor(x_phys, z_phys)
    task_kgt = self.task_covariance._build_kernel_grad_tensor(x_task, z_task)

    n_cols = len(points_sampled)
    n_rows = n_cols if points_to_sample is None else len(points_to_sample)
    kg_tensor = numpy.empty((n_rows, n_cols, self.dim))
    kg_tensor[:, :, :-1] = phys_kgt * task_matrix[:, :, None]
    kg_tensor[:, :, -1:] = task_kgt * phys_matrix[:, :, None]
    return kg_tensor

  def _build_kernel_hparam_grad_tensor_without_process_variance(self, points_sampled, points_to_sample=None):
    x_phys, x_task, z_phys, z_task = self.separate_physical_task_components(points_sampled, points_to_sample)
    phys_matrix = self.physical_covariance._build_kernel_matrix(x_phys, z_phys)
    task_matrix = self.task_covariance._build_kernel_matrix(x_task, z_task)
    phys_kgt = self.physical_covariance._build_kernel_hparam_grad_tensor_without_process_variance(x_phys, z_phys)
    task_kgt = self.task_covariance._build_kernel_hparam_grad_tensor_without_process_variance(x_task, z_task)

    n_cols = len(points_sampled)
    n_rows = n_cols if points_to_sample is None else len(points_to_sample)
    kg_tensor = numpy.empty((n_rows, n_cols, self.num_hyperparameters - 1))
    kg_tensor[:, :, :-1] = phys_kgt * task_matrix[:, :, None]
    kg_tensor[:, :, -1:] = task_kgt * phys_matrix[:, :, None]
    return kg_tensor
  # pylint: disable=protected-access
