from __future__ import annotations

import enum_lib
import random
import copy
import typing
import uuid

from NeonOcean.S4.Cycle import Guides as CycleGuides, This
from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Cycle.Females.Cycle import Shared as CycleShared, OvumRelease as CycleOvumRelease
from NeonOcean.S4.Cycle.Tools import Distribution, Tweakable, Probability
from NeonOcean.S4.Main.Tools import Exceptions, Python
from NeonOcean.S4.Main import Debug

class CycleStartTestingArguments(EventsBase.SeededArguments):
	class StartTimeTypes(enum_lib.IntFlag):
		"""
		AsSoonAsPossible - Start the cycle on the first possible tick.
		PlannedTime -
		"""

		AsSoonAsPossible = 1  # type: CycleStartTestingArguments.StartTimeTypes
		PlannedTime = 2  # type: CycleStartTestingArguments.StartTimeTypes
		Never = 4  # type: CycleStartTestingArguments.StartTimeTypes

	def __init__ (self, seed: int, timeSinceLastCycle: typing.Optional[float], *args, **kwargs):
		"""
		Event arguments to test when the next cycle should start.
		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param timeSinceLastCycle: The amount of time in reproductive minutes since the last cycle ended. This will be None if no cycle has been
		simulated yet.
		:type timeSinceLastCycle: typing.Optional[float]
		"""

		if not isinstance(timeSinceLastCycle, (float, int)) and timeSinceLastCycle is not None:
			raise Exceptions.IncorrectTypeException(timeSinceLastCycle, "timeSinceLastCycle", (float, int, None))

		super().__init__(seed, *args, **kwargs)

		self._timeSinceTest = 0  # type: float

		self._timeSinceLastCycle = timeSinceLastCycle  # type: typing.Optional[float]

		self._canStart = Tweakable.TweakableBoolean(True)  # type: Tweakable.TweakableBoolean
		self.StartingAt = None

	@property
	def TimeSinceTest (self) -> float:
		"""
		The amount of time in reproductive minutes since this test was run. This should be increased manually with the 'IncreaseTimeSinceTest' until the test
		is discarded.
		"""

		return self._timeSinceTest

	@property
	def TimeSinceLastCycle (self) -> typing.Optional[float]:
		"""
		The amount of time in reproductive minutes since the last cycle ended. This will be None if no cycle has been simulated yet.
		"""

		return self._timeSinceLastCycle

	@property
	def StartingAt (self) -> typing.Optional[float]:
		"""
		The amount of time in reproductive minutes until the next cycle can start. This can be none if the cycle does not have a planned start time,
		meaning it should start when ever.
		"""

		return self._startingAt

	@StartingAt.setter
	def StartingAt (self, value: typing.Optional[float]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "StartingAt", (float, int, None))

		if value is not None:
			if value < 0:
				raise ValueError("'StartingAt' values must be greater than or equal to 0.")

		self._startingAt = value

	@property
	def CanStart (self) -> Tweakable.TweakableBoolean:
		"""
		Whether or not the cycle can start. This should be false if the cycle will not start until something changes, such as the sim growing older.
		"""

		return self._canStart

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

	def PlanStartAt (self, minutesUntilStart: float, increaseTimeOnly: bool = True) -> None:
		"""
		Indicate that the cycle is planned to start this many minutes into the future.
		:param minutesUntilStart: The number of minutes into the future the cycle should start. The number of minutes cannot be less than or equal to 0.
		:type minutesUntilStart: float
		:param increaseTimeOnly: Whether or not we should ignore times that are earlier than previously planned times. If true, this will only ever	push the
		start of the cycle further into the future.
		:type increaseTimeOnly: bool
		"""

		if not isinstance(minutesUntilStart, (float, int)):
			raise Exceptions.IncorrectTypeException(minutesUntilStart, "minutesUntilStart", (float, int))

		if not isinstance(increaseTimeOnly, (bool,)):
			raise Exceptions.IncorrectTypeException(increaseTimeOnly, "increaseTimeOnly", (bool,))

		if minutesUntilStart <= 0:
			raise ValueError("'Minutes until start'cannot be less than or equal to 0.")

		if self.StartingAt > minutesUntilStart and increaseTimeOnly:
			return

		self.StartingAt = minutesUntilStart

	def GetCanStart (self) -> bool:
		"""
		Whether or not the cycle can start. This should return false if the cycle will not start until something changes, such as the sim growing older.
		"""

		return self.CanStart.Value

	def GetTimeUntilStart (self) -> typing.Optional[float]:
		"""
		Get the time in reproductive minutes until the next cycle can start. This can return none if the cycle will not start until something changes,
		such as the sim growing older.
		"""

		if not self.GetCanStart():
			return None

		return self.StartingAt

	def GetCycleTypeIdentifier (self) -> str:
		"""
		Get the identifier of the type of cycle that should be created.
		"""

		return "Menstrual"

	def _OnTimeSinceTestIncreased (self, increasingAmount: float) -> None:
		startingAt = self.StartingAt  # type: typing.Optional[float]

		if startingAt is not None:
			nextStartingAt = max(0.0, startingAt - increasingAmount)
			self.StartingAt = nextStartingAt

class CycleAbortTestingArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, *args, **kwargs):
		"""
		Event arguments to test whether or not a reproductive cycle can exist.
		"""

		super().__init__(*args, **kwargs)

		self._timeSinceTest = 0
		self._abortCycle = Tweakable.TweakableBoolean(False)

	@property
	def TimeSinceTest (self) -> float:
		"""
		The amount of time in reproductive minutes since this test was run. This should be increased manually with the 'IncreaseTimeSinceTest' until the test
		is discarded.
		"""

		return self._timeSinceTest

	@property
	def AbortCycle (self) -> Tweakable.TweakableBoolean:
		"""
		Whether or not any active cycle needs to end before it completes naturally.
		"""

		return self._abortCycle

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

	def _OnTimeSinceTestIncreased (self, increasingAmount: float) -> None:
		pass

class CycleGeneratingArguments(EventsBase.GenerationArguments):
	UniqueIdentifierSeed = 931825589  # type: int
	UniqueSeedSeed = -293225231  # type: int

	OvumReleaseAmountSeed = -637962674  # type: int

	def __init__ (self, seed: int, targetedObject: typing.Any, cycleGuide: CycleGuides.CycleGuide, *args, **kwargs):
		"""
		Event arguments for times when a new cycle object needs to fill its attributes.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each randomization
		operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The cycle being worked on.
		:type targetedObject: typing.Any
		:param cycleGuide: A guide to help in the creation of the cycle.
		:type cycleGuide: GuidesCycles.CycleGuide
		"""

		if not isinstance(cycleGuide, CycleGuides.CycleGuide):
			raise Exceptions.IncorrectTypeException(cycleGuide, "cycleGuide", (CycleGuides.CycleGuide,))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self._cycleGuide = cycleGuide  # type: CycleGuides.CycleGuide

		self._ovumReleaseAmountProbability = copy.copy(self.CycleGuide.OvumReleaseAmount)  # type: Probability.Probability

	@property
	def CycleGuide (self) -> CycleGuides.CycleGuide:
		"""
		A guide to help in the creation of the cycle.
		"""

		return self._cycleGuide

	@property
	def OvumReleaseAmountProbability (self) -> Probability.Probability:
		"""
		The probabilities for the amount of egg cells to be released during the cycle.
		"""

		return self._ovumReleaseAmountProbability

	def GetUniqueIdentifier (self) -> uuid.UUID:
		"""
		Get sperm object's unique identifier.
		"""

		seed = self.Seed + self.UniqueIdentifierSeed
		random.seed(seed)

		uuidBytes = random.getrandbits(128)
		return uuid.UUID(int = uuidBytes, version = 4)

	def GetUniqueSeed (self) -> int:
		"""
		Get sperm object's unique seed.
		"""

		return self.Seed + self.UniqueSeedSeed

	def GetOvumReleaseAmount (self) -> int:
		ovumReleaseAmountString = self.OvumReleaseAmountProbability.ChooseOption(seed = self.Seed + self.OvumReleaseAmountSeed).Identifier  # type: str

		try:
			ovumReleaseAmount = int(ovumReleaseAmountString)  # type: int
		except ValueError:
			Debug.Log("Failed to parse %s to a valid ovum count (an int)." % ovumReleaseAmountString, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			ovumReleaseAmount = 1

		return ovumReleaseAmount

	def GetOvumReleaseTimes (self) -> typing.List[float]:
		raise NotImplementedError()

class CycleMenstrualGeneratingArguments(CycleGeneratingArguments):
	LutealLengthSeed = -575347847  # type: int
	OvulationLengthSeed = -434638495  # type: int
	FollicularLengthSeed = 1856439451  # type: int
	MenstruationLengthSeed = -415580352  # type: int

	OvumReleaseTimesSeed = 327239528  # type: int

	LutealLengthMinimum = 5760  # type: typing.Optional[float]
	LutealLengthMaximum = None  # type: typing.Optional[float]

	OvulationLengthMinimum = 360  # type: typing.Optional[float]
	OvulationLengthMaximum = None  # type: typing.Optional[float]

	FollicularLengthMinimum = 5760  # type: typing.Optional[float]
	FollicularLengthMaximum = None

	MenstruationLengthMinimum = 1440  # type: typing.Optional[float]
	MenstruationLengthMaximum = None  # type: typing.Optional[float]


	def __init__ (self, seed: int, targetedObject: typing.Any, cycleGuide: CycleGuides.CycleMenstrualGuide, *args, **kwargs):
		"""
		Event arguments for times when a new cycle needs to fill its attributes.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each randomization
		operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The cycle being worked on.
		:type targetedObject: typing.Any
		:param cycleGuide: A guide to help in the creation of the cycle.
		:type cycleGuide: GuidesCycles.CycleMenstrualGuide
		"""

		if not isinstance(cycleGuide, CycleGuides.CycleGuide):
			raise Exceptions.IncorrectTypeException(cycleGuide, "cycleGuide", (CycleGuides.CycleMenstrualGuide,))

		super().__init__(seed, targetedObject, cycleGuide, *args, **kwargs)

		self._cycleGuide = cycleGuide  # type: CycleGuides.CycleMenstrualGuide

		self._lutealLengthDistribution = Distribution.TweakableNormalDistribution(self.CycleGuide.LutealLength.Mean, self.CycleGuide.LutealLength.StandardDeviation)  # type: Distribution.TweakableNormalDistribution
		self._ovulationLengthDistribution = Distribution.TweakableNormalDistribution(self.CycleGuide.OvulationLength.Mean, self.CycleGuide.OvulationLength.StandardDeviation)  # type: Distribution.TweakableNormalDistribution
		self._follicularLengthDistribution = Distribution.TweakableNormalDistribution(self.CycleGuide.FollicularLength.Mean, self.CycleGuide.FollicularLength.StandardDeviation)  # type: Distribution.TweakableNormalDistribution
		self._menstruationLengthDistribution = Distribution.TweakableNormalDistribution(self.CycleGuide.MenstruationLength.Mean, self.CycleGuide.MenstruationLength.StandardDeviation)  # type: Distribution.TweakableNormalDistribution

	@property
	def CycleGuide (self) -> CycleGuides.CycleMenstrualGuide:
		"""
		A guide to help in the creation of the cycle.
		"""

		return self._cycleGuide

	@property
	def LutealLengthDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution for the length of the cycle's follicular phase. These values should be in reproductive minutes.
		"""

		return self._lutealLengthDistribution

	@property
	def OvulationLengthDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution for the length of the cycle's follicular phase. These values should be in reproductive minutes.
		"""

		return self._ovulationLengthDistribution

	@property
	def FollicularLengthDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution for the length of the cycle's luteal phase. These values should be in reproductive minutes.
		"""

		return self._follicularLengthDistribution

	@property
	def MenstruationLengthDistribution (self) -> Distribution.TweakableNormalDistribution:
		"""
		A distribution for the length of the cycle's menstrual phase. These values should be in reproductive minutes.
		"""

		return self._menstruationLengthDistribution

	def GetLutealLength (self) -> float:
		phaseLengthArguments = {
			"lengthDistribution": self.LutealLengthDistribution,
			"seed": self.LutealLengthSeed,
			"minimum": self.LutealLengthMinimum,
			"maximum": self.LutealLengthMaximum
		}

		return self._GetPhaseLength(**phaseLengthArguments)

	def GetOvulationLength (self) -> float:
		phaseLengthArguments = {
			"lengthDistribution": self.OvulationLengthDistribution,
			"seed": self.OvulationLengthSeed,
			"minimum": self.OvulationLengthMinimum,
			"maximum": self.OvulationLengthMaximum
		}

		return self._GetPhaseLength(**phaseLengthArguments)

	def GetFollicularLength (self) -> float:
		phaseLengthArguments = {
			"lengthDistribution": self.FollicularLengthDistribution,
			"seed": self.FollicularLengthSeed,
			"minimum": self.FollicularLengthMinimum,
			"maximum": self.FollicularLengthMaximum
		}

		return self._GetPhaseLength(**phaseLengthArguments)

	def GetMenstruationLength (self) -> float:
		phaseLengthArguments = {
			"lengthDistribution": self.MenstruationLengthDistribution,
			"seed": self.MenstruationLengthSeed,
			"minimum": self.MenstruationLengthMinimum,
			"maximum": self.MenstruationLengthMaximum
		}

		return self._GetPhaseLength(**phaseLengthArguments)

	def GetOvumReleaseTimes(self) -> typing.List[float]:
		ovumReleaseTimes = list()  # type: typing.List[float]
		ovumReleaseAmount = self.GetOvumReleaseAmount()  # type: int

		if ovumReleaseAmount <= 0:
			return ovumReleaseTimes

		ovulationStartTime, ovulationEndTime = self._GetOvulationStartAndEndTimes()  # type: float, float
		ovulationLength = ovulationEndTime - ovulationStartTime  # type: float

		assert ovulationLength >= 0

		for ovumReleaseIndex in range(ovumReleaseAmount):  # type: int
			random.seed(self.Seed + self.OvumReleaseTimesSeed + ovumReleaseIndex)
			ovumRelativeReleaseTime = ovulationLength * random.random()  # type: float
			ovumReleaseTime = ovulationStartTime + ovumRelativeReleaseTime  # type: float

			ovumReleaseTimes.append(ovumReleaseTime)

		return ovumReleaseTimes

	def _GetPhaseLength (self, lengthDistribution: Distribution.NormalDistribution, seed: int, minimum: float, maximum: float) -> float:
		return lengthDistribution.GenerateValue(seed = self.Seed + seed, minimum = minimum, maximum = maximum)

	def _GetOvulationStartAndEndTimes (self) -> typing.Tuple[float, float]:
		follicularLength = self.GetFollicularLength()  # type: float
		ovulationLength = self.GetOvulationLength()  # type: float

		startTime = follicularLength - ovulationLength / 2  # type: float
		endTime = follicularLength + ovulationLength / 2  # type: float

		return startTime, endTime

class CycleChangedArguments(EventsBase.ReproductiveArguments):
	"""
	Event arguments for when the current cycle is switched out for another one.
	"""

class CycleCompletedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, completionReason: CycleShared.CompletionReasons, *args, **kwargs):
		"""
		Event arguments for when a cycle has completed.

		:param completionReason: The reason why this cycle has completed.
		:type completionReason: Cycles.CompletionReasons
		"""

		if not isinstance(completionReason, CycleShared.CompletionReasons):
			raise Exceptions.IncorrectTypeException(completionReason, "completionReason", (CycleShared.CompletionReasons,))

		super().__init__(*args, **kwargs)

		self._completionReason = completionReason

	@property
	def CompletionReason (self) -> CycleShared.CompletionReasons:
		"""
		The reason why this cycle has completed.
		"""

		return self._completionReason

class CycleReleaseOvumTestingArguments(EventsBase.TargetedArguments):
	def __init__ (self, targetObject: CycleOvumRelease.OvumRelease, *args, **kwargs):
		"""
		The event arguments for when a cycle is about to release an ovum to determine if we actually should.
		"""

		if not isinstance(targetObject, CycleOvumRelease.OvumRelease):
			raise Exceptions.IncorrectTypeException(targetObject, "targetObject", (CycleOvumRelease.OvumRelease, ))

		super().__init__(targetObject, *args, **kwargs)

		self._releaseTweakable = Tweakable.TweakableBoolean(True)

	@property
	def TargetedObject(self) -> CycleOvumRelease.OvumRelease:
		"""
		The ovum release object that has indicated that the cycle should release an object.
		"""

		return self._targetedObject

	@property
	def Release (self) -> bool:
		"""
		Whether or not this ovum should be released right now. This should be true if the release date was moved or if the ovum shouldn't be released at all.
		This just sets or gets the release tweakable value.
		"""

		return self.ReleaseTweakable.Value

	@Release.setter
	def Release (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Release", (bool, ))

		self.ReleaseTweakable.Value = value

	@property
	def ReleaseTweakable (self) -> Tweakable.TweakableBoolean:
		"""
		Whether or not this ovum should be released right now. This should be true if the release date was moved or if the ovum shouldn't be released at all.
		"""

		return self._releaseTweakable

	@ReleaseTweakable.setter
	def ReleaseTweakable (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "ReleaseTweakable", (bool, ))

		self._releaseTweakable = value

