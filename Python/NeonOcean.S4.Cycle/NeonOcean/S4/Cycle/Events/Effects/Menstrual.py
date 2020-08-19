from __future__ import annotations

import copy
import random
import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Buffs import Menstrual as BuffsMenstrual, Shared as BuffsShared
from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Cycle.Females.Cycle import Menstrual as CycleMenstrual
from NeonOcean.S4.Cycle.Tools import Probability
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Exceptions, Python
from buffs import buff
from sims import sim_info

class MenstrualEffectBuffAddedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, addedBuff: buff.Buff, *args, **kwargs):
		if not isinstance(addedBuff, buff.Buff):
			raise Exceptions.IncorrectTypeException(addedBuff, "addedBuff", (buff.Buff,))

		super().__init__(*args, **kwargs)

		self._addedBuff = addedBuff  # type: buff.Buff

	@property
	def AddedBuff (self) -> buff.Buff:
		return self._addedBuff

class MenstrualEffectBuffRemovedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, removedBuff: buff.Buff, *args, **kwargs):
		if not isinstance(removedBuff, buff.Buff):
			raise Exceptions.IncorrectTypeException(removedBuff, "removedBuff", (buff.Buff,))

		super().__init__(*args, **kwargs)

		self._removedBuff = removedBuff  # type: buff.Buff

	@property
	def RemovedBuff (self) -> buff.Buff:
		return self._removedBuff

