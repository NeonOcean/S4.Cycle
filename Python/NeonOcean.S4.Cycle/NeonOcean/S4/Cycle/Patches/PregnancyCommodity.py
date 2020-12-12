from __future__ import annotations

import typing
import weakref

import zone
from NeonOcean.S4.Cycle import Guides as CycleGuides, ReproductionShared, Settings, This
from NeonOcean.S4.Cycle.Settings import Base as SettingsBase
from NeonOcean.S4.Main import Debug, Director, LoadingShared
from NeonOcean.S4.Main.Tools import Patcher, Python
from objects import script_object
from sims import sim_info, sim_info_types
from sims.pregnancy import pregnancy_tracker as GamePregnancyTracker
from sims4 import resources
from sims4.tuning import instance_manager
from statistics import base_statistic, base_statistic_tracker, commodity

_pregnancyStatistics = set()  # type: typing.Set[weakref.ReferenceType]
_handlingPregnancyStatistics = set()  # type: typing.Set[weakref.ReferenceType]

class _AnnouncerPreemptive(Director.Announcer):
	Host = This.Mod
	Preemptive = True

	_priority = 100

	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		_ResetHandlingPregnancyStatistics()

class _PatchingAnnouncer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager) -> None:
		if instanceManager.TYPE == resources.Types.STATISTIC:
			_PatchStatistics()
			return

class _Announcer(Director.Announcer):
	Host = This.Mod

	_priority = -100

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		_ClearDeadPregnancyStatisticReferences()
		_ApplySettingsToAllPregnancyStatistics()

	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		_ApplySettingsToAllPregnancyStatistics()

	@classmethod
	def OnLoadingScreenAnimationFinished(cls, zoneReference: zone.Zone) -> None:
		_FixOldCyclePregnancyStatisticBug()


def _GetPregnancyRate () -> float:
	reproductiveTimeMultiplier = Settings.PregnancySpeed.Get()  # type: float

	pregnancyGuide = CycleGuides.HumanPregnancyGuide.Guide  # type: CycleGuides.PregnancyGuide

	pregnancyTime = pregnancyGuide.PregnancyTime  # type: float
	pregnancyGameTime = ReproductionShared.ReproductiveMinutesToGameMinutes(pregnancyTime, reproductiveTimeMultiplier)  # type: float

	if pregnancyGameTime != 0:
		pregnancyRate = 100 / pregnancyGameTime  # type: float
	else:
		Debug.Log("Calculated a pregnancy game time to be 0 minutes, this is probably not intentional.",
				  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 1)

		pregnancyRate = 0

	return pregnancyRate

