
from dmppl.stats import *
import unittest

class Test_truePositiveRate(unittest.TestCase): # {{{

    def setUp(self):
        self.g = 1.0 / 4

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = truePositiveRate(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = truePositiveRate(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_truePositiveRate

class Test_trueNegativeRate(unittest.TestCase): # {{{

    def setUp(self):
        self.g = 2.0 / 3

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = trueNegativeRate(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = trueNegativeRate(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_trueNegativeRate

class Test_positivePredictiveValue(unittest.TestCase): # {{{

    def setUp(self):
        self.g = 1.0 / 3

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = positivePredictiveValue(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = positivePredictiveValue(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_positivePredictiveValue

class Test_negativePredictiveValue(unittest.TestCase): # {{{

    def setUp(self):
        self.g = 4.0 / 7

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = negativePredictiveValue(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = negativePredictiveValue(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_negativePredictiveValue

class Test_accuracy(unittest.TestCase): # {{{

    def setUp(self):
        self.g = 1.0 / 2

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = accuracy(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = accuracy(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_accuracy

class Test_balancedAccuracy(unittest.TestCase): # {{{

    def setUp(self):
        self.g = 11.0 / 24

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = balancedAccuracy(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = balancedAccuracy(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_balancedAccuracy

class Test_matthewsCorrelation(unittest.TestCase): # {{{

    def setUp(self):
        self.g = -0.08908708 # TODO: Show working

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = matthewsCorrelation(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = matthewsCorrelation(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_matthewsCorrelation

class Test_bookmakersInformedness(unittest.TestCase): # {{{

    def setUp(self):
        self.g = -1.0 / 12

    def test_Scalar0(self):
        TP = 0.1
        FP = 0.2
        FN = 0.3
        TN = 0.4
        result = bookmakersInformedness(TP, FP, FN, TN)
        self.assertAlmostEqual(result, self.g)

    def test_MultiDim0(self):
        TP = np.array([[1, 1, 1, 1],
                       [1, 1, 1, 1]])
        FP = np.array([[2, 2, 2, 2],
                       [2, 2, 2, 2]])
        FN = np.array([[3, 3, 3, 3],
                       [3, 3, 3, 3]])
        TN = np.array([[4, 4, 4, 4],
                       [4, 4, 4, 4]])
        result = bookmakersInformedness(TP, FP, FN, TN)
        self.assertTrue(np.allclose(result, np.array([[self.g, self.g, self.g, self.g],
                                                      [self.g, self.g, self.g, self.g]])))

# }}} class Test_bookmakersInformedness
