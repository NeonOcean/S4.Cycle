from __future__ import annotations

import typing

import services
from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, Settings, This
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Types
from sims import sim_info
from sims4 import resources
from statistics import commodity, commodity_tracker

class PregnancyTracker(ReproductionShared.TrackerBase):
	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self.PregnancyStartedEvent = Events.EventHandler()
		self.PregnancyEndedEvent = Events.EventHandler()
		self.FetusGeneratingEvent = Events.EventHandler()

		self.MonitoringPregnancy = False

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

		if self.TrackingSystem.SimInfo.is_pregnant:
			return True

		return False

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return FemalesShared.ShouldHaveFemaleTrackers(targetSimInfo)

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
			self.FixPregnancySpeed()

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

		trackingSimInfo = self.TrackingSystem.SimInfo  # type: sim_info.SimInfo

		gamePregnancyTracker = trackingSimInfo.pregnancy_tracker

		pregnancyCommodityType = gamePregnancyTracker.PREGNANCY_COMMODITY_MAP.get(trackingSimInfo.species)
		pregnancyCommodityTracker = trackingSimInfo.get_tracker(pregnancyCommodityType)  # type: commodity_tracker.CommodityTracker
		pregnancyCommodity = pregnancyCommodityTracker.get_statistic(pregnancyCommodityType)  # type: commodity.Commodity

		progress = pregnancyCommodity.get_value() / pregnancyCommodity.max_value  # type: float

		if progress < 0 or progress > 1:
			Debug.Log("Calculated the pregnancy progress (%s) as being less than 0 or greater than 1.\n%s" % (progress, self.DebugInformation),
					  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

			progress = min(max(progress, 0), 1)

		return progress

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

	def FixPregnancySpeed (self, ignoreSetting: bool = False) -> None:  # TODO support mods that adjust the pregnancy rate some how.
		"""
		Fix the pregnancy speed for the tracking sim, conform it to the tracker's reproductive time multiplier.
		"""

		if not isinstance(ignoreSetting, bool):
			raise Exceptions.IncorrectTypeException(ignoreSetting, "ignoreSetting", (bool,))

		if not Settings.HandlePregnancySpeed.Get() and not ignoreSetting:
			return

		if self.IsPregnant:
			trackingSimInfo = self.TrackingSystem.SimInfo  # type: sim_info.SimInfo

			pregnancyRate = self._GetPregnancyRate()  # type: float

			gamePregnancyTracker = trackingSimInfo.pregnancy_tracker
			gamePregnancyTracker.PREGNANCY_RATE = pregnancyRate

			pregnancyCommodityType = gamePregnancyTracker.PREGNANCY_COMMODITY_MAP.get(trackingSimInfo.species)
			pregnancyCommodityTracker = trackingSimInfo.get_tracker(pregnancyCommodityType)  # type: commodity_tracker.CommodityTracker
			pregnancyCommodity = pregnancyCommodityTracker.get_statistic(pregnancyCommodityType)  # type: typing.Optional[commodity.Commodity]

			if pregnancyCommodity is None:
				return

			# noinspection PyProtectedMember
			pregnancyCommodityModifier = pregnancyCommodity._statistic_modifier  # type: float

			if pregnancyCommodityModifier != pregnancyRate:
				# noinspection PyProtectedMember
				pregnancyCommodityModifiers = pregnancyCommodity._statistic_modifiers  # type: typing.Optional[list]

				if pregnancyCommodityModifiers is not None:
					pregnancyCommodityModifiers = list(pregnancyCommodityModifiers)  # type: list

					for modifier in pregnancyCommodityModifiers:
						pregnancyCommodity.remove_statistic_modifier(modifier)

				pregnancyCommodity.add_statistic_modifier(pregnancyRate)

	def GetDebugNotificationString (self) -> str:
		return "Pregnant: %s" % str(self.IsPregnant)

	def _GetPregnancyRate (self) -> float:
		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: float
		pregnancyTrackerGuide = CycleGuides.PregnancyTrackerGuide.GetGuide(self.TrackingSystem.GuideGroup)  # type: CycleGuides.PregnancyTrackerGuide

		pregnancyTime = pregnancyTrackerGuide.PregnancyTime  # type: float
		pregnancyGameTime = ReproductionShared.ReproductiveMinutesToGameMinutes(pregnancyTime, reproductiveTimeMultiplier)  # type: float

		if pregnancyGameTime != 0:
			pregnancyRate = 100 / pregnancyGameTime  # type: float
		else:
			Debug.Log("Calculated a pregnancy game time to be 0 minutes, this is probably not intentional.\n" + self.DebugInformation,
					  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 1)

			pregnancyRate = 0

		return pregnancyRate

	def _HasVisiblePregnancyBuff (self) -> bool:
		firstTrimesterBuffID = 12561  # type: int
		secondTrimesterBuffID = 12562  # type: int
		thirdTrimesterBuffID = 12563  # type: int

		buffManager = services.get_instance_manager(resources.Types.BUFF)
		firstTrimesterBuff = buffManager.get(firstTrimesterBuffID)
		secondTrimesterBuff = buffManager.get(secondTrimesterBuffID)
		thirdTrimesterBuff = buffManager.get(thirdTrimesterBuffID)

		if self.TrackingSystem.SimInfo.Buffs.has_buff(firstTrimesterBuff) or \
				self.TrackingSystem.SimInfo.Buffs.has_buff(secondTrimesterBuff) or \
				self.TrackingSystem.SimInfo.Buffs.has_buff(thirdTrimesterBuff):

			return True

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

	def _OnAdding(self) -> None:
		self.TrackingSystem.TrackerAddedEvent += self._TrackerAddedCallback

		for tracker in self.TrackingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._SetTrackerCallbacks(tracker)

	def _OnRemoving(self) -> None:
		self.TrackingSystem.TrackerAddedEvent -= self._TrackerAddedCallback

		for tracker in self.TrackingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._UnsetTrackerCallbacks(tracker)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return FemalesShared.GetPregnancyTrackerReproductiveTimeMultiplier()

	def _OnUpdatedReproductiveTimeMultiplier (self) -> None:
		self.FixPregnancySpeed()

	# noinspection PyUnusedLocal
	def _TrackerAddedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._SetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _TrackerRemovedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._UnsetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _CycleStartTestingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.CycleStartTestingArguments) -> None:
		if self.IsPregnant:
			eventArguments.CanStart.Value = False

	# noinspection PyUnusedLocal
	def _CycleAbortTestingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.CycleAbortTestingArguments) -> None:
		if self.IsPregnant:
			eventArguments.AbortCycle.Value = True
			eventArguments.AbortCycle.Locked = True
