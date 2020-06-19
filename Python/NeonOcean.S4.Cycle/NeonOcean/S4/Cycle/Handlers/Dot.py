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

	def _OnAdded (self) -> None:
		cycleTracker = self.HandlingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]
		pregnancyTracker = self.HandlingSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

		if cycleTracker is None:
			return

		cycleTracker.CycleChangedEvent += self._CycleTrackerCycleChangedCallback
		cycleTracker.CycleCompletedEvent += self._CycleTrackerCycleCompletedCallback

		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			if dotInformation.TimeSinceCycleStart is None:
				if cycleTracker.TimeSinceLastCycle is not None:
					dotInformation.TimeSinceCycleStart = cycleTracker.TimeSinceLastCycle
				else:
					if cycleTracker.CurrentCycle is not None:
						dotInformation.TimeSinceCycleStart = cycleTracker.CurrentCycle.Age

		if pregnancyTracker is not None:
			pregnancyTracker.PregnancyStartedEvent += self._PregnancyTrackerPregnancyStartedCallback
			pregnancyTracker.PregnancyEndedEvent += self._PregnancyTrackerPregnancyEndedCallback

	def _OnRemoving(self) -> None:
		cycleTracker = self.HandlingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]
		pregnancyTracker = self.HandlingSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

		if cycleTracker is not None:
			cycleTracker.CycleChangedEvent -= self._CycleTrackerCycleChangedCallback
			cycleTracker.CycleCompletedEvent -= self._CycleTrackerCycleCompletedCallback

		if pregnancyTracker is not None:
			pregnancyTracker.PregnancyStartedEvent -= self._PregnancyTrackerPregnancyStartedCallback
			pregnancyTracker.PregnancyEndedEvent -= self._PregnancyTrackerPregnancyEndedCallback

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		if not simulation.LastTickStep:
			return

		cycleTracker = self.HandlingSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]
		pregnancyTracker = self.HandlingSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

		if cycleTracker is None:
			Dot.ClearDotInformation(self.HandlingSystem.SimInfo)
			return

		dotInformation = Dot.GetDotInformation(self.HandlingSystem.SimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is not None:
			if simulation.NonUpdateTicks > 0:
				dotInformation.Simulate(simulation.NonUpdateTicks)

			if pregnancyTracker is not None:
				if dotInformation.TrackingMode != Dot.TrackingMode.Pregnancy and pregnancyTracker.IsPregnant and pregnancyTracker.PregnancyIsKnown():
					dotInformation.TrackingMode = Dot.TrackingMode.Pregnancy

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
