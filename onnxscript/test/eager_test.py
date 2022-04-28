# SPDX-License-Identifier: Apache-2.0

import unittest
import numpy as np
from numpy.testing import assert_almost_equal
import onnx
from onnxscript.test.models import signal_dft
from onnxscript.test.functions.onnx_script_test_case import (
    OnnxScriptTestCase, FunctionTestParams)


class TestOnnxSignal(OnnxScriptTestCase):

    @staticmethod
    def _fft(x, fft_length):
        ft = np.fft.fft(x, fft_length[0])
        r = np.real(ft)
        i = np.imag(ft)
        merged = np.vstack([r[np.newaxis, ...], i[np.newaxis, ...]])
        perm = np.arange(len(merged.shape))
        perm[:-1] = perm[1:]
        perm[-1] = 0
        tr = np.transpose(merged, list(perm))
        if tr.shape[-1] != 2:
            raise AssertionError(f"Unexpected shape {tr.shape}, x.shape={x.shape} "
                                 f"fft_length={fft_length}.")
        return tr

    @staticmethod
    def _cfft(x, fft_length):
        slices = [slice(0, x) for x in x.shape]
        slices[-1] = slice(0, x.shape[-1], 2)
        real = x[slices]
        slices[-1] = slice(1, x.shape[-1], 2)
        imag = x[slices]
        c = np.squeeze(real + 1j * imag, -1)
        return TestOnnxSignal._fft(c, fft_length)

    @staticmethod
    def _complex2float(c):
        real = np.real(c)
        imag = np.imag(c)
        x = np.vstack([real[np.newaxis, ...], imag[np.newaxis, ...]])
        perm = list(range(len(x.shape)))
        perm[:-1] = perm[1:]
        perm[-1] = 0
        return np.transpose(x, perm)

    def test_dft_rfft(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(5).astype(np.float32).reshape((1, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]

        for x in xs:
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                expected = self._fft(x, le)
                with self.subTest(x_shape=x.shape, le=list(le), expected_shape=expected.shape):
                    case = FunctionTestParams(signal_dft.dft, [x, le], [expected])
                    self.run_eager_test(case, rtol=1e-4, atol=1e-4)

    def test_dft_cfft(self):

        xs = [np.arange(5).astype(np.float32),
              np.arange(5).astype(np.float32).reshape((1, -1)),
              np.arange(30).astype(np.float32).reshape((2, 3, -1)),
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1))]
        ys = [np.arange(5).astype(np.float32) / 10,
              np.arange(5).astype(np.float32).reshape((1, -1)) / 10,
              np.arange(30).astype(np.float32).reshape((2, 3, -1)) / 10,
              np.arange(60).astype(np.float32).reshape((2, 3, 2, -1)) / 10]
        cs = [x + 1j * y for x, y in zip(xs, ys)]

        for c in cs:
            x = self._complex2float(c)
            for s in [4, 5, 6]:
                le = np.array([s], dtype=np.int64)
                expected1 = self._fft(c, le)
                expected2 = self._cfft(x, le)
                assert_almost_equal(expected1, expected2)
                with self.subTest(c_shape=c.shape, le=list(le), expected_shape=expected1.shape):
                    case = FunctionTestParams(signal_dft.dft, [x, le, False], [expected1])
                    self.run_eager_test(case, rtol=1e-4, atol=1e-4)


if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    unittest.main()
