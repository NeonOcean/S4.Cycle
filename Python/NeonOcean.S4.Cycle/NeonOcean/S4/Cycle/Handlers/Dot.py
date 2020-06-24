from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Dot, Events as CycleEvents, ReproductionShared
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Cycle.Females.Cycle import Shared as CycleShared
from NeonOcean.S4.Cycle.Handlers import Base as HandlersBase, Shared as HandlersShared, Types as HandlersTypes
from NeonOcean.S4.Main import LoadingShared
from NeonOcean.S4.Main.Tools import Classes

if typing.TYPE_CHECKING:
	from NeonOcean.S4.Cycle.Females import PregnancyTracker, CycleTracker

class DotHandler(HandlersBase.HandlerBase):
	def __init__ (self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		return HandlersShared.DotHandlerTypeIdentifier

	@property
	def ShouldSave (self) -> bool:
		"""
		Whether or not we should save this handler.
		"""

		if not super().ShouldSave:
			return False

		return self.HandlingSystem.HasTracker(FemalesShared.CycleTrackerIdentifier)

	def _HandleTrackerAdded (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._HandleCycleTrackerAdded(tracker)
		elif tracker.TypeIdentifier == FemalesShared.PregnancyTrackerIdentifier:
			self._HandlePregnancyTrackerAdded(tracker)

	def _HandleCycleTrackerAdded (self, tracker) -> None:
		tracker.CycleChangedEvent += self._CycleTrackerCycleChangedCallback
		tracker.CycleCompletedEvent += self._CycleTrackerCycleCompletedCallback

		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			if dotInformation.TimeSinceCycleStart is None:
				if tracker.TimeSinceLastCycle is not None:
					dotInformation.TimeSinceCycleStart = tracker.TimeSinceLastCycle
				else:
					if tracker.CurrentCycle is not None:
						dotInformation.TimeSinceCycleStart = tracker.CurrentCycle.Age

	def _HandlePregnancyTrackerAdded (self, tracker) -> None:
		tracker.PregnancyStartedEvent += self._PregnancyTrackerPregnancyStartedCallback
		tracker.PregnancyEndedEvent += self._PregnancyTrackerPregnancyEndedCallback

	def _HandleTrackerRemoved (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.CycleTrackerIdentifier:
			self._HandleCycleTrackerRemoved(tracker)
		elif tracker.TypeIdentifier == FemalesShared.PregnancyTrackerIdentifier:
			self._HandlePregnancyTrackerRemoved(tracker)

	def _HandleCycleTrackerRemoved  (self, tracker) -> None:
		tracker.CycleChangedEvent -= self._PregnancyTrackerPregnancyStartedCallback
		tracker.CycleCompletedEvent -= self._PregnancyTrackerPregnancyEndedCallback

	def _HandlePregnancyTrackerRemoved  (self, tracker) -> None:
		tracker.PregnancyStartedEvent -= self._PregnancyTrackerPregnancyStartedCallback
		tracker.PregnancyEndedEvent -= self._PregnancyTrackerPregnancyEndedCallback

	def _OnAdded (self) -> None:
		self.HandlingSystem.TrackerAddedEvent += self._TrackerAddedCallback
		self.HandlingSystem.TrackerRemovedEvent += self._TrackerRemovedCallback

		for tracker in self.HandlingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._HandleTrackerAdded(tracker)

	def _OnRemoving(self) -> None:
		self.HandlingSystem.TrackerAddedEvent -= self._TrackerAddedCallback
		self.HandlingSystem.TrackerRemovedEvent -= self._TrackerRemovedCallback

		for tracker in self.HandlingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._HandleTrackerRemoved(tracker)

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		if not simulation.LastTickStep:
			return

		cycleTracker = self.HandlingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]
		pregnancyTracker = self.HandlingSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

		if cycleTracker is None:
			return

		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			if simulation.NonUpdateTicks > 0:
				dotInformation.Simulate(simulation.NonUpdateTicks)

			if pregnancyTracker is not None:
				if dotInformation.TrackingMode != Dot.TrackingMode.Pregnancy and pregnancyTracker.IsPregnant and pregnancyTracker.PregnancyIsKnown():
					dotInformation.TrackingMode = Dot.TrackingMode.Pregnancy
				elif dotInformation.TrackingMode != Dot.TrackingMode.Cycle and not pregnancyTracker.IsPregnant:
					dotInformation.TrackingMode = Dot.TrackingMode.Cycle
			else:
				if dotInformation.TrackingMode != Dot.TrackingMode.Cycle:
					dotInformation.TrackingMode = Dot.TrackingMode.Cycle

	# noinspection PyUnusedLocal
	def _TrackerAddedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._HandleTrackerAdded(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _TrackerRemovedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._HandleTrackerRemoved(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _CycleTrackerCycleChangedCallback (self, owner: CycleTracker.CycleTracker, eventArguments: CycleEvents.CycleChangedArguments) -> None:
		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			if dotInformation.TimeSinceCycleStart is None:
				cycleTracker = self.HandlingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]

				currentSimulation = self.HandlingSystem.Simulation  # type: typing.Optional[ReproductionShared.Simulation]

				if currentSimulation is None:
					dotInformation.SetCycleStart(cycleTracker.CurrentCycle.Age)
				else:
					dotInformation.SetCycleStart(cycleTracker.CurrentCycle.Age + currentSimulation.RemainingMinutes - currentSimulation.NonUpdateTicks) # Subtracting the non update ticks because they will be manually simulated for the dot app at the end of the system's simulation

	# noinspection PyUnusedLocal
	def _CycleTrackerCycleCompletedCallback (self, owner: CycleTracker.CycleTracker, eventArguments: CycleEvents.CycleCompletedArguments) -> None:
		if eventArguments.CompletionReason == CycleShared.CompletionReasons.Finished:
			dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

			if dotInformation is not None:
				currentSimulation = self.HandlingSystem.Simulation  # type: typing.Optional[ReproductionShared.Simulation]

				if currentSimulation is None:
					dotInformation.SetCycleStart(0)
				else:
					dotInformation.SetCycleStart(currentSimulation.RemainingMinutes)

	# noinspection PyUnusedLocal
	def _PregnancyTrackerPregnancyStartedCallback (self, owner: PregnancyTracker.PregnancyTracker, eventArguments: CycleEvents.PregnancyStartedArguments) -> None:
		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			if dotInformation.TimeSinceCycleStart is None:
				dotInformation.SetCycleStart(0)

	# noinspection PyUnusedLocal
	def _PregnancyTrackerPregnancyEndedCallback (self, owner: PregnancyTracker.PregnancyTracker, eventArguments: CycleEvents.PregnancyEndedArguments) -> None:
		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			dotInformation.TrackingMode = Dot.TrackingMode.Cycle
			dotInformation.SetCycleStart(0)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	HandlersTypes.RegisterHandlerType(DotHandler.TypeIdentifier, DotHandler)
