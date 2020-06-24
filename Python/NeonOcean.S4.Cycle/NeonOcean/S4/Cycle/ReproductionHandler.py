from __future__ import annotations

import sys
import typing

import alarms
import date_and_time
import indexed_manager
import services
import time_service
import zone
from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, Saving, This
from NeonOcean.S4.Main import Debug, Director, LoadingShared
from NeonOcean.S4.Main.Saving import SectionBranched
from sims import sim_info, sim_info_manager

_lastUpdateTick = None  # type: typing.Optional[int]

_standardUpdateInterval = 15000  # type: int  # About the number of ticks between reproduction update calls.
_standardUpdateAlarm = None  # type: typing.Optional[alarms.AlarmHandle]

_plannedUpdateAlarms = list()  # type: typing.List[alarms.AlarmHandle]

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		_ResetZoneHandling()
		_SetupZoneHandling()

	@classmethod
	def ZoneOnToreDown (cls, *args, **kwargs) -> None:
		_ResetZoneHandling()

# noinspection PyUnusedLocal
def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	Saving.GetSimsSection().RegisterLoadCallback(_SimsSectionLoadCallback)
	Saving.GetSimsSection().RegisterSaveCallback(_SimsSectionSaveCallback)
	Saving.GetSimsSection().RegisterResetCallback(_SimsSectionResetCallback)

	if services.current_zone() is not None:
		_SetupZoneHandling()

# noinspection PyUnusedLocal
def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	Saving.GetSimsSection().UnregisterLoadCallback(_SimsSectionLoadCallback)
	Saving.GetSimsSection().UnregisterSaveCallback(_SimsSectionSaveCallback)
	Saving.GetSimsSection().UnregisterResetCallback(_SimsSectionResetCallback)

	if services.current_zone() is not None:
		_ResetZoneHandling()

def _SetupZoneHandling () -> None:
	global _lastUpdateTick, _standardUpdateAlarm

	timeService = services.time_service()  # type: time_service.TimeService
	_lastUpdateTick = timeService.sim_now.absolute_ticks()

	simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager

	if simInfoManager is not None:
		simInfoManager.register_callback(indexed_manager.CallbackTypes.ON_OBJECT_ADD, _OnSimAddCallback)
		simInfoManager.register_callback(indexed_manager.CallbackTypes.ON_OBJECT_REMOVE, _OnSimRemoveCallback)

	if services.time_service() is not None:
		alarmTimeSpan = date_and_time.TimeSpan(_standardUpdateInterval)
		_standardUpdateAlarm = alarms.add_alarm(sys.modules[__name__], alarmTimeSpan, _StandardUpdateCallback, repeating = True)

def _ResetZoneHandling () -> None:
	global _lastUpdateTick, _standardUpdateAlarm

	_lastUpdateTick = None

	simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager

	if simInfoManager is not None:
		# noinspection PyProtectedMember
		onObjectAddCallbacks = simInfoManager._registered_callbacks.get(indexed_manager.CallbackTypes.ON_OBJECT_ADD, None)

		if onObjectAddCallbacks is not None:
			onObjectAddCallbackIndex = 0
			while onObjectAddCallbackIndex < len(onObjectAddCallbacks):
				onObjectAddCallback = onObjectAddCallbacks[onObjectAddCallbackIndex]

				if onObjectAddCallback == _OnSimAddCallback:
					onObjectAddCallbacks.pop(onObjectAddCallbackIndex)
					continue

				onObjectAddCallbackIndex += 1

		# noinspection PyProtectedMember
		onObjectRemoveCallbacks = simInfoManager._registered_callbacks.get(indexed_manager.CallbackTypes.ON_OBJECT_REMOVE, None)

		if onObjectRemoveCallbacks is not None:
			onObjectRemoveCallbackIndex = 0
			while onObjectRemoveCallbackIndex < len(onObjectRemoveCallbacks):
				onObjectRemoveCallback = onObjectRemoveCallbacks[onObjectRemoveCallbackIndex]

				if onObjectRemoveCallback == _OnSimAddCallback:
					onObjectRemoveCallbacks.pop(onObjectRemoveCallbackIndex)
					continue

				onObjectRemoveCallbackIndex += 1

	if _standardUpdateAlarm is not None:
		_standardUpdateAlarm.cancel()
		_standardUpdateAlarm = None

# noinspection PyUnusedLocal
def _StandardUpdateCallback (alarmHandle: alarms.AlarmHandle) -> None:
	if not This.Mod.IsLoaded():
		return

	reportLockIdentifier = __name__ + ":UpdateCallback"  # type: str

	try:
		Reproduction.UpdateSystems()  # TODO log the time taken?

		updateTicks = Reproduction.GetUpdateTicks(_standardUpdateInterval)  # type: typing.Dict[int, typing.List[ReproductionShared.ReproductiveSystem]]

		for plannedTick, plannedSystems in updateTicks.items():  # type: int, typing.List[ReproductionShared.ReproductiveSystem]
			if plannedTick >= _standardUpdateInterval:
				continue

			alarmTimeSpan = date_and_time.TimeSpan(plannedTick)
			plannedUpdateAlarm = alarms.add_alarm(sys.modules[__name__], alarmTimeSpan, _CreatePlannedUpdateCallback(plannedSystems))

			_plannedUpdateAlarms.append(plannedUpdateAlarm)
	except:
		Debug.Log("Reproduction standard update callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = reportLockIdentifier)
	else:
		Debug.Unlock(reportLockIdentifier)

def _CreatePlannedUpdateCallback (plannedSystems: typing.List[ReproductionShared.ReproductiveSystem]) -> typing.Callable:
	# noinspection PyUnusedLocal
	def _plannedUpdateCallback (alarmHandle: alarms.AlarmHandle) -> None:
		if not This.Mod.IsLoaded():
			return

		reportLockIdentifier = __name__ + ":UpdateCallback"  # type: str

		try:
			Reproduction.UpdateSystems(plannedSystems)  # TODO log the time taken?
		except:
			Debug.Log("Reproduction planned update callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = reportLockIdentifier)
		else:
			Debug.Unlock(reportLockIdentifier)

		try:
			_plannedUpdateAlarms.remove(alarmHandle)
		except ValueError:
			pass

	return _plannedUpdateCallback

def _OnSimAddCallback (simInfo: sim_info.SimInfo) -> None:
	if not This.Mod.IsLoaded():
		return

	try:
		if Reproduction.SimHasSystem(simInfo):
			Debug.Log("Went to create a reproductive system for a sim being added, but one already exists.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

		simSystem = Reproduction.InitiateReproductiveSystem(simInfo)
		simsSection = Saving.GetSimsSection()  # type: SectionBranched.SectionBranched

		if Saving.GetSimsSection().SavingObject.Loaded:
			simSystem.Load(simsSection)
	except:
		Debug.Log("Reproduction on sim add callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _OnSimRemoveCallback (simInfo: sim_info.SimInfo) -> None:
	if not This.Mod.IsLoaded():
		return

	try:
		Reproduction.RemoveSimSystem(simInfo)
	except:
		Debug.Log("Reproduction on sim remove callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _SimsSectionLoadCallback (simsSection: SectionBranched.SectionBranched) -> bool:
	return Reproduction.LoadAllSystems(simsSection = simsSection)

def _SimsSectionSaveCallback (simsSection: SectionBranched.SectionBranched) -> bool:
	return Reproduction.SaveAllSystems(simsSection = simsSection)

# noinspection PyUnusedLocal
def _SimsSectionResetCallback (simsSection: SectionBranched.SectionBranched) -> bool:
	return Reproduction.ResetSystems()