def _GetPregnancyStatisticOwner (pregnancyStatistic: base_statistic.BaseStatistic) -> typing.Optional[sim_info.SimInfo]:
	pregnancyStatisticTracker = pregnancyStatistic.tracker  # type: typing.Optional[base_statistic_tracker.BaseStatisticTracker]

	if pregnancyStatisticTracker is None:
		Debug.Log("Found a pregnancy statistic with no tracker.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		return None

	pregnancyStatisticOwner = pregnancyStatisticTracker.owner  # type: typing.Optional[script_object.ScriptObject]

	if pregnancyStatisticOwner is None:
		Debug.Log("Found a pregnancy statistic with a tracker but no owner.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		return

	if not isinstance(pregnancyStatisticOwner, sim_info.SimInfo):
		Debug.Log("Found a pregnancy statistic that has an object other than a sim as its owner.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		return

	return pregnancyStatisticOwner

def _ApplySettingsPregnancyStatistic (pregnancyStatistic: base_statistic.BaseStatistic) -> None:
	if not Settings.HandlePregnancySpeed.Get():
		_StopHandlingPregnancyStatistic(pregnancyStatistic)
		return

	pregnancyStatisticOwner = _GetPregnancyStatisticOwner(pregnancyStatistic)  # type: typing.Optional[sim_info.SimInfo]

	if pregnancyStatisticOwner is None:
		return

	ownerPregnancyTracker = pregnancyStatisticOwner.pregnancy_tracker  # type: GamePregnancyTracker.PregnancyTracker

	if not ownerPregnancyTracker.is_pregnant:
		_StopHandlingPregnancyStatistic(pregnancyStatistic)
		return

	pregnancyRate = _GetPregnancyRate()  # type: float
	_ApplyPregnancyStatisticRate(pregnancyStatistic, pregnancyRate)
	_handlingPregnancyStatistics.add(weakref.ref(pregnancyStatistic))  # Using a set prevents one stat from being added more than once, even though they are saved as weak refs.
	return

def _ApplySettingsToAllPregnancyStatistics () -> None:
	for statisticReference in _pregnancyStatistics:  # type: weakref.ref
		statistic = statisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

		if statistic is not None:
			_ApplySettingsPregnancyStatistic(statistic)

def _StopHandlingPregnancyStatistic (pregnancyStatistic: base_statistic.BaseStatistic) -> None:
	for handlingStatisticReference in _handlingPregnancyStatistics:  # type: weakref.ref
		handlingStatistic = handlingStatisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

		if handlingStatistic == pregnancyStatistic:
			_handlingPregnancyStatistics.remove(handlingStatisticReference)
			break

	_ResetPregnancyStatistic(pregnancyStatistic)

def _ResetPregnancyStatistic (pregnancyStatistic: base_statistic.BaseStatistic) -> None:
	pregnancyStatisticOwner = _GetPregnancyStatisticOwner(pregnancyStatistic)  # type: typing.Optional[sim_info.SimInfo]

	if pregnancyStatisticOwner is None:
		return

	ownerPregnancyTracker = pregnancyStatisticOwner.pregnancy_tracker  # type: GamePregnancyTracker.PregnancyTracker

	if ownerPregnancyTracker.is_pregnant:
		pregnancyRate = ownerPregnancyTracker.PREGNANCY_RATE
		_ApplyPregnancyStatisticRate(pregnancyStatistic, pregnancyRate)
	else:
		_ApplyPregnancyStatisticRate(pregnancyStatistic, None)

def _ResetHandlingPregnancyStatistics () -> None:
	global _handlingPregnancyStatistics

	for handlingStatisticReference in _handlingPregnancyStatistics:  # type: weakref.ref
		handlingStatistic = handlingStatisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

		if handlingStatistic is not None:
			_ResetPregnancyStatistic(handlingStatistic)

	_handlingPregnancyStatistics = set()

def _ClearDeadPregnancyStatisticReferences () -> None:
	global _pregnancyStatistics

	alivePregnancyStatistics = set()

	for pregnancyStatisticReference in _pregnancyStatistics:  # type: weakref.ref
		pregnancyStatistic = pregnancyStatisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

		if pregnancyStatistic is not None:
			alivePregnancyStatistics.add(pregnancyStatisticReference)

	_pregnancyStatistics = alivePregnancyStatistics

# noinspection PyProtectedMember
def _ApplyPregnancyStatisticRate (pregnancyStatistic: base_statistic.BaseStatistic, pregnancyRate: typing.Optional[float]) -> None:
	if pregnancyRate is not None:
		if pregnancyStatistic._statistic_modifier != pregnancyRate:
			pregnancyStatistic._statistic_modifier = pregnancyRate
			pregnancyStatistic._statistic_modifiers = [pregnancyRate]
	else:
		if pregnancyStatistic._statistic_modifier != 0:
			pregnancyStatistic._statistic_modifier = 0
			pregnancyStatistic._statistic_modifiers = None

		# noinspection PyProtectedMember
		pregnancyStatistic._on_statistic_modifier_changed(notify_watcher = False)

def _FixOldCyclePregnancyStatisticBug () -> None:
	"""
	This makes sure a bug from an older version of this mod isn't still affecting someone's game.
	"""

	for pregnancyStatisticReference in _pregnancyStatistics:  # type: weakref.ref
		pregnancyStatistic = pregnancyStatisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

		if pregnancyStatistic is not None:
			pregnancyStatisticOwner = _GetPregnancyStatisticOwner(pregnancyStatistic)  # type: typing.Optional[sim_info.SimInfo]

			if pregnancyStatisticOwner is None:
				continue

			if not pregnancyStatisticOwner.is_pregnant:
				pregnancyStatistic.set_value(0)

def _PatchStatistics () -> None:
	_PatchPregnancyCommodity()

def _PatchPregnancyCommodity () -> None:
	pregnancyCommodity = GamePregnancyTracker.PregnancyTracker.PREGNANCY_COMMODITY_MAP.get(sim_info_types.Species.HUMAN, None)  # type: typing.Optional[typing.Type[commodity.Commodity]]

	if pregnancyCommodity is None:
		Debug.Log("Went to patch the human pregnancy commodity but could not find it.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
		return

	Patcher.Patch(pregnancyCommodity, "__init__", _PregnancyCommodityInit, patchType = Patcher.PatchTypes.After)

# noinspection PyUnusedLocal
def _PregnancyCommodityInit (self: commodity.Commodity, *args, **kwargs) -> None:
	if self.tracker is not None:
		self.tracker.add_watcher(_CreatePregnancyCommodityWatcherWrapper(self.tracker))

	_pregnancyStatistics.add(weakref.ref(self))

def _CreatePregnancyCommodityWatcherWrapper (commodityTracker: base_statistic_tracker.BaseStatisticTracker) -> typing.Callable:
	# Without this, we only get the statistic type, old value, and new value. We would have no way of figuring out which instance of the statistic actually changed or for what object in changed for. I'm not sure why it isn't this way by default.

	def _pregnancyCommodityWatcherWrapper (statisticType: typing.Type[base_statistic.BaseStatistic], oldValue: float, newValue: float) -> None:
		_PregnancyCommodityWatcher(commodityTracker, statisticType, oldValue, newValue)

	return _pregnancyCommodityWatcherWrapper

# noinspection PyUnusedLocal
def _OnStart (cause) -> None:
	Settings.RegisterOnUpdateCallback(_SettingsOnUpdatedCallback)

	if cause != LoadingShared.LoadingCauses.Reloading:
		Patcher.Patch(GamePregnancyTracker.PregnancyTracker, "clear_pregnancy", _GamePregnancyTrackerClearPregnancyPatch)

# noinspection PyUnusedLocal
def _OnStop (cause) -> None:
	Settings.UnregisterOnUpdateCallback(_SettingsOnUpdatedCallback)

def _PregnancyCommodityWatcher (statisticTracker: base_statistic_tracker.BaseStatisticTracker, statisticType: typing.Type[base_statistic.BaseStatistic], oldValue: float, newValue: float) -> None:
	try:
		if oldValue != newValue:
			# We only care about statistic modifier changes here, when those change the old value will always equal the new value.
			return

		if not isinstance(statisticTracker.owner, sim_info.SimInfo):
			return

		if not statisticTracker.owner.is_pregnant:
			return

		if statisticType is not GamePregnancyTracker.PregnancyTracker.PREGNANCY_COMMODITY_MAP.get(sim_info_types.Species.HUMAN, None):
			return

		statistic = statisticTracker.get_statistic(statisticType, add = True)  # type: base_statistic.BaseStatistic
		_ApplySettingsPregnancyStatistic(statistic)
	except:
		Debug.Log("Failed to handle statistic change.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

# noinspection PyUnusedLocal
def _SettingsOnUpdatedCallback (settingsModule, eventArguments: SettingsBase.UpdateEventArguments) -> None:
	global _handlingPregnancyStatistics

	_ApplySettingsToAllPregnancyStatistics()

def _GamePregnancyTrackerClearPregnancyPatch (self: GamePregnancyTracker.PregnancyTracker) -> None:
	simPregnancyStatisticType = self.PREGNANCY_COMMODITY_MAP.get(sim_info_types.Species.HUMAN, None)  # type: typing.Type[base_statistic.BaseStatistic]
	simPregnancyStatistic = self._sim_info.get_statistic(simPregnancyStatisticType)  # type: base_statistic.BaseStatistic

	_StopHandlingPregnancyStatistic(simPregnancyStatistic)