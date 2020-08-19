from __future__ import annotations

import typing
import random

import services
from NeonOcean.S4.Cycle import Events as CycleEvents, References, ReproductionShared, This, Guides
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Cycle.Females.Cycle import Shared as CycleShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Types
from protocolbuffers import PersistenceBlobs_pb2
from sims import sim_info, sim_info_types
from sims4 import resources
from statistics import commodity, commodity_tracker

class PregnancyTracker(ReproductionShared.TrackerBase):
	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self.PregnancyStartedEvent = Events.EventHandler()
		self.PregnancyEndedEvent = Events.EventHandler()
		self.FetusGeneratingEvent = Events.EventHandler()

		self.MonitoringPregnancy = False

		self._cachedPregnancyTestResult = None  # type: typing.Optional[bool]
		self._cachedPregnancyTestGameMinutesRemaining = None  # type: typing.Optional[float]

		self._nonPregnantBellyModifier = 0 # type: float
		self._pregnancyVisualsActive = False  # type: bool

		self.PregnancyStartedEvent += self._PregnancyStartedCallback

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		return FemalesShared.PregnancyTrackerIdentifier

	@property
	def PregnancyStartedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when the tracking sim has become pregnant.
		The event arguments parameter should be a 'PregnancyStartedArguments' object.
		"""

		return self._pregnancyStartedEvent

	@PregnancyStartedEvent.setter
	def PregnancyStartedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "PregnancyStartedEvent", (Events.EventHandler,))

		self._pregnancyStartedEvent = value

	@property
	def PregnancyEndedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when the tracking sim's pregnancy ends.
		The event arguments parameter should be a 'PregnancyEndedArguments' object.
		"""

		return self._pregnancyEndedEvent

	@PregnancyEndedEvent.setter
	def PregnancyEndedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "PregnancyEndedEvent", (Events.EventHandler,))

		self._pregnancyEndedEvent = value

	@property
	def IsPregnant (self) -> bool:
		"""
		Whether or not this sim is pregnant, pregnancy begins as soon as the egg cell implants.
		"""

		if not self.TrackingSystem.SimInfo.is_pregnant:
			return False

		return True

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return True

	def NotifyPregnancyStarted (self) -> None:
		"""
		Notify this reproductive system that a pregnancy has started. If we are already monitoring the pregnancy, or no pregnancy for this sim is
		detected, nothing will happen.
		"""

		if not self.IsPregnant:
			return

		if self.MonitoringPregnancy:
			return

		self.MonitoringPregnancy = True
		eventArguments = CycleEvents.PregnancyStartedArguments()

		for pregnancyStartedCallback in self.PregnancyStartedEvent:
			try:
				pregnancyStartedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call pregnancy started callback '" + Types.GetFullName(pregnancyStartedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = pregnancyStartedCallback)

		self.SetPregnancyVisualsIfAppropriate()

	def NotifyPregnancyEnded (self) -> None:
		"""
		Notify this reproductive system that a pregnancy has ended. If we are not monitoring the pregnancy, or we detect the sim is still
		pregnant, nothing will happen.
		"""

		if self.IsPregnant:
			return

		if not self.MonitoringPregnancy:
			return

		self.MonitoringPregnancy = False
		eventArguments = CycleEvents.PregnancyEndedArguments()

		for pregnancyEndedCallback in self.PregnancyEndedEvent:
			try:
				pregnancyEndedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call pregnancy ended callback '" + Types.GetFullName(pregnancyEndedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = pregnancyEndedCallback)

		self.ResetPregnancyVisualsIfAppropriate()

	def StartPregnancy (self, firstParent: typing.Optional[sim_info.SimInfo], secondParent: typing.Optional[sim_info.SimInfo], overrideParents: bool = False, addOffspring: bool = True) -> None:
		"""
		Start a pregnancy for the tracking sim.
		:param firstParent: One of the two biological parents of the baby. This will be replaced with the second parent or this system's tracking sim if None.
		:type firstParent: sim_info.SimInfo | None
		:param secondParent: One of the two biological parents of the baby. This will be replaced with the first parent or this system's tracking sim if None.
		:type secondParent: sim_info.SimInfo | None
		:param overrideParents: Whether or not to override the parents of any currently active pregnancy. Having more than one set of parents to a single
		pregnancy is not currently supported.
		:type overrideParents: sim_info.SimInfo | None
		:param addOffspring: Whether or not to add a new offspring if this sim is already pregnant.
		:type addOffspring: bool
		"""

		if not isinstance(firstParent, sim_info.SimInfo) and firstParent is not None:
			raise Exceptions.IncorrectTypeException(firstParent, "firstParent", (sim_info.SimInfo, None))

		if not isinstance(secondParent, sim_info.SimInfo) and secondParent is not None:
			raise Exceptions.IncorrectTypeException(secondParent, "secondParent", (sim_info.SimInfo, None))

		if not isinstance(overrideParents, bool):
			raise Exceptions.IncorrectTypeException(overrideParents, "overrideParents", (bool,))

		if not isinstance(addOffspring, bool):
			raise Exceptions.IncorrectTypeException(addOffspring, "addOffspring", (bool,))

		if firstParent is None and secondParent is None:
			firstParent = self.TrackingSystem.SimInfo
			secondParent = self.TrackingSystem.SimInfo
		else:
			if firstParent is None and secondParent is not None:
				firstParent = secondParent
			elif secondParent is None and firstParent is not None:
				secondParent = firstParent

		gamePregnancyTracker = self.TrackingSystem.SimInfo.pregnancy_tracker

		if not self.IsPregnant:
			gamePregnancyTracker.start_pregnancy(firstParent, secondParent)
			gamePregnancyTracker.offspring_count_override = 1
		else:
			if addOffspring:
				gamePregnancyTracker.offspring_count_override += 1

			if overrideParents:
				gamePregnancyTracker._parent_ids = (firstParent.id, secondParent.id)

	def PregnancyIsKnown (self) -> bool:
		"""
		Whether or not the sim knows that they are pregnant. This will always be false if the sim is not pregnant.
		"""

		if not self.IsPregnant:
			return False

		if self._HasVisiblePregnancyBuff():
			return True

		pregnancyTrimester = self.GetPregnancyTrimester()  # type: typing.Optional[FemalesShared.PregnancyTrimester]

		if pregnancyTrimester is None or pregnancyTrimester == FemalesShared.PregnancyTrimester.First:
			return False

		return False

	def GetPregnancyProgress (self) -> float:
		"""
		Get the amount the active pregnancy has progressed toward completion. This will be a number from 0 to 1.
		"""

		if not self.IsPregnant:
			return 0

		gamePregnancyTracker = self.TrackingSystem.SimInfo.pregnancy_tracker

		pregnancyCommodityType = gamePregnancyTracker.PREGNANCY_COMMODITY_MAP.get(self.TrackingSystem.SimInfo.species)  # type: typing.Type[commodity.Commodity]
		pregnancyCommodityTracker = self.TrackingSystem.SimInfo.get_tracker(pregnancyCommodityType)  # type: commodity_tracker.CommodityTracker
		pregnancyCommodity = pregnancyCommodityTracker.get_statistic(pregnancyCommodityType, add = True)  # type: commodity.Commodity

		pregnancyProgress = pregnancyCommodity.get_value() / pregnancyCommodity.max_value  # type: float

		if pregnancyProgress < 0 or pregnancyProgress > 1:
			Debug.Log("Calculated the pregnancy progress (%s) as being less than 0 or greater than 1.\n%s" % (pregnancyProgress, self.DebugInformation),
					  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

			pregnancyProgress = min(max(pregnancyProgress, 0), 1)

		return pregnancyProgress

	def SetPregnancyProgress (self, pregnancyProgress: float) -> None:
		"""
		Set the amount the active pregnancy has progressed toward completion. The input progress should be a number from 0 to 1. Nothing will happen
		if this system's sim is not pregnant.
		"""

		if not isinstance(pregnancyProgress, (float, int)):
			raise Exceptions.IncorrectTypeException(pregnancyProgress, "pregnancyProgress", (float, int))

		if pregnancyProgress < 0 or pregnancyProgress > 1:
			raise ValueError("The parameter 'pregnancyProgress' must be between or equal to 0 and 1.")

		if not self.IsPregnant:
			return

		gamePregnancyTracker = self.TrackingSystem.SimInfo.pregnancy_tracker

		pregnancyCommodityType = gamePregnancyTracker.PREGNANCY_COMMODITY_MAP.get(self.TrackingSystem.SimInfo.species)  # type: typing.Type[commodity.Commodity]
		pregnancyCommodityTracker = self.TrackingSystem.SimInfo.get_tracker(pregnancyCommodityType)  # type: commodity_tracker.CommodityTracker
		pregnancyCommodity = pregnancyCommodityTracker.get_statistic(pregnancyCommodityType, add = True)  # type: commodity.Commodity

		pregnancyCommodity.set_value(pregnancyCommodity.max_value * pregnancyProgress)

	def GetPregnancyTrimester (self) -> typing.Optional[FemalesShared.PregnancyTrimester]:
		"""
		Get the trimester that the active pregnancy is on. This will be none if no pregnancy is active.
		"""

		if not self.IsPregnant:
			return None

		pregnancyProgress = self.GetPregnancyProgress()  # type: float

		trimesterProgress = 100 / 3  # type: float

		if pregnancyProgress < trimesterProgress:
			return FemalesShared.PregnancyTrimester.First
		elif pregnancyProgress < trimesterProgress * 2:
			return FemalesShared.PregnancyTrimester.Second
		else:
			return FemalesShared.PregnancyTrimester.Third

	def GeneratePregnancyTestResults (self, ignoreCachedResults: bool = False) -> bool:
		"""
		Get whether or a pregnancy test, if taken at this moment, should come up positive or negative.
		"""

		if not ignoreCachedResults and self._cachedPregnancyTestResult is not None:
			# The pregnancy test results are cached so that players can't just test multiple times in quick succession to rule out false positives or negatives.
			return self._cachedPregnancyTestResult

		pregnancyGuide = Guides.PregnancyGuide.GetGuide(self.TrackingSystem.GuideGroup)  # type: Guides.PregnancyGuide

		if not self.IsPregnant:
			falsePositiveRoll = random.random()  # type: float

			if falsePositiveRoll <= pregnancyGuide.PregnancyTestFalsePositiveProbability:
				testResult = True
			else:
				testResult = False
		else:
			pregnancyProgress = self.GetPregnancyProgress()  # type: float

			positiveRoll = random.random()  # type: float

			if positiveRoll <= pregnancyGuide.PregnancyTestProgressProbability.Evaluate(pregnancyProgress):
				testResult = True
			else:
				testResult = False

		self._CachePregnancyTestResults(testResult)

		return testResult

	def GetPregnancyBellyModifierValue (self) -> float:
		"""
		Get the belly modifier value the tracking sim should have due to their pregnancy. This will return a value from -1 to 1.
		"""

		pregnancyProgress = self.GetPregnancyProgress()  # type: float
		nonPregnantBellyModifier = self._nonPregnantBellyModifier  # type: float
		fullPregnancyDistance = 1 - self._nonPregnantBellyModifier  # type: float
		bellyModifier = nonPregnantBellyModifier + fullPregnancyDistance * pregnancyProgress

		return bellyModifier

	def SetPregnancyVisuals (self) -> None:
		"""
		Set the tracking sim's pregnancy visuals. This method will assume the tracking sim should have pregnancy visuals.
		"""

		if not self._pregnancyVisualsActive:
			self._nonPregnantBellyModifier = self._GetCurrentBellyModifierValue()

		self._ApplyBellyModifierValue(self.GetPregnancyBellyModifierValue())  # type: float
		self._pregnancyVisualsActive = True

	def SetPregnancyVisualsIfAppropriate (self) -> None:
		"""
		Set the tracking sim's pregnancy visuals if it is appropriate for them to have.
		"""

		if not self.IsPregnant:
			return

		self.SetPregnancyVisuals()

	def ResetPregnancyVisuals (self) -> None:
		"""
		Reset the sim's pregnancy visuals. This will change the tracking sim's belly modifiers back to what they where we the pregnancy started.
		"""

		self._ApplyBellyModifierValue(self._nonPregnantBellyModifier)
		self._pregnancyVisualsActive = False

	def ResetPregnancyVisualsIfAppropriate (self) -> None:
		"""
		Reset the sim's pregnancy visuals if they have been changed by this tracker.
		"""

		if not self._pregnancyVisualsActive:
			return

		self.ResetPregnancyVisuals()

	def GetDebugNotificationString (self) -> str:
		return "Pregnant: %s" % str(self.IsPregnant)

	def Verify(self) -> None:
		if self.IsPregnant and not self.MonitoringPregnancy:
			self.NotifyPregnancyStarted()
		elif not self.IsPregnant and self.MonitoringPregnancy:
			self.NotifyPregnancyEnded()

	def _CachePregnancyTestResults (self, result: bool) -> None:
		self._cachedPregnancyTestResult = result
		self._cachedPregnancyTestGameMinutesRemaining = 120

	def _ResetCachedPregnancyTestResults (self) -> None:
		self._cachedPregnancyTestResult = None
		self._cachedPregnancyTestGameMinutesRemaining = None

	def _GetCurrentBellyModifierValue (self) -> float:
		hasFeminineFrameTrait = self._HasFeminineFrameTrait()  # type: bool
		hasMasculineFrameTrait = self._HasMasculineFrameTrait()  # type: bool

		if hasFeminineFrameTrait or (not hasFeminineFrameTrait and not hasMasculineFrameTrait and self.TrackingSystem.SimInfo.gender == sim_info_types.Gender.FEMALE):
			appropriatePositiveModifierKey = References.FemaleBellyPositiveModifierKey  # type: int
			appropriateNegativeModifierKey = References.FemaleBellyNegativeModifierKey  # type: int
		elif hasMasculineFrameTrait or (not hasFeminineFrameTrait and not hasMasculineFrameTrait and self.TrackingSystem.SimInfo.gender == sim_info_types.Gender.MALE):
			appropriatePositiveModifierKey = References.MaleBellyPositiveModifierKey  # type: int
			appropriateNegativeModifierKey = References.MaleBellyNegativeModifierKey  # type: int
		else:
			Debug.Log("Could not determine the frame type or gender of a system's sim.\n" + self.DebugInformation,
					  This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

			return 0

		simAttributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()  # type: typing.Any
		# noinspection PyPropertyAccess
		simAttributes.ParseFromString(self.TrackingSystem.SimInfo.facial_attributes)

		for bodyModifier in simAttributes.body_modifiers:
			if bodyModifier.key == appropriatePositiveModifierKey:
				return bodyModifier.amount
			elif bodyModifier.key == appropriateNegativeModifierKey:
				return bodyModifier.amount * -1

		return 0

	def _ApplyBellyModifierValue (self, applyingModifierValue: float) -> None:
		hasFeminineFrameTrait = self._HasFeminineFrameTrait()  # type: bool
		hasMasculineFrameTrait = self._HasMasculineFrameTrait()  # type: bool

		if hasFeminineFrameTrait or (not hasFeminineFrameTrait and not hasMasculineFrameTrait and self.TrackingSystem.SimInfo.gender == sim_info_types.Gender.FEMALE):
			appropriatePositiveModifierKey = References.FemaleBellyPositiveModifierKey  # type: int
			appropriateNegativeModifierKey = References.FemaleBellyNegativeModifierKey  # type: int
		elif hasMasculineFrameTrait or (not hasFeminineFrameTrait and not hasMasculineFrameTrait and self.TrackingSystem.SimInfo.gender == sim_info_types.Gender.MALE):
			appropriatePositiveModifierKey = References.MaleBellyPositiveModifierKey  # type: int
			appropriateNegativeModifierKey = References.MaleBellyNegativeModifierKey  # type: int
		else:
			Debug.Log("Could not determine the frame type or gender of a system's sim.\n" + self.DebugInformation,
					  This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

			return

		simAttributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()  # type: typing.Any
		# noinspection PyPropertyAccess
		simAttributes.ParseFromString(self.TrackingSystem.SimInfo.facial_attributes)

		if applyingModifierValue > 0:
			targetModifierKey = appropriatePositiveModifierKey  # type: int
			inappropriateModifierKey = appropriateNegativeModifierKey  # type: int
			targetModifierValue = applyingModifierValue  # type: float
		else:
			targetModifierKey = appropriateNegativeModifierKey
			inappropriateModifierKey = appropriatePositiveModifierKey  # type: int
			targetModifierValue = applyingModifierValue * -1  # type: float

		for bodyModifier in simAttributes.body_modifiers:
			if bodyModifier.key == targetModifierKey:
				bodyModifier.amount = targetModifierValue

		bodyModifierIndex = 0
		while bodyModifierIndex < len(simAttributes.body_modifiers):
			bodyModifier = simAttributes.body_modifiers[bodyModifierIndex]

			if bodyModifier.key == inappropriateModifierKey:
				del simAttributes.body_modifiers[bodyModifierIndex]
				continue

			bodyModifierIndex += 1

		self.TrackingSystem.SimInfo.facial_attributes = simAttributes.SerializeToString()

	def _HasVisiblePregnancyBuff (self) -> bool:
		buffManager = services.get_instance_manager(resources.Types.BUFF)
		firstTrimesterBuff = buffManager.get(References.PregnancyFirstTrimesterBuffID)
		secondTrimesterBuff = buffManager.get(References.PregnancySecondTrimesterBuffID)
		thirdTrimesterBuff = buffManager.get(References.PregnancyThirdTrimesterBuffID)
		inLaborBuff = buffManager.get(References.PregnancyInLaborBuffID)

		if self.TrackingSystem.SimInfo.Buffs.has_buff(firstTrimesterBuff) or \
				self.TrackingSystem.SimInfo.Buffs.has_buff(secondTrimesterBuff) or \
				self.TrackingSystem.SimInfo.Buffs.has_buff(thirdTrimesterBuff) or \
				self.TrackingSystem.SimInfo.Buffs.has_buff(inLaborBuff):

			return True

		return False

	def _HasFeminineFrameTrait (self) -> bool:
		feminineFrameTrait = services.get_instance_manager(resources.Types.TRAIT).get(References.FeminineFrameTraitID)

		if feminineFrameTrait is not None:
			return self.TrackingSystem.SimInfo.has_trait(feminineFrameTrait)
		else:
			Debug.Log("Could not find the feminine frame trait.\nTrait ID: %s" % References.FeminineFrameTraitID,
					  This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 1)

			return False

	def _HasMasculineFrameTrait (self) -> bool:
		masculineFrameTrait = services.get_instance_manager(resources.Types.TRAIT).get(References.MasculineFrameTraitID)

		if masculineFrameTrait is not None:
			return self.TrackingSystem.SimInfo.has_trait(masculineFrameTrait)
		else:
			Debug.Log("Could not find the masculine frame trait.\nTrait ID: %s" % References.MasculineFrameTraitID,
					  This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 1)

			return False

	def _SetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._SetCycleTrackerCallbacks(tracker)

	def _SetCycleTrackerCallbacks (self, tracker) -> None:
		tracker.CycleStartTestingEvent += self._CycleStartTestingCallback
		tracker.CycleAbortTestingEvent += self._CycleAbortTestingCallback

	def _UnsetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._UnsetCycleTrackerCallbacks(tracker)

	def _UnsetCycleTrackerCallbacks (self, tracker) -> None:
		tracker.CycleStartTestingEvent -= self._CycleStartTestingCallback
		tracker.CycleAbortTestingEvent -= self._CycleAbortTestingCallback

	def _Setup(self) -> None:
		if self.IsPregnant:
			self.NotifyPregnancyStarted()

	def _OnAdded (self) -> None:
		self.SetPregnancyVisualsIfAppropriate()

		self.TrackingSystem.TrackerAddedEvent += self._TrackerAddedCallback
		self.TrackingSystem.TrackerRemovedEvent += self._TrackerRemovedCallback

		for tracker in self.TrackingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._SetTrackerCallbacks(tracker)

	def _OnRemoving (self) -> None:
		self.ResetPregnancyVisualsIfAppropriate()

		self.TrackingSystem.TrackerAddedEvent -= self._TrackerAddedCallback
		self.TrackingSystem.TrackerRemovedEvent -= self._TrackerRemovedCallback

		for tracker in self.TrackingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._UnsetTrackerCallbacks(tracker)

	def _OnLoaded(self) -> None:
		self.SetPregnancyVisualsIfAppropriate()

	def _OnResetting(self) -> None:
		self.ResetPregnancyVisualsIfAppropriate()

	# noinspection PyUnusedLocal
	def _PregnancyCachedTestSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		simulatingGameMinutes = ReproductionShared.TicksToGameMinutes(ticks)  # type: float

		if self._cachedPregnancyTestGameMinutesRemaining is not None:
			self._cachedPregnancyTestGameMinutesRemaining -= simulatingGameMinutes

			if self._cachedPregnancyTestGameMinutesRemaining <= 0:
				self._ResetCachedPregnancyTestResults()

	# noinspection PyUnusedLocal
	def _PregnancyVisualsSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		if self.IsPregnant:
			self.SetPregnancyVisualsIfAppropriate()
		else:
			self.ResetPregnancyVisualsIfAppropriate()

	def _PlanSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		if self._cachedPregnancyTestGameMinutesRemaining is not None:
			ticksUntilPregnancyTestCacheReset = ReproductionShared.GameMinutesToTicks(self._cachedPregnancyTestGameMinutesRemaining)

			if simulation.RemainingTicks >= ticksUntilPregnancyTestCacheReset:
				simulation.Schedule.AddPoint(ticksUntilPregnancyTestCacheReset)

	def _PrepareForSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PrepareForSimulation(simulation)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(30, self._PregnancyCachedTestSimulationPhase)
		)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(-30, self._PregnancyVisualsSimulationPhase)
		)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return FemalesShared.GetPregnancyTrackerReproductiveTimeMultiplier()

	# noinspection PyUnusedLocal
	def _TrackerAddedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._SetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _TrackerRemovedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._UnsetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _PregnancyStartedCallback(self, owner: PregnancyTracker, eventArguments: CycleEvents.PregnancyStartedArguments) -> None:
		cycleTracker = self.TrackingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Any

		if cycleTracker is None:
			return

		if cycleTracker.CurrentCycle is not None:
			cycleTracker.CurrentCycle.End(CycleShared.CompletionReasons.Pregnancy)

	# noinspection PyUnusedLocal
	def _CycleStartTestingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.CycleStartTestingArguments) -> None:
		if self.IsPregnant:
			eventArguments.CanStart.Value = False

	# noinspection PyUnusedLocal
	def _CycleAbortTestingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.CycleAbortTestingArguments) -> None:
		if self.IsPregnant:
			eventArguments.AbortCycle.Value = True
			eventArguments.AbortCycle.Locked = True
