from __future__ import annotations

import typing
import random

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, Settings
from NeonOcean.S4.Cycle.Effects import Base as EffectsBase, Shared as EffectsShared, Types as EffectsTypes
from NeonOcean.S4.Cycle.Females import CycleTracker, Shared as FemalesShared, OvumTracker, SpermTracker
from NeonOcean.S4.Cycle.Tools import Distribution
from NeonOcean.S4.Main.Tools import Classes, Exceptions

class EmergencyContraceptivePillEffect(EffectsBase.EffectBase):
	effectOvumGuaranteeIdentifier = "EmergencyContraceptivePillEffect"  # type: str

	def __init__ (self, effectingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(effectingSystem)

		self.Strength = 0

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This effect type's identifier, this is used to save and load the effect. Loading will not be possible unless the cycle type is registered
		through the function in the effect types module.
		"""

		return EffectsShared.EmergencyContraceptivePillEffectTypeIdentifier

	@property
	def EmergencyContraceptivePillEffectGuide (self) -> CycleGuides.EmergencyContraceptivePillEffectGuide:
		"""
		Get the emergency contraceptive pill effect guide for this affecting sim.
		"""

		return CycleGuides.EmergencyContraceptivePillEffectGuide.GetGuide(self.AffectingSystem.GuideGroup)

	@property
	def Strength (self) -> float:
		"""
		A number from 0 to 1 indicating how strong the medication is. 1 means the pill was taken recently and is at the maximum strength, 0 means the pill
		is out of the sim's system, if they've ever taken one at all.
		"""

		return self._strength

	@Strength.setter
	def Strength (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "Strength", (float, int))

		if value < 0 or value > 1:
			raise ValueError("Strength values must be between 0 and 1.")

		self._strength = value

	def NotifyOfTakenPill (self) -> None:
		"""
		Notify the effect that the sim has now taken an emergency contraceptive pill.
		"""

		self.Strength = 1

	def GenerateOvumDelay(self, strength: float, seed: typing.Optional[typing.Hashable] = None) -> float:
		"""
		Generate a random ovum delay based on this strength value and using this seed.
		"""

		if not isinstance(strength, (float, int)):
			raise Exceptions.IncorrectTypeException(strength, "strength", (float, int))

		if strength < 0 or strength > 1:
			raise ValueError("The 'strength' parameter must be between 0 and 1.")

		effectGuide = self.EmergencyContraceptivePillEffectGuide  # type: CycleGuides.EmergencyContraceptivePillEffectGuide

		delayTimeMean = effectGuide.DelayTimeMean.Evaluate(strength)  # type: float
		delayTimeStandardDeviation = effectGuide.DelayTimeStandardDeviation.Evaluate(strength)  # type: float

		random.seed(seed)
		delayTimeDistribution = Distribution.NormalDistribution(mean = delayTimeMean, standardDeviation = delayTimeStandardDeviation)  # type: Distribution.NormalDistribution
		delayTime = delayTimeDistribution.GenerateValue(seed, minimum = 0, maximum = effectGuide.DelayTimeMaximum)  # type: float

		return delayTime

	def _SetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._SetCycleTrackerCallbacks(tracker)
		elif tracker.TypeIdentifier == FemalesShared.OvumTrackerIdentifier:
			self._SetOvumTrackerCallbacks(tracker)

	def _SetCycleTrackerCallbacks (self, tracker) -> None:
		tracker.CycleReleaseOvumTestingEvent += self._CycleTrackerCycleReleaseOvumTestingCallback

	def _SetOvumTrackerCallbacks (self, tracker) -> None:
		tracker.OvumReleasedEvent += self._OvumTrackerOvumReleasedCallback

	def _UnsetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._UnsetCycleTrackerCallbacks(tracker)
		elif tracker.TypeIdentifier == FemalesShared.OvumTrackerIdentifier:
			self._UnsetOvumTrackerCallbacks(tracker)

	def _UnsetCycleTrackerCallbacks (self, tracker) -> None:
		tracker.CycleReleaseOvumTestingEvent -= self._CycleTrackerCycleReleaseOvumTestingCallback

	def _UnsetOvumTrackerCallbacks (self, tracker) -> None:
		tracker.OvumReleasedEvent -= self._OvumTrackerOvumReleasedCallback

	def _OnAdded (self) -> None:
		self.AffectingSystem.TrackerAddedEvent += self._TrackerAddedCallback

		for tracker in self.AffectingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._SetTrackerCallbacks(tracker)

	def _OnRemoving (self) -> None:
		self.AffectingSystem.TrackerAddedEvent -= self._TrackerAddedCallback

		for tracker in self.AffectingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._UnsetTrackerCallbacks(tracker)

	# noinspection PyUnusedLocal
	def _TrackerAddedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._SetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _TrackerRemovedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._UnsetTrackerCallbacks(eventArguments.Tracker)

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		simulatingMinutes = ReproductionShared.TicksToReproductiveMinutes(ticks, reproductiveTimeMultiplier)  # type: float

		effectGuide = self.EmergencyContraceptivePillEffectGuide  # type: CycleGuides.EmergencyContraceptivePillEffectGuide

		currentStrength = self.Strength  # type: float
		nextStrength = self.Strength  # type: float

		if effectGuide.StrengthPerReproductiveMinute != 0:
			if effectGuide.StrengthPerReproductiveMinute > 0:
				if currentStrength != 1:
					nextStrength += simulatingMinutes * effectGuide.StrengthPerReproductiveMinute

			else:
				if currentStrength != 0:
					nextStrength += simulatingMinutes * effectGuide.StrengthPerReproductiveMinute

		nextStrength = min(max(nextStrength, 0), 1)

		self.Strength = nextStrength

	# noinspection PyUnusedLocal
	def _CycleTrackerCycleReleaseOvumTestingCallback (self, owner: CycleTracker.CycleTracker, eventArguments: CycleEvents.CycleReleaseOvumTestingArguments) -> None:
		if Settings.QuickMode.Get():
			return  # We handle ova in a different way for quick mode.

		if self.Strength <= 0:
			return

		if eventArguments.TargetedObject.IsReleaseMinuteGuaranteed(self.effectOvumGuaranteeIdentifier):
			return

		effectGuide = self.EmergencyContraceptivePillEffectGuide  # type: CycleGuides.EmergencyContraceptivePillEffectGuide

		effectOvumDelayTime = self.GenerateOvumDelay(self.Strength, seed = self.AffectingSystem.CreateUniqueSeed())  # type: float

		if effectOvumDelayTime == 0:
			return

		currentOvumDelayTime = eventArguments.TargetedObject.ReleaseDelay  # type: float
		nextOvumDelayTime = min(effectOvumDelayTime + eventArguments.TargetedObject.ReleaseDelay, effectGuide.DelayTimeMaximum)  # type: float

		if currentOvumDelayTime == nextOvumDelayTime:
			eventArguments.TargetedObject.GuaranteeReleaseMinute(self.effectOvumGuaranteeIdentifier)
			return

		eventArguments.TargetedObject.GuaranteeReleaseMinute(self.effectOvumGuaranteeIdentifier)
		eventArguments.TargetedObject.ReleaseDelay = nextOvumDelayTime
		eventArguments.Release = False

	# noinspection PyUnusedLocal
	def _OvumTrackerOvumReleasedCallback(self, owner: OvumTracker.OvumTracker, eventArguments: CycleEvents.OvumReleasedArguments) -> None:
		if not Settings.QuickMode.Get():
			return

		if self.Strength <= 0:
			return

		spermTracker = self.AffectingSystem.GetTracker(FemalesShared.SpermTrackerIdentifier)  # type: typing.Optional[SpermTracker.SpermTracker]

		if spermTracker is None:
			return

		effectGuide = self.EmergencyContraceptivePillEffectGuide  # type: CycleGuides.EmergencyContraceptivePillEffectGuide

		spermBlockChance = effectGuide.QuickModeSpermBlockChance.Evaluate(self.Strength)  # type: float

		for activeSperm in spermTracker.ActiveSperm:
			random.seed(self.AffectingSystem.CurrentSeed + activeSperm.UniqueSeed)
			spermBlockRoll = random.random()  # type: float

			if spermBlockRoll <= spermBlockChance:
				eventArguments.TargetedObject.BlockSperm(str(activeSperm.UniqueIdentifier))

def _OnStart (cause) -> None:
	if cause:
		pass

	EffectsTypes.RegisterEffectType(EmergencyContraceptivePillEffect.TypeIdentifier, EmergencyContraceptivePillEffect)
