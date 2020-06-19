from __future__ import annotations

import enum_lib
import typing

from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Buffs import Shared as BuffsShared
from NeonOcean.S4.Cycle.Effects import Shared as EffectsShared
from NeonOcean.S4.Cycle.Females.Cycle import Menstrual as CycleMenstrual, Shared as CycleShared
from NeonOcean.S4.Cycle.Universal import Shared as UniversalShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Exceptions, Python, Tunable as ToolsTunable
from buffs import buff
from sims import sim_info
from sims4.tuning import tunable

_menstrualBuffs = list()  # type: typing.List[typing.Type[MenstrualBuff]]

class CyclePhaseTest(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
	class PhaseState(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
		class MatchTypes(enum_lib.IntEnum):
			Whitelist = 1  # type: CyclePhaseTest.PhaseState.MatchTypes
			Blacklist = 2  # type: CyclePhaseTest.PhaseState.MatchTypes

		FACTORY_TUNABLES = {
			"Phase": ToolsTunable.TunablePythonEnumEntry(description = "The targeted phase of a menstrual cycle.", enumType = CycleShared.MenstrualCyclePhases, default = CycleShared.MenstrualCyclePhases.Menstruation),
			"MatchType": ToolsTunable.TunablePythonEnumEntry(description = "Whether the specified phase is whitelisted or blacklisted. If there are no whitelisted states we will assume that all states are valid unless told otherwise by blacklisted states.", enumType = MatchTypes, default = MatchTypes.Whitelist),
			"StartCompletion": tunable.OptionalTunable(tunable = tunable.TunableRange(description = "The completion percentage for the targeted phase at which this test will start matching.", tunable_type = float, default = 0, minimum = 0, maximum = 1)),
			"EndCompletion": tunable.OptionalTunable(tunable = tunable.TunableRange(description = "The completion percentage for the targeted phase at which this test will stop matching.", tunable_type = float, default = 0, minimum = 0, maximum = 1))
		}

		Phase: CycleShared.MenstrualCyclePhases
		MatchType: MatchTypes
		StartCompletion: typing.Optional[float]
		EndCompletion: typing.Optional[float]

	FACTORY_TUNABLES = {
		"PhaseStates": tunable.TunableList(tunable = PhaseState.TunableFactory(description = "A list of phase states that the menstrual cycle must either match or not match. Letting this be empty indicates that the menstrual cycle will always be valid."))
	}

	PhaseStates: typing.Tuple[PhaseState, ...]

	def InValidPhase (self, testingCycle: CycleMenstrual.MenstrualCycle) -> bool:
		"""
		Get whether or not this cycle is in a valid phase for this test.
		"""

		if not isinstance(testingCycle, CycleMenstrual.MenstrualCycle):
			raise Exceptions.IncorrectTypeException(testingCycle, "testingCycle", (CycleMenstrual.MenstrualCycle, ))

		if len(self.PhaseStates) == 0:
			return True

		validState = True  # type: bool

		hasWhitelistedPhase = False  # type: bool
		inWhitelistedPhase = False  # type: bool

		for phaseState in self.PhaseStates:  # type: CyclePhaseTest.PhaseState
			if phaseState.MatchType == CyclePhaseTest.PhaseState.MatchTypes.Whitelist:
				hasWhitelistedPhase = True

			if not testingCycle.GetPhaseIsActive(phaseState.Phase):
				continue

			phaseCompletion = testingCycle.GetPhaseCompletionPercentage(phaseState.Phase)  # type: typing.Optional[float]

			if phaseCompletion is None:
				continue

			if phaseState.StartCompletion is not None and phaseState.StartCompletion > phaseCompletion:
				continue

			if phaseState.EndCompletion is not None and phaseState.EndCompletion < phaseCompletion:
				continue

			if phaseState.MatchType == CyclePhaseTest.PhaseState.MatchTypes.Whitelist:
				inWhitelistedPhase = True
				continue
			elif phaseState.MatchType == CyclePhaseTest.PhaseState.MatchTypes.Blacklist:
				validState = False
				break

		if hasWhitelistedPhase and not inWhitelistedPhase:
			validState = False

		return validState

	def TicksUntilValidPhase (self, testingCycle: CycleMenstrual.MenstrualCycle, reproductiveTimeMultiplier: float) -> typing.Optional[int]:
		"""
		Get the number of game ticks until the input cycle reaches a valid phase. This will return none if the cycle will never enter a valid phase.
		:param testingCycle: The menstrual cycle to find valid phases for.
		:type testingCycle: CycleMenstrual.MenstrualCycle
		:param reproductiveTimeMultiplier: The reproductive time multiplier used to simulate the testing cycle
		:type reproductiveTimeMultiplier: float
		"""

		if not isinstance(testingCycle, CycleMenstrual.MenstrualCycle):
			raise Exceptions.IncorrectTypeException(testingCycle, "testingCycle", (CycleMenstrual.MenstrualCycle,))

		if len(self.PhaseStates) == 0:
			return 0

		hasWhitelistedPhase = False  # type: bool

		whitelistedTimes = list()  # type: typing.List[typing.Tuple[float, float]]
		blacklistedTimes = list()  # type: typing.List[typing.Tuple[float, float]]

		for phaseState in self.PhaseStates:
			if phaseState.MatchType == CyclePhaseTest.PhaseState.MatchTypes.Whitelist:
				hasWhitelistedPhase = True

			if testingCycle.GetPhaseCompleted(phaseState.Phase):
				continue

			timeUntilPhaseStart = testingCycle.GetTimeUntilPhaseStarts(phaseState.Phase)  # type: float
			timeUntilPhaseEnd = testingCycle.GetTimeUntilPhaseEnds(phaseState.Phase)  # type: float

			if timeUntilPhaseEnd < 0:
				Debug.Log("A menstrual cycle indicated a phase was not complete, but its end time was %s minutes ago. Phase: %s" % (str(timeUntilPhaseEnd), str(phaseState.Phase)), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
				continue

			phaseLength = timeUntilPhaseEnd - timeUntilPhaseStart  # type: float

			if phaseLength <= 0:
				Debug.Log("Calculated a menstrual cycle phase length as less than or equal to 0. Phase: %s" % str(phaseState.Phase), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
				continue

			if phaseState.StartCompletion is None:
				listedStartTime = timeUntilPhaseStart
			else:
				listedStartTime = timeUntilPhaseStart + phaseLength * phaseState.StartCompletion

			if phaseState.EndCompletion is None:
				listedEndTime = timeUntilPhaseEnd
			else:
				listedEndTime = timeUntilPhaseStart + phaseLength * phaseState.EndCompletion

			if phaseState.MatchType == CyclePhaseTest.PhaseState.MatchTypes.Whitelist:
				whitelistedTimes.append((listedStartTime, listedEndTime))
			elif phaseState.MatchType == CyclePhaseTest.PhaseState.MatchTypes.Blacklist:
				blacklistedTimes.append((listedStartTime, listedEndTime))

		soonestValidTime = None  # type: typing.Optional[float]

		def setTimeIfSooner (testingValidTime: float) -> None:
			nonlocal soonestValidTime

			if soonestValidTime is None:
				soonestValidTime = testingValidTime

			if soonestValidTime < testingValidTime:
				soonestValidTime = testingValidTime

		if hasWhitelistedPhase:
			for whitelistedStartTime, whitelistedEndTime in whitelistedTimes:  # type: float, float
				if soonestValidTime is not None and whitelistedStartTime >= soonestValidTime:
					continue

				validTime = whitelistedStartTime  # type: float

				intervalBlacklisted = False  # type: bool
				for blackListedStartTime, blackListedEndTime in blacklistedTimes:  # type: float, float
					if blackListedStartTime <= validTime and blackListedEndTime >= whitelistedEndTime:
						intervalBlacklisted = True
						break

					if blackListedStartTime <= validTime:
						validTime = blackListedEndTime

				if not intervalBlacklisted:
					setTimeIfSooner(max(validTime, 0.0))

				if soonestValidTime == 0:
					break
		else:
			for blackListedStartTime, blackListedEndTime in blacklistedTimes:  # type: float, float
				if soonestValidTime is not None and blackListedEndTime >= soonestValidTime:
					continue

				blacklistContinues = False  # type: bool
				for otherBlackListedStartTime, otherBlackListedEndTime in blacklistedTimes:  # type: float, float
					if otherBlackListedStartTime <= blackListedEndTime < otherBlackListedEndTime:
						blacklistContinues = True
						pass

				if not blacklistContinues:
					setTimeIfSooner(max(blackListedEndTime, 0.0))

				if soonestValidTime == 0:
					break

		if soonestValidTime is None:
			return None
		else:
			return ReproductionShared.ReproductiveMinutesToTicks(soonestValidTime, reproductiveTimeMultiplier)

class MenstrualBuff(buff.Buff):
	INSTANCE_TUNABLES = {
		# TODO allow persistent buffs.
		"Rarity": ToolsTunable.TunablePythonEnumEntry(description = "How rare this buff is.", enumType = BuffsShared.BuffRarity, default = BuffsShared.BuffRarity.NotApplicable),
		"ApplyCoolDown": tunable.Tunable(description = "Whether or not adding this buff should temporarily prevent new menstrual buffs from being added.", tunable_type = bool, default = True),
		"ApplyRarityOffset": tunable.Tunable(description = "Whether or not adding this buff will temporarily offset the chances that a buff of certain rarity types will appear.", tunable_type = bool, default = True),
		"CyclePhaseTest": CyclePhaseTest.TunableFactory(description = "A test to determine if this buff can be added based on their current menstrual cycle."),
	}

	Rarity: BuffsShared.BuffRarity
	ApplyCoolDown: bool
	ApplyRarityOffset: bool
	CyclePhaseTest: CyclePhaseTest

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			_menstrualBuffs.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

	def on_add (self, from_load = False, apply_buff_loot = True) -> None:
		returnValue = super().on_add(from_load = from_load, apply_buff_loot = apply_buff_loot)

		ownerSimInfo = self._owner  # type: sim_info.SimInfo
		ownerSimSystem = Reproduction.GetSimSystem(ownerSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if ownerSimSystem is None:
			return

		ownerEffectTracker = ownerSimSystem.GetTracker(UniversalShared.EffectTrackerIdentifier)  # type: typing.Any

		if ownerEffectTracker is None:
			return

		ownerMenstrualEffect = ownerEffectTracker.GetEffect(EffectsShared.MenstrualEffectTypeIdentifier)

		if ownerMenstrualEffect is None:
			return

		ownerMenstrualEffect.NotifyBuffAdded(self, fromLoad = from_load)

		return returnValue

	def on_remove (self, apply_loot_on_remove: bool = True) -> None:
		returnValue = super().on_remove(apply_loot_on_remove = apply_loot_on_remove)

		ownerSimInfo = self._owner  # type: sim_info.SimInfo
		ownerSimSystem = Reproduction.GetSimSystem(ownerSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if ownerSimSystem is None:
			return

		ownerEffectTracker = ownerSimSystem.GetTracker(UniversalShared.EffectTrackerIdentifier)  # type: typing.Any

		if ownerEffectTracker is None:
			return

		ownerMenstrualEffect = ownerEffectTracker.GetEffect(EffectsShared.MenstrualEffectTypeIdentifier)

		if ownerMenstrualEffect is None:
			return

		ownerMenstrualEffect.NotifyBuffRemoved(self)

		return returnValue

def GetAllMenstrualBuffs () -> typing.List[typing.Type[MenstrualBuff]]:
	"""
	Get all buffs that use the MenstrualBuff type.
	"""

	return list(_menstrualBuffs)

def GetMenstrualBuffsWithRarity (rarity: BuffsShared.BuffRarity) -> typing.List[typing.Type[MenstrualBuff]]:
	"""
	Get all menstrual buffs with a rarity flag that matches the input rarity flag.
	"""

	if not isinstance(rarity, BuffsShared.BuffRarity):
		raise Exceptions.IncorrectTypeException(rarity, "rarity", (BuffsShared.BuffRarity, ))

	matchingBuffs = list()  # type: typing.List[typing.Type[MenstrualBuff]]

	for menstrualBuff in _menstrualBuffs:  # type: typing.Type[MenstrualBuff]
		if menstrualBuff.Rarity in rarity:
			matchingBuffs.append(menstrualBuff)

	return matchingBuffs

def IsMenstrualBuff (testingBuff: typing.Union[buff.Buff, typing.Type[buff.Buff]]) -> bool:
	"""
	Get whether or not the testing buff is a menstrual buff.
	"""

	if not isinstance(testingBuff, (buff.Buff, type)):
		raise Exceptions.IncorrectTypeException(testingBuff, "testingBuff", (buff.Buff, type))

	if not isinstance(testingBuff, type):
		testingBuff = testingBuff.buff_type

	return issubclass(testingBuff, MenstrualBuff)
