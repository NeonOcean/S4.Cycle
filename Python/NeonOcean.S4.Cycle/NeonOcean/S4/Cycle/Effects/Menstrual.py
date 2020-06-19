from __future__ import annotations

import copy
import random
import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Buffs import Menstrual as BuffsMenstrual, Shared as BuffsShared
from NeonOcean.S4.Cycle.Effects import Base as EffectsBase, Shared as EffectsShared, Types as EffectsTypes
from NeonOcean.S4.Cycle.Females import CycleTracker, Shared as FemalesShared
from NeonOcean.S4.Cycle.Females.Cycle import Menstrual as CycleMenstrual, Shared as CycleShared
from NeonOcean.S4.Main import Debug, LoadingShared
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Types

if typing.TYPE_CHECKING:
	from NeonOcean.S4.Cycle.Tools import Probability, Distribution
	from buffs import buff

class MenstrualEffect(EffectsBase.EffectBase):
	def __init__ (self, effectingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(effectingSystem)

		self.BuffAddedEvent = Events.EventHandler()
		self.BuffRemovedEvent = Events.EventHandler()

		self._buffRarity = copy.copy(self.MenstruationEffectGuide.BuffRarity)  # type: Probability.Probability
		self._buffCoolDown = None  # type: typing.Optional[float]

		self.RegisterSavableAttribute(Savable.StaticSavableAttributeHandler("BuffRarity", "_buffRarity"))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BuffCoolDown", "_buffCoolDown", None))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This effect type's identifier, this is used to save and load the effect. Loading will not be possible unless the cycle type is registered
		through the function in the effect types module.
		"""

		return EffectsShared.MenstrualEffectTypeIdentifier

	@property
	def ShouldSave (self) -> bool:
		"""
		Whether or not we should save this handler.
		"""

		if not super().ShouldSave:
			return False

		return self.AffectingSystem.HasTracker(FemalesShared.CycleTrackerIdentifier)

	@property
	def BuffAddedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a menstruation effect buff was added.
		The event arguments parameter should be a 'MenstrualEffectBuffAddedArguments' object.
		"""

		return self._buffAddedEvent

	@BuffAddedEvent.setter
	def BuffAddedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "BuffAddedEvent", (Events.EventHandler,))

		self._buffAddedEvent = value

	@property
	def BuffRemovedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a menstruation effect buff was removed.
		The event arguments parameter should be a 'MenstrualEffectBuffRemovedArguments' object.
		"""

		return self._buffRemovedEvent

	@BuffRemovedEvent.setter
	def BuffRemovedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "BuffRemovedEvent", (Events.EventHandler,))

		self._buffRemovedEvent = value

	@property
	def MenstruationEffectGuide (self) -> CycleGuides.MenstrualEffectGuide:
		"""
		Get the menstruation effect guide for this affecting sim.
		"""

		return CycleGuides.MenstrualEffectGuide.GetGuide(self.AffectingSystem.GuideGroup)

	@property
	def MenstrualBuffs (self) -> typing.List[typing.Type[BuffsMenstrual.MenstrualBuff]]:
		"""
		Get a list of every menstrual buff type.
		"""

		return BuffsMenstrual.GetAllMenstrualBuffs()

	@property
	def BuffRarity (self) -> Probability.Probability:
		"""
		A probability object to randomly select the rarity of the next buff
		"""

		return self._buffRarity

	@property
	def BuffCoolDown (self) -> typing.Optional[float]:
		"""
		The times in sim minutes until a new buff can be added. This may be none if there is no active cool down.
		"""

		return self._buffCoolDown

	@BuffCoolDown.setter
	def BuffCoolDown (self, value: typing.Optional[float]) -> None:
		if not isinstance(value, float) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "BuffCoolDown", (float, None))

		self._buffCoolDown = value

	def NotifyBuffAdded (self, addedBuff: BuffsMenstrual.MenstrualBuff, fromLoad: bool = False) -> None:
		"""
		Notify the effect that a new menstrual buff was just added.
		"""

		if not isinstance(addedBuff, BuffsMenstrual.MenstrualBuff):
			raise Exceptions.IncorrectTypeException(addedBuff, "addedBuff", (BuffsMenstrual.MenstrualBuff,))

		if not isinstance(fromLoad, bool):
			raise Exceptions.IncorrectTypeException(fromLoad, "fromLoad", (bool,))

		eventArguments = CycleEvents.MenstrualEffectBuffAddedArguments(addedBuff)  # type: CycleEvents.MenstrualEffectBuffAddedArguments

		if addedBuff.ApplyCoolDown:
			self._ApplyBuffCoolDown(addedBuff.Rarity)

		if addedBuff.ApplyRarityOffset:
			self._ApplyRarityOffset(addedBuff.Rarity)

		for buffAddedCallback in self.BuffAddedEvent:
			try:
				buffAddedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call buff added callback '" + Types.GetFullName(buffAddedCallback) + "'.\n" + self.AffectingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = buffAddedCallback)

	def NotifyBuffRemoved (self, removedBuff: BuffsMenstrual.MenstrualBuff) -> None:
		"""
		Notify the effect that a new buff was just added.
		"""

		if not isinstance(removedBuff, BuffsMenstrual.MenstrualBuff):
			raise Exceptions.IncorrectTypeException(removedBuff, "removedBuff", (BuffsMenstrual.MenstrualBuff,))

		eventArguments = CycleEvents.MenstrualEffectBuffRemovedArguments(removedBuff)  # type: CycleEvents.MenstrualEffectBuffRemovedArguments

		for buffRemovedCallback in self.BuffRemovedEvent:
			try:
				buffRemovedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call buff removed callback '" + Types.GetFullName(buffRemovedCallback) + "'.\n" + self.AffectingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = buffRemovedCallback)

	def GetMenstrualBuffsWithRarity (self, rarity: BuffsShared.BuffRarity) -> typing.List[typing.Type[BuffsMenstrual.MenstrualBuff]]:
		"""
		Get all menstrual buffs with a rarity flag that matches the input rarity flag.
		"""

		return BuffsMenstrual.GetMenstrualBuffsWithRarity(rarity)

	def SimHasBuffWithRarity (self, rarity: BuffsShared.BuffRarity) -> bool:
		"""
		Get whether or not the affecting sim has a buff with a rarity flag that matches the input rarity flag.
		"""

		affectingSimInfo = self.AffectingSystem.SimInfo

		for menstrualBuff in self.GetMenstrualBuffsWithRarity(rarity):  # type: typing.Type[buff.Buff]
			if affectingSimInfo.has_buff(menstrualBuff):
				return True

		return False

	def SimBuffWithRarityCount (self, rarity: BuffsShared.BuffRarity) -> int:
		"""
		Get number of the affecting sim's buffs that have a rarity flag that matches the input rarity flag.
		"""

		matchingMenstrualBuffs = 0  # type: int

		affectingSimInfo = self.AffectingSystem.SimInfo

		for menstrualBuff in self.GetMenstrualBuffsWithRarity(rarity):  # type: typing.Type[buff.Buff]
			if affectingSimInfo.has_buff(menstrualBuff):
				matchingMenstrualBuffs += 1

		return matchingMenstrualBuffs

	def _ApplyBuffCoolDown (self, buffRarity: BuffsShared.BuffRarity) -> None:
		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		coolDownDistribution = effectGuide.BuffCoolDown.get(buffRarity)  # type: typing.Optional[Distribution.NormalDistribution]

		if coolDownDistribution is None:
			return

		coolDown = coolDownDistribution.GenerateValue(seed = self.AffectingSystem.CreateUniqueSeed() + -135824265, minimum = 0)

		self._buffCoolDown = coolDown

	def _ApplyAbstainedCoolDown (self) -> None:
		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		coolDownDistribution = effectGuide.AbstainedBuffCoolDown
		coolDown = coolDownDistribution.GenerateValue(seed = self.AffectingSystem.CreateUniqueSeed() + 453777896, minimum = 0)

		self._buffCoolDown = coolDown

	def _ApplyRarityOffset (self, buffRarity: BuffsShared.BuffRarity) -> None:
		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		optionAdjusters = effectGuide.BuffRarityOffsets.get(buffRarity)  # type: typing.Optional[typing.Dict[str, Probability.OptionWeightAdjuster]]

		if optionAdjusters is None:
			return

		for optionIdentifier, optionAdjuster in optionAdjusters.items():  # type: str, Probability.OptionWeightAdjuster
			rarityOption = self.BuffRarity.GetOption(optionIdentifier)  # type: typing.Optional[Probability.Option]

			if rarityOption is None:
				continue

			optionAdjuster.AdjustOption(rarityOption)

	def _ApplyAbstainedRarityOffset (self) -> None:
		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		for optionIdentifier, optionAdjuster in effectGuide.AbstainedBuffRarityOffset.items():  # type: str, Probability.OptionWeightAdjuster
			rarityOption = self.BuffRarity.GetOption(optionIdentifier)  # type: typing.Optional[Probability.Option]

			if rarityOption is None:
				continue

			optionAdjuster.AdjustOption(rarityOption)

	def _GetValidBuffTypes (self, currentCycle: CycleMenstrual.MenstrualCycle) -> typing.List[typing.Type[BuffsMenstrual.MenstrualBuff]]:
		validBuffs = self.MenstrualBuffs  # type:  typing.List[typing.Type[BuffsMenstrual.MenstrualBuff]]

		affectingSimInfo = self.AffectingSystem.SimInfo

		buffIndex = 0  # type: int
		while buffIndex < len(validBuffs):
			buffType = validBuffs[buffIndex]  # type: typing.Type[BuffsMenstrual.MenstrualBuff]

			if not buffType.can_add(affectingSimInfo):
				validBuffs.pop(buffIndex)
				continue

			if affectingSimInfo.Buffs.has_buff(buffType):
				validBuffs.pop(buffIndex)
				continue

			if not buffType.CyclePhaseTest.InValidPhase(currentCycle):
				validBuffs.pop(buffIndex)
				continue

			buffIndex += 1

		return validBuffs

	def _OnAdded (self) -> None:
		self.AffectingSystem.PlanUpdateEvent += self._PlanUpdateCallback

	def _OnRemoving (self) -> None:
		self.AffectingSystem.PlanUpdateEvent -= self._PlanUpdateCallback

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		simulatingGameMinutes = ReproductionShared.TicksToGameMinutes(ticks)  # type: float

		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		if self.BuffCoolDown is not None:
			self.BuffCoolDown -= simulatingGameMinutes

			if self.BuffCoolDown <= 0:
				self.BuffCoolDown = None

		for buffRarityOption in self.BuffRarity.Options:  # type: Probability.Option
			if buffRarityOption.WeightOffset == 0:
				continue

			rarityResetRate = effectGuide.BuffRarityResetRates.get(buffRarityOption.Identifier, None)

			if rarityResetRate is None:
				Debug.Log("Missing rarity reset rate for an option that has been offset.\nOption Identifier: %s" % buffRarityOption.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 1)
				continue

			if buffRarityOption.WeightOffset < 0:
				buffRarityOption.WeightOffset += rarityResetRate * simulatingGameMinutes
			else:
				buffRarityOption.WeightOffset += -rarityResetRate * simulatingGameMinutes

		if not self.AffectingSystem.SimInfo.is_instanced():
			return  # The game doesn't appear to allow us to add the buffs to non-instanced sims.

		if not self.BuffRarity.HasOptions:
			Debug.Log("Buff rarity probability object has no options to pick from.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 1)
			return

		if not simulation.LastTickStep:
			return

		cycleTracker = self.AffectingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]

		if cycleTracker is None:
			return

		currentCycle = cycleTracker.CurrentCycle  # type: typing.Optional[CycleMenstrual.MenstrualCycle]

		if currentCycle is None:
			return

		if currentCycle.TypeIdentifier != CycleShared.MenstrualCycleTypeIdentifier:
			return

		affectingSimInfo = self.AffectingSystem.SimInfo

		if self.BuffCoolDown is not None and self.BuffCoolDown > 0:
			return

		validBuffs = self._GetValidBuffTypes(currentCycle)  # type: typing.List[typing.Type[BuffsMenstrual.MenstrualBuff]]

		if len(validBuffs) == 0:
			return

		rarityChoiceSeed = self.AffectingSystem.CurrentSeed + 470760185  # type: int
		rarityChoiceString = self.BuffRarity.ChooseOption(rarityChoiceSeed).Identifier  # type: str

		try:
			if rarityChoiceString == "Abstain":
				self._ApplyAbstainedCoolDown()
				self._ApplyAbstainedRarityOffset()
				return
			else:
				rarityChoice = BuffsShared.BuffRarity[rarityChoiceString]
		except:
			Debug.Log("Failed to parse rarity option identifier '%s'" % rarityChoiceString, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			self._ApplyAbstainedCoolDown()
			self._ApplyAbstainedRarityOffset()
			return

		matchingValidBuffs = list()  # type: typing.List[typing.Type[BuffsMenstrual.MenstrualBuff]]

		for validBuff in validBuffs:  # type: typing.Type[BuffsMenstrual.MenstrualBuff]
			if validBuff.Rarity == rarityChoice:
				matchingValidBuffs.append(validBuff)

		if len(matchingValidBuffs) == 0:
			self._ApplyAbstainedCoolDown()
			self._ApplyAbstainedRarityOffset()
			return

		random.seed(self.AffectingSystem.CurrentSeed + -579905054)
		selectedBuffType = random.choice(matchingValidBuffs)  # type: typing.Type[BuffsMenstrual.MenstrualBuff]
		affectingSimInfo.Buffs.add_buff_from_op(selectedBuffType)

	# noinspection PyUnusedLocal
	def _PlanUpdateCallback (self, owner, eventArguments: CycleEvents.PlanUpdateArguments) -> None:
		if not self.AffectingSystem.SimInfo.is_instanced():
			return  # The game doesn't appear to allow us to add the buffs to non-instanced sims.

		cycleTracker = self.AffectingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]

		if cycleTracker is None:
			return

		if cycleTracker.CurrentCycle is None:
			return

		currentCycle = cycleTracker.CurrentCycle  # type: typing.Optional[CycleMenstrual.MenstrualCycle]

		if currentCycle.TypeIdentifier != CycleShared.MenstrualCycleTypeIdentifier:
			return

		if self.BuffCoolDown is not None and self.BuffCoolDown > 0:
			eventArguments.RequestTick(ReproductionShared.GameMinutesToTicks(self.BuffCoolDown))
			return

		soonestBuffValidTick = None  # type: typing.Optional[int]

		for menstrualBuff in self.MenstrualBuffs:  # type: BuffsMenstrual.MenstrualBuff
			ticksUntilBuffValid = menstrualBuff.CyclePhaseTest.TicksUntilValidPhase(currentCycle, cycleTracker.ReproductiveTimeMultiplier)  # type: int

			if ticksUntilBuffValid is None:
				continue

			if soonestBuffValidTick is None or soonestBuffValidTick > ticksUntilBuffValid:
				soonestBuffValidTick = ticksUntilBuffValid

		if soonestBuffValidTick is None or soonestBuffValidTick <= 0:
			return

		eventArguments.RequestTick(soonestBuffValidTick)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	EffectsTypes.RegisterEffectType(MenstrualEffect.TypeIdentifier, MenstrualEffect)
