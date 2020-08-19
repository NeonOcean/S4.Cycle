from __future__ import annotations

import copy
import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Buffs import Menstrual as BuffsMenstrual, Shared as BuffsShared
from NeonOcean.S4.Cycle.Effects import Base as EffectsBase, Shared as EffectsShared, Types as EffectsTypes
from NeonOcean.S4.Cycle.Females import CycleTracker, Shared as FemalesShared
from NeonOcean.S4.Cycle.Females.Cycle import Menstrual as CycleMenstrual, Shared as CycleShared
from NeonOcean.S4.Cycle.Tools import Probability
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Types

if typing.TYPE_CHECKING:
	from NeonOcean.S4.Cycle.Tools import Distribution

class MenstrualEffect(EffectsBase.EffectBase):
	def __init__ (self, effectingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(effectingSystem)

		self.BuffAddedEvent = Events.EventHandler()
		self.BuffRemovedEvent = Events.EventHandler()
		self.BuffSelectionTestingEvent = Events.EventHandler()

		self._buffCoolDown = None  # type: typing.Optional[float]

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BuffCoolDown", "BuffCoolDown", self.BuffCoolDown))

		self.BuffSelectionTestingEvent += self._BuffSelectionTestingCallback

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
	def BuffSelectionTestingEvent (self) -> Events.EventHandler:
		"""
		Event arguments to determine what menstrual effect buff should be added, or choose to abstain from adding one.
		The event arguments parameter should be a 'MenstrualEffectBuffSelectionTestingArguments' object.
		"""

		return self._buffSelectionTestingEvent

	@BuffSelectionTestingEvent.setter
	def BuffSelectionTestingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "BuffSelectionTestingEvent", (Events.EventHandler,))

		self._buffSelectionTestingEvent = value

	@property
	def MenstruationEffectGuide (self) -> CycleGuides.MenstrualEffectGuide:
		"""
		Get the menstruation effect guide for this affecting sim.
		"""

		return CycleGuides.MenstrualEffectGuide.GetGuide(self.AffectingSystem.GuideGroup)

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

	def NotifyBuffAdded (self, addedBuff: BuffsMenstrual.MenstrualBuffBase, fromLoad: bool = False) -> None:
		"""
		Notify the effect that a new menstrual buff was just added.
		"""

		if not isinstance(addedBuff, BuffsMenstrual.MenstrualBuffBase):
			raise Exceptions.IncorrectTypeException(addedBuff, "addedBuff", (BuffsMenstrual.MenstrualBuffBase,))

		if not isinstance(fromLoad, bool):
			raise Exceptions.IncorrectTypeException(fromLoad, "fromLoad", (bool,))

		eventArguments = CycleEvents.MenstrualEffectBuffAddedArguments(addedBuff)  # type: CycleEvents.MenstrualEffectBuffAddedArguments

		self.ApplyBuffEffects(addedBuff)

		for buffAddedCallback in self.BuffAddedEvent:
			try:
				buffAddedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call buff added callback '" + Types.GetFullName(buffAddedCallback) + "'.\n" + self.AffectingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = buffAddedCallback)

	def NotifyBuffRemoved (self, removedBuff: BuffsMenstrual.MenstrualBuffBase) -> None:
		"""
		Notify the effect that a new buff was just added.
		"""

		if not isinstance(removedBuff, BuffsMenstrual.MenstrualBuffBase):
			raise Exceptions.IncorrectTypeException(removedBuff, "removedBuff", (BuffsMenstrual.MenstrualBuffBase,))

		eventArguments = CycleEvents.MenstrualEffectBuffRemovedArguments(removedBuff)  # type: CycleEvents.MenstrualEffectBuffRemovedArguments

		for buffRemovedCallback in self.BuffRemovedEvent:
			try:
				buffRemovedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call buff removed callback '" + Types.GetFullName(buffRemovedCallback) + "'.\n" + self.AffectingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = buffRemovedCallback)

	def DoBuffSelectionTesting (self) -> CycleEvents.MenstrualEffectBuffSelectionTestingArguments:
		eventArguments = CycleEvents.MenstrualEffectBuffSelectionTestingArguments(self.AffectingSystem.CurrentSeed, self.AffectingSystem.SimInfo)  # type: CycleEvents.MenstrualEffectBuffSelectionTestingArguments

		for buffSelectionTestingCallback in self.BuffSelectionTestingEvent:
			try:
				buffSelectionTestingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call buff selection testing callback '" + Types.GetFullName(buffSelectionTestingCallback) + "'.\n" + self.AffectingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = buffSelectionTestingCallback)

		return eventArguments

	def GetBaseBuffRarity (self) -> Probability.Probability:
		"""
		Get a copy of the affecting sim's base buff rarity probability object.
		"""

		return copy.copy(self.MenstruationEffectGuide.BuffRarity)

	def ApplyBuffAbstainedEffects (self) -> None:
		"""
		Apply the appropriate effects for when the opportunity to select a buff arose, but no buff was chosen.
		"""

		self.ApplyBuffAbstainedCoolDown()

	def ApplyBuffEffects (self, addedBuff: BuffsMenstrual.MenstrualBuffBase) -> None:
		"""
		Apply the appropriate effects for when a buff of this rarity is added to the affecting sim.
		"""

		if addedBuff.ApplyCoolDown:
			self.ApplyBuffRarityCoolDown(addedBuff.Rarity)

	def ApplyBuffRarityCoolDown (self, buffRarity: BuffsShared.BuffRarity) -> None:
		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		coolDownDistribution = effectGuide.BuffCoolDown.get(buffRarity)  # type: typing.Optional[Distribution.NormalDistribution]

		if coolDownDistribution is None:
			return

		coolDown = coolDownDistribution.GenerateValue(seed = self.AffectingSystem.CreateUniqueSeed() + -135824265, minimum = 0)

		self._buffCoolDown = coolDown

	def ApplyBuffAbstainedCoolDown (self) -> None:
		effectGuide = self.MenstruationEffectGuide  # type: CycleGuides.MenstrualEffectGuide

		coolDownDistribution = effectGuide.AbstainedBuffCoolDown
		coolDown = coolDownDistribution.GenerateValue(seed = self.AffectingSystem.CreateUniqueSeed() + 453777896, minimum = 0)

		self._buffCoolDown = coolDown

	def _OnAdded (self) -> None:
		self.AffectingSystem.PlanUpdateEvent += self._PlanUpdateCallback

	def _OnRemoving (self) -> None:
		self.AffectingSystem.PlanUpdateEvent -= self._PlanUpdateCallback

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		simulatingGameMinutes = ReproductionShared.TicksToGameMinutes(ticks)  # type: float

		if self.BuffCoolDown is not None:
			self.BuffCoolDown -= simulatingGameMinutes

			if self.BuffCoolDown <= 0:
				self.BuffCoolDown = None

		if self.BuffCoolDown is not None and self.BuffCoolDown > 0:
			return

		if not self.AffectingSystem.SimInfo.is_instanced():
			return  # The game doesn't appear to allow us to add the buffs to non-instanced sims.

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

		buffSelectionTesting = self.DoBuffSelectionTesting()  # type: CycleEvents.MenstrualEffectBuffSelectionTestingArguments
		selectedBuffType, hadValidSelections = buffSelectionTesting.SelectAppropriateBuff(currentCycle)  # type: typing.Optional[typing.Type[BuffsMenstrual.MenstrualBuffBase]], bool

		if not hadValidSelections:
			return

		if selectedBuffType is None:
			self.ApplyBuffAbstainedEffects()
			return

		self.AffectingSystem.SimInfo.Buffs.add_buff_from_op(selectedBuffType, BuffsShared.ReproductiveSystemBuffReason.GetLocalizationString())

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

		for menstrualBuff in BuffsMenstrual.GetAllMenstrualBuffs():  # type: BuffsMenstrual.MenstrualBuffBase
			ticksUntilBuffValid = menstrualBuff.CyclePhaseTest.TicksUntilValidPhase(currentCycle, cycleTracker.ReproductiveTimeMultiplier)  # type: int

			if ticksUntilBuffValid is None:
				continue

			if soonestBuffValidTick is None or soonestBuffValidTick > ticksUntilBuffValid:
				soonestBuffValidTick = ticksUntilBuffValid

		if soonestBuffValidTick is None or soonestBuffValidTick <= 0:
			return

		eventArguments.RequestTick(soonestBuffValidTick)

	# noinspection PyUnusedLocal
	def _BuffSelectionTestingCallback (self, owner: MenstrualEffect, eventArguments: CycleEvents.MenstrualEffectBuffSelectionTestingArguments) -> None:
		eventArguments.BuffRarityBase = self.GetBaseBuffRarity()

def _OnStart (cause) -> None:
	if cause:
		pass

	EffectsTypes.RegisterEffectType(MenstrualEffect.TypeIdentifier, MenstrualEffect)
