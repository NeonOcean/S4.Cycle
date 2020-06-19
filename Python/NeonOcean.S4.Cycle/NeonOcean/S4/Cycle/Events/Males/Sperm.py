from __future__ import annotations

import random
import typing
import uuid

from NeonOcean.S4.Cycle import Guides as CycleGuides, Settings
from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Cycle.Tools import Distribution
from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info

class SpermGeneratingArguments(EventsBase.GenerationArguments):
	SpermCountMinimum = 0  # type: typing.Optional[int]
	SpermCountMaximum = None  # type: typing.Optional[int]

	MotilePercentageMinimum = 0  # type: typing.Optional[int]
	MotilePercentageMaximum = 1  # type: typing.Optional[int]

	ViablePercentageMinimum = 0  # type: typing.Optional[int]
	ViablePercentageMaximum = 1  # type: typing.Optional[int]

	UniqueIdentifierSeed = -842490766  # type: int
	UniqueSeedSeed = 573054244  # type: int

	LifetimeDistributionMeanSeed = 796385459  # type: int
	LifetimeDistributionSDSeed = -616904637  # type: int
	SpermCountSeed = -1564992761  # type: int

	MotilePercentageSeed = 541170293  # type: int
	ViablePercentageSeed = 152650811  # type: int

	def __init__ (self, seed: int, targetedObject: typing.Any, spermGuide: CycleGuides.SpermGuide, *args, **kwargs):
		"""
		Event arguments for times when a new sperm object needs to fill its attributes.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The object the event has been triggered for.
		:type targetedObject: typing.Any
		"""

		if not isinstance(spermGuide, CycleGuides.SpermGuide):
			raise Exceptions.IncorrectTypeException(spermGuide, "spermGuide", (CycleGuides.SpermGuide,))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self._spermGuide = spermGuide

		self.Source = None  # type: typing.Optional[sim_info.SimInfo]

		self.LifetimeDistributionMean = Distribution.TweakableNormalDistribution(spermGuide.LifetimeDistributionMean.Mean, spermGuide.LifetimeDistributionMean.StandardDeviation)
		self.LifetimeDistributionSD = Distribution.TweakableNormalDistribution(spermGuide.LifetimeDistributionSD.Mean, spermGuide.LifetimeDistributionSD.StandardDeviation)
		self.SpermCountDistribution = Distribution.TweakableNormalDistribution(spermGuide.SpermCount.Mean, spermGuide.SpermCount.StandardDeviation)

		self.MotilePercentageDistribution = Distribution.TweakableNormalDistribution(spermGuide.MotilePercentage.Mean, spermGuide.MotilePercentage.StandardDeviation)
		self.ViablePercentageDistribution = Distribution.TweakableNormalDistribution(spermGuide.ViablePercentage.Mean, spermGuide.ViablePercentage.StandardDeviation)

	@property
	def SpermGuide (self) -> CycleGuides.SpermGuide:
		"""
		A guide to help in the creation of the sperm object.
		"""

		return self._spermGuide

	@property
	def Source (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that produced the generating sperm object.
		"""

		return self._source

	@Source.setter
	def Source (self, value: typing.Optional[sim_info.SimInfo]) -> None:
		if not isinstance(value, sim_info.SimInfo) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "Source", (sim_info.SimInfo, None))

		self._source = value

	@property
	def LifetimeDistributionMean (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution to select the mean of every sperm cell's lifetime normal distribution. The distribution's values are measured in
		reproductive minutes.
		"""

		return self._lifetimeDistributionMean

	@LifetimeDistributionMean.setter
	def LifetimeDistributionMean (self, value: Distribution.TweakableNormalDistribution) -> None:
		if not isinstance(value, Distribution.TweakableNormalDistribution):
			raise Exceptions.IncorrectTypeException(value, "LifetimeDistributionMean", (Distribution.TweakableNormalDistribution,))

		self._lifetimeDistributionMean = value

	@property
	def LifetimeDistributionSD (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution to select the standard deviation of every sperm cell's lifetime normal distribution. These values should be in
		reproductive minutes.
		"""

		return self._lifetimeDistributionSD

	@LifetimeDistributionSD.setter
	def LifetimeDistributionSD (self, value: Distribution.TweakableNormalDistribution) -> None:
		if not isinstance(value, Distribution.TweakableNormalDistribution):
			raise Exceptions.IncorrectTypeException(value, "LifetimeDistributionSD", (Distribution.TweakableNormalDistribution,))

		self._lifetimeDistributionSD = value

	@property
	def SpermCountDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A normal distribution used to selected a random sperm count.
		"""

		return self._spermCountDistribution

	@SpermCountDistribution.setter
	def SpermCountDistribution (self, value: Distribution.TweakableNormalDistribution) -> None:
		if not isinstance(value, Distribution.TweakableNormalDistribution):
			raise Exceptions.IncorrectTypeException(value, "SpermCountDistribution", (Distribution.TweakableNormalDistribution,))

		self._spermCountDistribution = value

	@property
	def MotilePercentageDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution to select the percentage of sperm that can make it to an ovum.
		"""

		return self._motilePercentageDistribution

	@MotilePercentageDistribution.setter
	def MotilePercentageDistribution (self, value: Distribution.TweakableNormalDistribution) -> None:
		if not isinstance(value, Distribution.TweakableNormalDistribution):
			raise Exceptions.IncorrectTypeException(value, "MotilePercentageDistribution", (Distribution.TweakableNormalDistribution,))

		self._motilePercentageDistribution = value

	@property
	def ViablePercentageDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution to select the percentage of sperm that can produce a viable fetus.
		"""

		return self._viablePercentageDistribution

	@ViablePercentageDistribution.setter
	def ViablePercentageDistribution (self, value: Distribution.TweakableNormalDistribution) -> None:
		if not isinstance(value, Distribution.TweakableNormalDistribution):
			raise Exceptions.IncorrectTypeException(value, "ViablePercentageDistribution", (Distribution.TweakableNormalDistribution,))

		self._viablePercentageDistribution = value

	def GetUniqueIdentifier (self) -> uuid.UUID:
		seed = self.Seed + self.UniqueIdentifierSeed
		random.seed(seed)

		uuidBytes = random.getrandbits(128)
		return uuid.UUID(int = uuidBytes, version = 4)

	def GetUniqueSeed (self) -> typing.Hashable:
		return self.Seed, self.UniqueSeedSeed

	def GetLifetimeDistribution (self) -> Distribution.NormalDistribution:
		mean = self.LifetimeDistributionMean.GenerateValue(seed = self.Seed + self.LifetimeDistributionMeanSeed, minimum = 0)
		standardDeviation = self.LifetimeDistributionSD.GenerateValue(seed = self.Seed + self.LifetimeDistributionSDSeed, minimum = 0)

		return Distribution.NormalDistribution(mean, standardDeviation)

	def GetSpermCount (self) -> int:
		spermCount = int(self.SpermCountDistribution.GenerateValue(seed = self.Seed + self.SpermCountSeed, minimum = self.SpermCountMinimum, maximum = self.SpermCountMaximum))  # type: int
		return spermCount

	def GetMotilePercentage (self) -> float:
		motilePercentage = self.MotilePercentageDistribution.GenerateValue(seed = self.Seed + self.MotilePercentageSeed, minimum = self.MotilePercentageMinimum, maximum = self.MotilePercentageMaximum)  # type: float
		return motilePercentage

	def GetViablePercentage (self) -> float:
		if Settings.EasyFertilization.Get():
			return self.ViablePercentageMaximum
		else:
			viablePercentage = self.ViablePercentageDistribution.GenerateValue(seed = self.Seed + self.ViablePercentageSeed, minimum = self.ViablePercentageMinimum, maximum = self.ViablePercentageMaximum)  # type: float
			return viablePercentage
