from __future__ import annotations

import copy
import random
import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared
from NeonOcean.S4.Cycle.Effects import Base as EffectsBase, Menstrual as EffectsMenstrual, Shared as EffectsShared, Types as EffectsTypes
from NeonOcean.S4.Cycle.Females import CycleTracker, Shared as FemalesShared
from NeonOcean.S4.Cycle.Tools import Probability
from NeonOcean.S4.Cycle.Universal import EffectTracker, Shared as UniversalShared
from NeonOcean.S4.Main.Tools import Classes, Exceptions, Savable

class BirthControlPillsEffect(EffectsBase.EffectBase):
	def __init__ (self, effectingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(effectingSystem)

		self.Need = 1
		self.Entrenchment = 0

		self.GameMinutesSinceLastPill = None

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Need", "Need", self.Need))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Entrenchment", "Entrenchment", self.Entrenchment))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("GameMinutesSinceLastPill", "GameMinutesSinceLastPill", self.GameMinutesSinceLastPill))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This effect type's identifier, this is used to save and load the effect. Loading will not be possible unless the cycle type is registered
		through the function in the effect types module.
		"""

		return EffectsShared.BirthControlPillsEffectTypeIdentifier

	@property
	def BirthControlPillsEffectGuide (self) -> CycleGuides.BirthControlPillsEffectGuide:
		"""
		Get the birth control pills effect guide for this affecting sim.
		"""

		return CycleGuides.BirthControlPillsEffectGuide.GetGuide(self.AffectingSystem.GuideGroup)

	@property
	def Need (self) -> float:
		"""
		A measure of how recently the affecting system last took a birth control pill, from 0 to 1. At a value of 0, the sim has just taken a new pill. At a
		value of 1, the sim has not taken their medicine around the time they where suppose to and the entrenchment value should be decreasing.
		"""

		return self._need

	@Need.setter
	def Need (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "Need", (float, int))

		if value < 0 or value > 1:
			raise ValueError("Need values must be between 0 and 1.")

		self._need = value

	@property
	def Entrenchment (self) -> float:
		"""
		A number from 0 to 1 indicating how entrenched the medication is. This is used to simulate how birth control might not stop the first ovulation after you start
		taking them, or how periods will eventually become lighter or stop. It also is used to simulate how it may take a few weeks to start ovulating again after you
		stop taking the pills
		"""

		return self._entrenchment

	@Entrenchment.setter
	def Entrenchment (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "Entrenchment", (float, int))

		if value < 0 or value > 1:
			raise ValueError("Entrenchment values must be between 0 and 1.")

		self._entrenchment = value

	@property
	def GameMinutesSinceLastPill (self) -> typing.Optional[float]:
		"""
		The amount of time in game minutes since the last time the affecting sim took a birth control pill.
		"""

		return self._gameMinutesSinceLastPill

	@GameMinutesSinceLastPill.setter
	def GameMinutesSinceLastPill (self, value: typing.Optional[float]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "GameMinutesSinceLastPill", (float, int, None))

		self._gameMinutesSinceLastPill = value

	def GetAmountOfMissedPills (self) -> typing.Optional[int]:
		"""
		Get the amount of pills the affecting sim has officially missed since they last one. This can return none if the sim has never taken any birth control pills.
		"""

		effectGuide = self.BirthControlPillsEffectGuide  # type: CycleGuides.BirthControlPillsEffectGuide

		gameMinutesSinceLastPill = self.GameMinutesSinceLastPill  # type: float

		if gameMinutesSinceLastPill is None:
			return None

		return int(max(gameMinutesSinceLastPill - effectGuide.GameMinutesBeforePillMissed, 0) / effectGuide.GameMinutesBetweenPills)

	def MissedPillsIntentional (self) -> bool:
		"""
		Get whether or not the number of pills the affecting sim missed appears to be intentional.
		"""

		amountOfMissedPills = self.GetAmountOfMissedPills()  # type: typing.Optional[int]

		if amountOfMissedPills is None:
			return True

		if amountOfMissedPills >= self.BirthControlPillsEffectGuide.MissedPillsBeforeIntentional:
			return True

		return False

	def OnBirthControlPills (self) -> bool:
		"""
		Get Whether or not the affecting sim is officially considered to be on birth control pills.
		"""

		amountOfMissedPills = self.GetAmountOfMissedPills()  # type: typing.Optional[int]

		if amountOfMissedPills is None:
			return False

		return self.MissedPillsIntentional()

	def TooRecentForTakePillInteraction (self) -> bool:
		"""
		Whether or not the affecting sim took a pill too recently for the take pill interaction to be usable again.
		"""

		gameMinutesSinceLastPill = self.GameMinutesSinceLastPill  # type: float

		if gameMinutesSinceLastPill is None:
			return False

		if gameMinutesSinceLastPill <= self.BirthControlPillsEffectGuide.GameMinutesUntilPillInteractionAllowed:
			return True

		return False

	def NotifyOfTakenPill (self) -> None:
		"""
		Notify the effect that the sim has now taken another birth control pill.
		"""

		self.Need = 0
		self.GameMinutesSinceLastPill = 0

	def GetDebugNotificationString (self) -> str:
		need = self.Need  # type: float
		entrenchment = self.Entrenchment  # type: float

		if need == 1 and entrenchment == 0:
			return ""

		debugStringTemplate = "Need: {Need}\n" \
							  "Entrenchment: {Entrenchment}\n" \
							  "Ovum Chance: {OvumChance}%"  # type: str

		debugStringFormatting = {
			"Need": str(round(need, 4)),
			"Entrenchment": str(round(entrenchment, 4)),
			"OvumChance": str(round(self._GetOvumSuppressionChance() * 100, 1))
		}

		return debugStringTemplate.format_map(debugStringFormatting)

	def _GetOvumSuppressionChance (self) -> float:
		return self.BirthControlPillsEffectGuide.OvumReleaseSuppressionCurve.Evaluate(self.Entrenchment)  # type: float

	def _SetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == UniversalShared.EffectTrackerIdentifier:
			self._SetEffectTrackerCallbacks(tracker)
		elif tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._SetCycleTrackerCallbacks(tracker)

	def _SetCycleTrackerCallbacks (self, tracker) -> None:
		tracker.CycleReleaseOvumTestingEvent += self._CycleTrackerCycleReleaseOvumTestingCallback

	def _SetEffectTrackerCallbacks (self, tracker) -> None:
		for effect in tracker.ActiveEffects:
			self._SetEffectCallbacks(effect)

		tracker.EffectAddedEvent += self._EffectsTrackerEffectAddedCallback
		tracker.EffectRemovedEvent += self._EffectsTrackerEffectRemovedCallback

	def _UnsetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == UniversalShared.EffectTrackerIdentifier:
			self._UnsetEffectTrackerCallbacks(tracker)
		elif tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._UnsetCycleTrackerCallbacks(tracker)

	def _UnsetCycleTrackerCallbacks (self, tracker) -> None:
		tracker.CycleReleaseOvumTestingEvent -= self._CycleTrackerCycleReleaseOvumTestingCallback

	def _UnsetEffectTrackerCallbacks (self, tracker) -> None:
		for effect in tracker.ActiveEffects:
			self._UnsetTrackerCallbacks(effect)

		tracker.EffectAddedEvent -= self._EffectsTrackerEffectAddedCallback
		tracker.EffectRemovedEvent -= self._EffectsTrackerEffectRemovedCallback

	def _SetEffectCallbacks (self, effect) -> None:
		if effect.TypeIdentifier == EffectsShared.MenstrualEffectTypeIdentifier:
			self._SetMenstrualEffectCallbacks(effect)

	def _SetMenstrualEffectCallbacks (self, effect) -> None:
		effect.BuffSelectionTestingEvent += self._MenstrualEffectBuffSelectionTestingCallback

	def _UnsetEffectCallbacks (self, effect) -> None:
		if effect.TypeIdentifier == EffectsShared.MenstrualEffectTypeIdentifier:
			self._UnsetMenstrualEffectCallbacks(effect)

	def _UnsetMenstrualEffectCallbacks (self, effect) -> None:
		effect.BuffSelectionTestingEvent -= self._MenstrualEffectBuffSelectionTestingCallback

	def _OnAdded (self) -> None:
		self.AffectingSystem.TrackerAddedEvent += self._TrackerAddedCallback

		for tracker in self.AffectingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._SetTrackerCallbacks(tracker)

	def _OnRemoving (self) -> None:
		self.AffectingSystem.TrackerAddedEvent -= self._TrackerAddedCallback

		for tracker in self.AffectingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._UnsetTrackerCallbacks(tracker)

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		simulatingMinutes = ReproductionShared.TicksToReproductiveMinutes(ticks, reproductiveTimeMultiplier)  # type: float
		gameMinutes = ReproductionShared.TicksToGameMinutes(ticks)  # type: float

		effectGuide = self.BirthControlPillsEffectGuide  # type: CycleGuides.BirthControlPillsEffectGuide

		currentNeed = self.Need  # type: float
		nextNeed = self.Need  # type: float

		if effectGuide.NeedPerGameMinute != 0:
			if effectGuide.NeedPerGameMinute > 0:
				if currentNeed != 1:
					nextNeed += gameMinutes * effectGuide.NeedPerGameMinute

			else:
				if currentNeed != 0:
					nextNeed += gameMinutes * effectGuide.NeedPerGameMinute

		nextNeed = min(max(nextNeed, 0), 1)

		currentEntrenchmentRate = effectGuide.EntrenchmentPerReproductiveMinute.Evaluate(currentNeed)  # type: float
		nextEntrenchmentRate = effectGuide.EntrenchmentPerReproductiveMinute.Evaluate(nextNeed)  # type: float

		averageEntrenchmentRate = (currentEntrenchmentRate + nextEntrenchmentRate) / 2  # type: float  # This is probably only right if the curve is linear.

		currentEntrenchment = self.Entrenchment
		nextEntrenchment = self.Entrenchment

		if averageEntrenchmentRate != 0:
			if averageEntrenchmentRate > 0:
				if currentEntrenchment != 1:
					nextEntrenchment += simulatingMinutes * averageEntrenchmentRate
			else:
				if currentEntrenchment != 0:
					nextEntrenchment += simulatingMinutes * averageEntrenchmentRate

		nextEntrenchment = min(max(nextEntrenchment, 0), 1)

		gameMinutesSinceLastPill = self.GameMinutesSinceLastPill  # type: float

		self.Need = nextNeed
		self.Entrenchment = nextEntrenchment

		if gameMinutesSinceLastPill is not None:
			self.GameMinutesSinceLastPill = gameMinutesSinceLastPill + gameMinutes

	# noinspection PyUnusedLocal
	def _TrackerAddedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._SetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _TrackerRemovedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._UnsetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _CycleTrackerCycleReleaseOvumTestingCallback (self, owner: CycleTracker.CycleTracker, eventArguments: CycleEvents.CycleReleaseOvumTestingArguments) -> None:
		suppressionChance = self._GetOvumSuppressionChance()  # type: float

		random.seed(self.AffectingSystem.CreateUniqueSeed() + 262842484)
		suppressionRoll = random.random()  # type: float

		if suppressionRoll <= suppressionChance:
			eventArguments.Release = False

	# noinspection PyUnusedLocal
	def _EffectsTrackerEffectAddedCallback (self, owner: EffectTracker.EffectTracker, eventArguments: CycleEvents.EffectAddedArguments) -> None:
		self._SetEffectCallbacks(eventArguments.AddedEffect)

	# noinspection PyUnusedLocal
	def _EffectsTrackerEffectRemovedCallback (self, owner: EffectTracker.EffectTracker, eventArguments: CycleEvents.EffectRemovedArguments) -> None:
		self._UnsetEffectCallbacks(eventArguments.RemovedEffect)

	# noinspection PyUnusedLocal
	def _MenstrualEffectBuffSelectionTestingCallback (self, owner: EffectsMenstrual.MenstrualEffect, eventArguments: CycleEvents.MenstrualEffectBuffSelectionTestingArguments) -> None:
		for optionIdentifier, optionAdjuster in self.BirthControlPillsEffectGuide.MenstrualBuffRarityOptionAdjusters.items():  # type: str, Probability.OptionAdjuster
			optionAdjusterCopy = copy.copy(optionAdjuster)

			if isinstance(optionAdjusterCopy.Adjustment, Probability.OptionAdjustmentExpression):
				optionAdjusterCopy.Adjustment.AddVariables(**{
					"Need": self.Need,
					"Entrenchment": self.Entrenchment
				})

			eventArguments.AddBuffRarityOptionAdjuster(optionIdentifier, optionAdjusterCopy)

def _OnStart (cause) -> None:
	if cause:
		pass

	EffectsTypes.RegisterEffectType(BirthControlPillsEffect.TypeIdentifier, BirthControlPillsEffect)