class MenstrualEffectBuffSelectionTestingArguments(EventsBase.SeededAndTargetedArguments):
	def __init__ (self, seed: int, targetedObject: sim_info.SimInfo, *args, **kwargs):
		"""
		Event arguments to determine what menstrual effect buff should be added, or choose to abstain from adding one.
		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The sim the event has been triggered for.
		:type targetedObject: typing.Any
		"""

		if not isinstance(targetedObject, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetedObject, "targetedObject", (sim_info.SimInfo,))

		super().__init__(seed, targetedObject, *args, **kwargs)

		self.BuffRarityBase = None

		self._buffRarityOptionAdjusters = dict()

	if typing.TYPE_CHECKING:
		TargetedObject: sim_info.SimInfo

	@property
	def BuffRarityBase (self) -> typing.Optional[Probability.Probability]:
		"""
		A probability object to act as the buff rarity base, to be modified with option adjusters later.
		"""

		return self._buffRarityBase

	@BuffRarityBase.setter
	def BuffRarityBase (self, value: typing.Optional[Probability.Probability]) -> None:
		if not isinstance(value, Probability.Probability) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "BuffRarityBase", (Probability.Probability, None))

		self._buffRarityBase = value

	def GetBuffRarityOptionAdjusters (self, option: str) -> typing.List[Probability.OptionAdjuster]:
		if not isinstance(option, str):
			raise Exceptions.IncorrectTypeException(option, "option", (str, ))

		buffRarityOptionAdjusters = self._buffRarityOptionAdjusters.get(option, None)  # type: typing.List[Probability.OptionAdjuster]

		if buffRarityOptionAdjusters is None:
			return list()
		else:
			return buffRarityOptionAdjusters

	def AddBuffRarityOptionAdjuster (self, option: str, adjuster: Probability.OptionAdjuster) -> None:
		if not isinstance(option, str):
			raise Exceptions.IncorrectTypeException(option, "option", (str, ))

		if not isinstance(adjuster, Probability.OptionAdjuster):
			raise Exceptions.IncorrectTypeException(adjuster, "adjuster", (Probability.OptionAdjuster, ))

		buffRarityOptionAdjusters = self._buffRarityOptionAdjusters.get(option, None)  # type: typing.List[Probability.OptionAdjuster]

		if buffRarityOptionAdjusters is None:
			self._buffRarityOptionAdjusters[option] = [ adjuster ]
		else:
			buffRarityOptionAdjusters.append(adjuster)

	def GetBuffRarity (self) -> typing.Optional[Probability.Probability]:
		buffRarityBase = self.BuffRarityBase  # type: typing.Optional[Probability.Probability]

		if buffRarityBase is None:
			return None

		buffRarity = copy.copy(buffRarityBase)  # type: Probability.Probability
		self._ApplyRarityOffsets(buffRarity)
		return buffRarity

	def SelectBuffRarity (self) -> typing.Optional[BuffsShared.BuffRarity]:
		"""
		Randomly select a buff rarity based on the current state of the effect and the system. This will return None if no buff rarity was selected.
		"""

		buffRarity = self.GetBuffRarity()  # type: typing.Optional[Probability.Probability]

		if buffRarity is None:
			Debug.Log("Could not get a valid buff rarity probability object, the buff rarity base value was probably never set.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			return None

		if not buffRarity.HasOptions:
			Debug.Log("Retrieved a buff rarity probability object had no options to pick from.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			return None

		rarityChoiceSeed = self.Seed + 470760185  # type: int
		rarityChoiceString = self.GetBuffRarity().ChooseOption(rarityChoiceSeed).Identifier  # type: str

		try:
			if rarityChoiceString == "Abstain":
				return None
			else:
				return BuffsShared.BuffRarity[rarityChoiceString]
		except:
			Debug.Log("Failed to parse rarity option identifier '%s'" % rarityChoiceString, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			return None

	def SelectAppropriateBuff (self, menstrualCycle: CycleMenstrual.MenstrualCycle) -> typing.Tuple[typing.Optional[typing.Type[BuffsMenstrual.MenstrualBuffBase]], bool]:
		"""
		Randomly select an appropriate buff for target sim with a menstrual cycle in the input cycle's state.
		:param menstrualCycle: The menstrual cycle which we will look at to find appropriate buffs for the event's target sim.
		:type menstrualCycle: CycleMenstrual.MenstrualCycle
		:return: The selected buff type, if any, and a boolean indicating whether or not there where any valid buffs to select.
		"""

		if not isinstance(menstrualCycle, CycleMenstrual.MenstrualCycle):
			raise Exceptions.IncorrectTypeException(menstrualCycle, "menstrualCycle", (CycleMenstrual.MenstrualCycle,))

		rarityChoice = self.SelectBuffRarity()  # type: typing.Optional[BuffsShared.BuffRarity]

		if rarityChoice is None:
			return None, self._HasValidBuffType(menstrualCycle)
		else:
			validBuffs = self._GetValidBuffTypesWithRarity(rarityChoice, menstrualCycle)  # type: typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]]

			if len(validBuffs) == 0:
				return None, self._HasValidBuffType(menstrualCycle)

			random.seed(self.Seed + -579905054)
			selectedBuffType = random.choice(validBuffs)  # type: typing.Type[BuffsMenstrual.MenstrualBuffBase]
			return selectedBuffType, True

	def _ApplyRarityOffsets (self, rarityProbabilities: Probability.Probability) -> None:
		"""
		Adjust a probability object's offsets according to the results of this test.
		:param rarityProbabilities: The probability object meant to be adjusted.
		:type rarityProbabilities: Probability.Probability
		"""

		for optionIdentifier, optionAdjusters in self._buffRarityOptionAdjusters.items():  # type: str, typing.List[Probability.OptionAdjuster]
			for optionAdjuster in optionAdjusters:  # type: Probability.OptionAdjuster
				rarityOption = rarityProbabilities.GetOption(optionIdentifier)  # type: Probability.Option

				if rarityOption is None:
					continue

				optionAdjuster.AdjustOption(rarityOption)

	def _GetValidBuffTypesWithRarity (self, rarity: BuffsShared.BuffRarity, menstrualCycle: CycleMenstrual.MenstrualCycle) -> typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]]:
		validBuffs = BuffsMenstrual.GetMenstrualBuffsWithRarity(rarity)  # type:  typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]]
		self._FilterValidBuffTypes(validBuffs, menstrualCycle)
		return validBuffs

	def _GetValidBuffTypes (self, menstrualCycle: CycleMenstrual.MenstrualCycle) -> typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]]:
		validBuffs = BuffsMenstrual.GetAllMenstrualBuffs()  # type:  typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]]
		self._FilterValidBuffTypes(validBuffs, menstrualCycle)
		return validBuffs

	def _HasValidBuffType (self, menstrualCycle: CycleMenstrual.MenstrualCycle) -> bool:
		validBuffs = BuffsMenstrual.GetAllMenstrualBuffs()  # type:  typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]]

		for buffType in validBuffs:  # type: typing.Type[BuffsMenstrual.MenstrualBuffBase]
			if self._BuffIsValid(buffType, menstrualCycle):
				return True

		return False

	def _FilterValidBuffTypes (self, validBuffs: typing.List[typing.Type[BuffsMenstrual.MenstrualBuffBase]], menstrualCycle: CycleMenstrual.MenstrualCycle) -> None:
		buffIndex = 0  # type: int
		while buffIndex < len(validBuffs):
			buffType = validBuffs[buffIndex]  # type: typing.Type[BuffsMenstrual.MenstrualBuffBase]

			if not self._BuffIsValid(buffType, menstrualCycle):
				validBuffs.pop(buffIndex)
				continue

			buffIndex += 1

	def _BuffIsValid (self, buffType: typing.Type[BuffsMenstrual.MenstrualBuffBase], menstrualCycle: CycleMenstrual.MenstrualCycle) -> bool:
		if not buffType.can_add(self.TargetedObject):
			return False

		if self.TargetedObject.Buffs.has_buff(buffType):
			return False

		if not buffType.CyclePhaseTest.InValidPhase(menstrualCycle):
			return False

		return True
