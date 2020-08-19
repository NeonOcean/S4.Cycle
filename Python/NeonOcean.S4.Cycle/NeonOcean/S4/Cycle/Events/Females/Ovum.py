from __future__ import annotations

import random
import typing
import uuid

from NeonOcean.S4.Cycle import Guides as CycleGuides, Settings
from NeonOcean.S4.Cycle.Females import Ovum
from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Cycle.Tools import Distribution, Tweakable
from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info, sim_info_types

class OvumGeneratingArguments(EventsBase.GenerationArguments):
	UniqueIdentifierSeed = -790178406  # type: int
	UniqueSeedSeed = 767087501  # type: int

	NormalLifetimeSeed = -982766232  # type: int
	ImplantationTimeSeed = 265207036  # type: int
	ViabilitySeed = 377991025  # type: int

	def __init__ (self, seed: int, targetedObject: Ovum.Ovum, ovumGuide: CycleGuides.OvumGuide, *args, **kwargs):
		"""
		Event arguments for times when a new ovum object needs to fill its attributes.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The ovum being worked on.
		:type targetedObject: Ovum.Ovum
		:param ovumGuide: A guide to help in the creation of the ovum.
		:type ovumGuide: GuidesOva.OvumGuide
		"""

		if not isinstance(targetedObject, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(targetedObject, "targetedObject", (Ovum.Ovum,))

		if not isinstance(ovumGuide, CycleGuides.OvumGuide):
			raise Exceptions.IncorrectTypeException(ovumGuide, "ovumGuide", (CycleGuides.OvumGuide,))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self._ovumGuide = ovumGuide  # type: CycleGuides.OvumGuide
		self._normalLifetimeDistribution = Distribution.TweakableNormalDistribution(mean = ovumGuide.NormalLifetime.Mean, standardDeviation = ovumGuide.NormalLifetime.StandardDeviation)
		self._implantationTimeDistribution = Distribution.TweakableNormalDistribution(mean = ovumGuide.ImplantationTime.Mean, standardDeviation = ovumGuide.ImplantationTime.StandardDeviation)
		self._viabilityChance = Tweakable.TweakableRealNumber(ovumGuide.ViabilityChance)

		self.Source = None
		self.FertilizationSeed = 0  # type: int

	@property
	def TargetedObject (self) -> Ovum.Ovum:
		"""
		The ovum being worked on.
		"""

		return self._targetedObject

	@property
	def OvumGuide (self) -> CycleGuides.OvumGuide:
		"""
		A guide to help in the creation of the ovum object.
		"""

		return self._ovumGuide

	@property
	def Source (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that produced the generating ovum object.
		"""

		return self._source

	@Source.setter
	def Source (self, value: typing.Optional[sim_info.SimInfo]) -> None:
		if not isinstance(value, sim_info.SimInfo) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "Source", (sim_info.SimInfo, None))

		self._source = value

	@property
	def FertilizationSeed (self) -> int:
		"""
		A seed used to run fertilization events.
		"""

		return self._fertilizationSeed

	@FertilizationSeed.setter
	def FertilizationSeed (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "FertilizationSeed", (int,))

		self._fertilizationSeed = value

	@property
	def NormalLifetimeDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		The normal distribution used to create a random ovum lifetime. These values should be in reproductive minutes.
		"""

		return self._normalLifetimeDistribution

	@property
	def ImplantationTimeDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		The distribution used to create a random ovum implantation time. The ovum's lifetime should be extended to the generated value if fertilized.
		These values should be in reproductive minutes.
		"""

		return self._implantationTimeDistribution

	@property
	def ViabilityChance (self) -> Tweakable.TweakableRealNumber:
		"""
		The chance that a particular ovum can ever cause a pregnancy.
		"""

		return self._viabilityChance

	def GetUniqueIdentifier (self) -> uuid.UUID:
		"""
		Get sperm object's unique identifier.
		"""

		seed = self.Seed + self.UniqueIdentifierSeed
		random.seed(seed)

		uuidBytes = random.getrandbits(128)
		return uuid.UUID(int = uuidBytes, version = 4)

	def GetUniqueSeed (self) -> int:
		return self.Seed + self.UniqueSeedSeed

	def GetSource (self) -> typing.Optional[sim_info.SimInfo]:
		return self.Source

	def GetFertilizationSeed (self) -> int:
		return self.FertilizationSeed

	def GetNormalLifetime (self) -> float:
		return self.NormalLifetimeDistribution.GenerateValue(seed = self.Seed + self.NormalLifetimeSeed, minimum = 0)

	def GetImplantationTime (self) -> float:
		return self.ImplantationTimeDistribution.GenerateValue(seed = self.Seed + self.ImplantationTimeSeed, minimum = 0)

	def GetViability (self) -> bool:
		if Settings.EasyFertilization.Get():
			return True
		else:
			viabilityChance = self.ViabilityChance.Value  # type: float
			random.seed(self.Seed + self.ViabilitySeed)
			viabilityRoll = random.random()
			return viabilityRoll <= viabilityChance

class OvumReleasedArguments(EventsBase.TargetedArguments):
	def __init__ (self, targetedObject: Ovum.Ovum, *args, **kwargs):
		"""
		Event arguments to be used when an egg cell has been released from the ovaries.

		:param targetedObject: The ovum that is being released.
		:type targetedObject: Ovum.Ovum
		"""

		if not isinstance(targetedObject, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(targetedObject, "targetedObject", (Ovum.Ovum,))

		super().__init__(targetedObject, *args, **kwargs)

	@property
	def TargetedObject (self) -> Ovum.Ovum:
		"""
		The ovum that is being released.
		"""

		return self._targetedObject

class OvumFertilizationTestingArguments(EventsBase.SeededAndTargetedArguments):
	def __init__ (self, seed: int, targetedObject: Ovum.Ovum, *args, **kwargs):
		"""
		Event arguments to determine if an ovum should be fertilized.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The ovum this test is being run for.
		:type targetedObject: Ovum.Ovum
		"""

		if not isinstance(targetedObject, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(targetedObject, "targetedObject", (Ovum.Ovum, ))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self._timeSinceTest = 0  # type: float

		self._shouldFertilizeTweakable = Tweakable.TweakableBoolean(False)  # type: Tweakable.TweakableBoolean

	@property
	def TargetedObject (self) -> Ovum.Ovum:
		"""
		The ovum this test is being run for.
		"""

		return self._targetedObject

	@property
	def TimeSinceTest (self) -> float:
		"""
		The amount of time in reproductive minutes since this test was run. This should be increased manually with the 'IncreaseTimeSinceTest' until the test
		is discarded.
		"""

		return self._timeSinceTest

	@property
	def Fertilizing (self) -> Tweakable.TweakableBoolean:
		"""
		Whether of not the ovum is being fertilized.
		"""

		return self._shouldFertilizeTweakable

	def IncreaseTimeSinceTest (self, increasingAmount: float) -> None:
		"""
		Increase the amount of time in reproductive minutes since this test was run. Increasing the time will cause other values to adjust accordingly.
		"""

		if not isinstance(increasingAmount, (float, int)):
			raise Exceptions.IncorrectTypeException(increasingAmount, "increasingAmount", (float, int))

		if increasingAmount < 0:
			raise ValueError("The parameter 'increasingAmount' cannot be less than 0.")

		if increasingAmount == 0:
			return

		self._timeSinceTest += increasingAmount
		self._OnTimeSinceTestIncreased(increasingAmount)

	def ShouldFertilize (self) -> bool:
		"""
		Whether or not the ovum this event is being run for should be fertilized.
		"""

		return self.Fertilizing.Value

	def _OnTimeSinceTestIncreased (self, increasingAmount: float) -> None:
		pass

class OvumFertilizingArguments(EventsBase.SeededAndTargetedArguments):
	def __init__ (self, seed: int, targetedObject: Ovum.Ovum, *args, **kwargs):
		"""
		Event arguments to determine fertilization values, such as the source and viability.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The ovum this test is being run for.
		:type targetedObject: Ovum.Ovum
		"""

		if not isinstance(targetedObject, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(targetedObject, "targetedObject", (Ovum.Ovum, ))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self.FertilizerChosen = False
		self.Fertilizer = None
		self.FertilizingObject = None

		self._fertilizationViability = Tweakable.TweakableBoolean(True)

	@property
	def TargetedObject (self) -> Ovum.Ovum:
		"""
		The ovum this test is being run for.
		"""

		return self._targetedObject

	@property
	def OvumSourceSpecies (self) -> sim_info_types.Species:
		ovumSource = self.TargetedObject.Source
		return ovumSource.species

	@property
	def FertilizerSpecies (self) -> sim_info_types.Species:
		fertilizer = self.Fertilizer
		return fertilizer.species

	@property
	def FertilizerChosen (self) -> bool:
		"""
		Whether or not the fertilizer of this ovum has already been chosen.
		"""

		return self._fertilizerChosen

	@FertilizerChosen.setter
	def FertilizerChosen (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "FertilizerChosen", (bool,))

		self._fertilizerChosen = value

	@property
	def Fertilizer (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that is fertilizing the ovum.
		"""

		return self._fertilizer

	@Fertilizer.setter
	def Fertilizer (self, value: typing.Optional[sim_info.SimInfo]) -> None:
		if not isinstance(value, sim_info.SimInfo) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "Fertilizer", (sim_info.SimInfo, None))

		self._fertilizer = value

	@property
	def FertilizingObject (self) -> typing.Any:
		"""
		The object that is causing the ovum to be fertilized.
		"""

		return self._fertilizingObject

	@FertilizingObject.setter
	def FertilizingObject (self, value: typing.Any) -> None:
		self._fertilizingObject = value

	@property
	def FertilizationViability (self) -> Tweakable.TweakableBoolean:
		"""
		Whether or not the ovum will become un-viable as a result of this fertilization. This shouldn't allow the ovum to become viable if it isn't
		already.
		"""

		return self._fertilizationViability

	def SpeciesIncompatible (self) -> bool:
		"""
		Get whether or not the fertilizer and the and ovum creator are of compatible species.
		"""

		return self.OvumSourceSpecies != self.FertilizerSpecies

	def GetFertilizer (self) -> typing.Optional[sim_info.SimInfo]:
		return self.Fertilizer

	def GetFertilizationViability (self) -> bool:
		if self.SpeciesIncompatible():
			return False

		return self.FertilizationViability.Value

class OvumFertilizedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, fertilizingArguments: OvumFertilizingArguments):
		"""
		Event arguments to handle special post ovum fertilization work.

		:param fertilizingArguments: The event arguments used in calling the fertilizing event for the ovum.
		type fertilizingArguments: OvumFertilizingArguments
		"""

		if not isinstance(fertilizingArguments, OvumFertilizingArguments):
			raise Exceptions.IncorrectTypeException(fertilizingArguments, "fertilizingArguments", (OvumFertilizingArguments,))

		self._fertilizingArguments = fertilizingArguments

	@property
	def FertilizingArguments (self) -> OvumFertilizingArguments:
		return self._fertilizingArguments

class OvumImplantationTestingArguments(EventsBase.SeededAndTargetedArguments):
	def __init__ (self, seed: int, targetedObject: Ovum.Ovum, *args, **kwargs):
		"""
		Event arguments to determine if an ovum can implant and begin a pregnancy.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The ovum this test is being run for.
		:type targetedObject: Ovum.Ovum
		"""

		if not isinstance(targetedObject, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(targetedObject, "targetedObject", (Ovum.Ovum, ))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self._implantationPossible = Tweakable.TweakableBoolean(True)

	@property
	def TargetedObject (self) -> Ovum.Ovum:
		"""
		The ovum this test is being run for.
		"""

		return self._targetedObject

	@property
	def ImplantationPossible (self) -> Tweakable.TweakableBoolean:
		"""
		Whether or not implantation is possible.
		"""

		return self._implantationPossible

	def CanImplant (self) -> typing.Optional[bool]:
		"""
		Get whether or not the ovum is allowed to implant.
		"""

		return self.ImplantationPossible.Value
