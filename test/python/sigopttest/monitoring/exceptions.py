# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import mock
import pytest

from zigopt.exception.logger import FullTraceback, _SoftExceptionHandler


class TestProcessSoftException:
  @pytest.fixture
  def services(self):
    return mock.Mock()

  def test_success(self, services):
    def f():
      with _SoftExceptionHandler(RuntimeError, services, {}):
        return True
      assert False, "Should not be reached"

    assert f() is True
    services.exception_logger.process_soft_exception.assert_not_called()

  def test_throw_exception(self, services):
    def f():
      with _SoftExceptionHandler(RuntimeError, services, {}):
        raise RuntimeError()
      return False

    assert f() is False
    services.exception_logger.process_soft_exception.assert_called_once()
    # Ensure we are getting the full traceback, and not just a weak one-line traceback
    ((_, _, tb),), _ = services.exception_logger.process_soft_exception.call_args_list[0]
    assert isinstance(tb, FullTraceback)
    assert tb.tb_next
    assert tb.tb_next.tb_next
    assert tb.tb_next.tb_next.tb_next

  def test_throw_wrong_type(self, services):
    def f():
      with _SoftExceptionHandler(RuntimeError, services, {}):
        raise IOError()
      assert False, "Should not be reached"

    with pytest.raises(IOError):
      f()
    services.exception_logger.process_soft_exception.assert_not_called()
