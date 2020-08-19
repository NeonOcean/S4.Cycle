from __future__ import annotations

import typing
import weakref

import zone
from NeonOcean.S4.Cycle import Guides as CycleGuides, ReproductionShared, Settings, This
from NeonOcean.S4.Cycle.Settings import Base as SettingsBase
from NeonOcean.S4.Main import Debug, Director
from NeonOcean.S4.Main.Tools import Patcher, Python
from objects import script_object
from sims import sim_info, sim_info_types
from sims.pregnancy import pregnancy_tracker as GamePregnancyTracker
from sims4 import resources
from sims4.tuning import instance_manager
from statistics import base_statistic, base_statistic_tracker, commodity

_pregnancyStatistics = list()  # type: typing.List[weakref.ReferenceType]
_handlingPregnancyStatistics = list()  # type: typing.List[weakref.ReferenceType]

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
		_ApplySettingsToAllPregnancyStatistics()

	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		_ApplySettingsToAllPregnancyStatistics()

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

def _ApplySettingsPregnancyStatistic (pregnancyStatistic: base_statistic.BaseStatistic) -> None:
	if Settings.HandlePregnancySpeed.Get():
		pregnancyRate = _GetPregnancyRate()  # type: float
		_ApplyPregnancyStatisticRate(pregnancyStatistic, pregnancyRate)
		_handlingPregnancyStatistics.append(weakref.ref(pregnancyStatistic))
	else:
		handlingReferenceIndex = 0
		while handlingReferenceIndex < len(_handlingPregnancyStatistics):
			handlingStatisticReference = _handlingPregnancyStatistics[handlingReferenceIndex]  # type: weakref.ref

			handlingStatistic = handlingStatisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

			if handlingStatistic == pregnancyStatistic:
				_ResetPregnancyStatistic(pregnancyStatistic)
				_handlingPregnancyStatistics.pop(handlingReferenceIndex)
				continue

			handlingReferenceIndex += 1

def _ApplySettingsToAllPregnancyStatistics () -> None:
	for statisticReference in _pregnancyStatistics:  # type: weakref.ref
		statistic = statisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

		if statistic is not None:
			_ApplySettingsPregnancyStatistic(statistic)

def _ResetPregnancyStatistic (pregnancyStatistic: base_statistic.BaseStatistic) -> None:
	pregnancyStatisticTracker = pregnancyStatistic.tracker  # type: typing.Optional[base_statistic_tracker.BaseStatisticTracker]

	if pregnancyStatisticTracker is None:
		Debug.Log("Went to reset a pregnancy statistic, but it has no tracker. We can't get to the original pregnancy rate.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		_ApplyPregnancyStatisticRate(pregnancyStatistic, None)
		return

	pregnancyStatisticOwner = pregnancyStatisticTracker.owner  # type: typing.Optional[script_object.ScriptObject]

	if pregnancyStatisticOwner is None:
		Debug.Log("Went to reset a pregnancy statistic, but its tracker has no owner. We can't get to the original pregnancy rate.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		_ApplyPregnancyStatisticRate(pregnancyStatistic, None)
		return

	if not isinstance(pregnancyStatisticOwner, sim_info.SimInfo):
		Debug.Log("Went to reset a pregnancy statistic, but its owner is not a sim. We can't get to the original pregnancy rate.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		_ApplyPregnancyStatisticRate(pregnancyStatistic, None)
		return

	ownerPregnancyTracker = pregnancyStatisticOwner.pregnancy_tracker  # type: GamePregnancyTracker.PregnancyTracker

	pregnancyRate = ownerPregnancyTracker.PREGNANCY_RATE

	_ApplyPregnancyStatisticRate(pregnancyStatistic, pregnancyRate)

def _ResetHandlingPregnancyStatistics () -> None:
	global _handlingPregnancyStatistics

	if len(_handlingPregnancyStatistics) != 0:
		for handlingStatisticReference in _handlingPregnancyStatistics:  # type: weakref.ref
			handlingStatistic = handlingStatisticReference()  # type: typing.Optional[base_statistic.BaseStatistic]

			if handlingStatistic is not None:
				_ResetPregnancyStatistic(handlingStatistic)

		_handlingPregnancyStatistics = list()

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

	_pregnancyStatistics.append(weakref.ref(self))

def _CreatePregnancyCommodityWatcherWrapper (commodityTracker: base_statistic_tracker.BaseStatisticTracker) -> typing.Callable:
	# Without this, we only get the statistic type, old value, and new value. We would have no way of figuring out which instance of the statistic actually changed or for what object in changed for. I'm not sure why it isn't this way by default.

	def _pregnancyCommodityWatcherWrapper (statisticType: typing.Type[base_statistic.BaseStatistic], oldValue: float, newValue: float) -> None:
		_PregnancyCommodityWatcher(commodityTracker, statisticType, oldValue, newValue)

	return _pregnancyCommodityWatcherWrapper

# noinspection PyUnusedLocal
def _OnStart (cause) -> None:
	Settings.RegisterOnUpdateCallback(_SettingsOnUpdatedCallback)

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
