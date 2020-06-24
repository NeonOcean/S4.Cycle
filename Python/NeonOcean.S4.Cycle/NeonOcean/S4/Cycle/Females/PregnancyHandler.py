from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, Settings
from NeonOcean.S4.Cycle.Settings import Base as SettingsBase
from NeonOcean.S4.Cycle.Females import PregnancyTracker, Shared as FemalesShared
from NeonOcean.S4.Main import Director
from NeonOcean.S4.Main.Tools import Patcher
from sims.pregnancy import pregnancy_tracker
import zone

class _AnnouncerPreemptive (Director.Announcer):
	_priority = 100

	Preemptive = True

	@classmethod
	def ZoneSave(cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		for reproductiveSystem in Reproduction.GetAllSystems():
			pregnancyTracker = reproductiveSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

			if pregnancyTracker is not None:
				pregnancyTracker.ResetPregnancyVisualsIfAppropriate()

class _Announcer(Director.Announcer):
	_priority = -100

	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		for reproductiveSystem in Reproduction.GetAllSystems():
			systemPregnancyTracker = reproductiveSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

			if systemPregnancyTracker is not None:
				systemPregnancyTracker.SetPregnancyVisualsIfAppropriate()

def _OnStart (cause) -> None:
	if cause:
		pass

	Patcher.Patch(pregnancy_tracker.PregnancyTracker, "start_pregnancy", _StartPregnancy)
	Patcher.Patch(pregnancy_tracker.PregnancyTracker, "clear_pregnancy", _ClearPregnancy)

	Settings.RegisterOnUpdateCallback(_SettingsOnUpdateCallback)

def _OnStop (cause) -> None:
	if cause:
		pass

	Settings.UnregisterOnUpdateCallback(_SettingsOnUpdateCallback)

# noinspection PyUnusedLocal
def _StartPregnancy (self: pregnancy_tracker.PregnancyTracker, *args, **kwargs) -> None:
	targetSimSystem = Reproduction.GetSimSystem(self._sim_info)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]
	pregnancyTracker = targetSimSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

	if pregnancyTracker is None:
		return

	pregnancyTracker.NotifyPregnancyStarted()

# noinspection PyUnusedLocal
def _ClearPregnancy (self: pregnancy_tracker.PregnancyTracker, *args, **kwargs) -> None:
	targetSimSystem = Reproduction.GetSimSystem(self._sim_info)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]
	pregnancyTracker = targetSimSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

	if pregnancyTracker is None:
		return

	pregnancyTracker.NotifyPregnancyEnded()

# noinspection PyUnusedLocal
def _SettingsOnUpdateCallback (owner, eventArguments: SettingsBase.UpdateEventArguments) -> None:
	if eventArguments.Changed(Settings.PregnancySpeed.Key):
		for simReproductiveSystem in Reproduction.GetAllSystems(automaticallyUpdate = False):
			pregnancyTracker = simReproductiveSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

			if pregnancyTracker is None:
				continue

			simReproductiveSystem.Update()


