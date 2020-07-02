from __future__ import annotations

import math
import random
import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Tools import Tweakable
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Exceptions, Python, Savable
from sims4.tuning import tunable

class NormalDistribution(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, mean: float = 0, standardDeviation: float = 0):
		"""
		A type for storing a normal distribution's average and standard deviation in one convenient object.
		:param mean: The mean of this normal distribution.
		:type mean: float
		:param standardDeviation: The standard deviation of this normal distribution.
		:type standardDeviation: float
		"""

		super().__init__()

		self.Mean = mean
		self.StandardDeviation = standardDeviation

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Mean", "Mean", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("StandardDeviation", "StandardDeviation", 1, requiredAttribute = True))

	@property
	def Mean (self) -> float:
		"""
		The mean of this normal distribution.
		"""

		return self._mean

	@Mean.setter
	def Mean (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "Mean", (float, int))

		self._mean = value

	@property
	def StandardDeviation (self) -> float:
		"""
		The standard deviation of this normal distribution.
		"""

		return self._standardDeviation

	@StandardDeviation.setter
	def StandardDeviation (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "StandardDeviation", (float, int))

		self._standardDeviation = value

	def __copy__ (self):
		distributionCopy = self.__class__(mean = self.Mean, standardDeviation = self.StandardDeviation)
		return distributionCopy

	def StandardScore (self, value: float) -> float:
		"""
		Get the number of standard deviations away from the average this value is.
		"""

		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "value", (float, int))

		return (value - self.Mean) / self.StandardDeviation

	def CumulativeDistribution (self, value: float) -> float:
		"""
		Get the probability that any data point of this normal distribution is less than or equal to the input value.
		"""

		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "value", (float, int))

		valueStandardScore = self.StandardScore(value)

		return (1 + math.erf(valueStandardScore / math.sqrt(2.0))) / 2

	def GenerateValue (self, seed: typing.Hashable = None, minimum: typing.Optional[float] = None, maximum: typing.Optional[float] = None) -> float:
		"""
		Generate a random number based on this distribution.
		:param seed: The seed used in the creation of random values. Values generated with the same seed will be identical.
		:type seed: typing.Hashable
		:param minimum: The minimum value that may be randomly generated using this normal distribution.
		:type minimum: typing.Optional[float]
		:param maximum: The maximum value that may be randomly generated using this normal distribution.
		:type maximum: typing.Optional[float]
		"""

		if not isinstance(seed, typing.Hashable):
			raise Exceptions.IncorrectTypeException(seed, "seed", (typing.Hashable, ))

		if not isinstance(minimum, (float, int)) and minimum is not None:
			raise Exceptions.IncorrectTypeException(minimum, "minimum", (float, int, None))

		if not isinstance(maximum, (float, int)) and maximum is not None:
			raise Exceptions.IncorrectTypeException(maximum, "maximum", (float, int, None))

		random.seed(seed)

		generatedValue = random.normalvariate(self.Mean, self.StandardDeviation)

		if (minimum is None or generatedValue >= minimum) and \
				(maximum is None or generatedValue <= maximum):

			return generatedValue

		if minimum is not None and maximum is None:
			distanceOutOfBounds = minimum - generatedValue  # type: float

			if distanceOutOfBounds < 0:
				Debug.Log("Calculated generated value (%s) distance below the minimum (%s) as less than 0." % (generatedValue, maximum), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self, lockThreshold = 1)
				return minimum

			return minimum + distanceOutOfBounds
		elif minimum is None and maximum is not None:
			distanceOutOfBounds = generatedValue - maximum  # type: float

			if distanceOutOfBounds < 0:
				Debug.Log("Calculated generated value (%s) distance above the maximum (%s) as less than 0." % (generatedValue, maximum), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self, lockThreshold = 1)
				return maximum

			return maximum - distanceOutOfBounds
		else:
			if typing.TYPE_CHECKING: # To prevent type problems in pycharm.
				minimum: float
				maximum: float

			boundsDistance = maximum - minimum  # type: float

			if boundsDistance < 0:
				Debug.Log("Distribution generation minimum (%s) is greater than the generation maximum (%s)." % (minimum, maximum), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self, lockThreshold = 1)
				return minimum

			relativeValue = generatedValue % boundsDistance  # type: float

			if generatedValue < minimum:
				return minimum + relativeValue
			else:
				return maximum - relativeValue

class TweakableNormalDistribution(NormalDistribution):
	def __init__ (self, mean: float = 0, standardDeviation: float = 0):
		"""
		A type for storing a normal distribution's average and standard deviation in one convenient object. This version used tweakable real number
		objects to store the mean and standard deviation values.
		:param mean: The mean of this normal distribution.
		:type mean: float | int
		:param standardDeviation: The standard deviation of this normal distribution.
		:type standardDeviation: float | int
		"""

		self._meanTweakable = Tweakable.TweakableRealNumber(mean)
		self._standardDeviationTweakable = Tweakable.TweakableRealNumber(standardDeviation)

		super().__init__(mean, standardDeviation)

		self._savables = list()

		self.RegisterSavableAttribute(Savable.DynamicSavableAttributeHandler(
			"Mean",
			"MeanTweakable",
			lambda: Tweakable.TweakableRealNumber(0),
			lambda: Tweakable.TweakableRealNumber(0),
			requiredAttribute = True
		))

		self.RegisterSavableAttribute(Savable.DynamicSavableAttributeHandler(
			"StandardDeviation",
			"StandardDeviationTweakable",
			lambda: Tweakable.TweakableRealNumber(0),
			lambda: Tweakable.TweakableRealNumber(0),
			requiredAttribute = True
		))

	@property
	def Mean (self) -> float:
		"""
		The mean of this normal distribution.
		"""

		return self.MeanTweakable.Value

	@Mean.setter
	def Mean (self, value: float) -> None:
		self.MeanTweakable.Value = value

	@property
	def MeanTweakable (self) -> Tweakable.TweakableRealNumber:
		return self._meanTweakable

	@property
	def StandardDeviation (self) -> float:
		"""
		The standard deviation of this normal distribution.
		"""

		return self.StandardDeviationTweakable.Value

	@StandardDeviation.setter
	def StandardDeviation (self, value: float) -> None:
		self.StandardDeviationTweakable.Value = value

	@property
	def StandardDeviationTweakable (self) -> Tweakable.TweakableRealNumber:
		return self._standardDeviationTweakable

	def __copy__ (self):
		distributionCopy = self.__class__(mean = self.Mean, standardDeviation = self.StandardDeviation)

		distributionCopy._meanTweakable = self._meanTweakable.__copy__()
		distributionCopy._standardDeviationTweakable = self._standardDeviationTweakable.__copy__()
		return distributionCopy

class TunableNormalDistribution(tunable.TunableSingletonFactory):
	FACTORY_TYPE = NormalDistribution

	def __init__ (
			self,
			description = "A normal distribution.",
			meanDefault: float = 0,
			standardDeviationDefault: float = 1,
			**kwargs):  # TODO add the spacings the ea's tunables use to descriptions?

		super().__init__(
			description = description,
			mean = tunable.Tunable(description = "The mean of the normal distribution.", tunable_type = float, default = meanDefault),
			standardDeviation = tunable.Tunable(description = "The standard deviation of the normal distribution.", tunable_type = float, default = standardDeviationDefault),
			**kwargs)
