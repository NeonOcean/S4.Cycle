from __future__ import annotations

import typing

import services
import zone
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Debug, Director
from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info
from sims4 import resources
from statistics import statistic

LastSimIDStatisticID = 9391266768967019788  # type: int

class _AnnouncerPreemptive(Director.Announcer):
	@classmethod
	def ZoneSave (cls, zoneReference: zone.Zone, saveSlotData: typing.Optional[typing.Any] = None) -> None:
		for simInfo in services.sim_info_manager().get_all():
			try:
				UpdateLastSimID(simInfo)
			except:
				Debug.Log("Failed to update the last sim id for a sim with the id '%s'." % simInfo.id, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def GetLastSimID (targetSimInfo: sim_info.SimInfo) -> typing.Optional[int]:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	lastSimIDStatisticType = services.get_instance_manager(resources.Types.STATISTIC).get(LastSimIDStatisticID, None)  # type: typing.Optional[typing.Type[statistic.Statistic]]

	if lastSimIDStatisticType is None:
		Debug.Log("Could not find the last sim id statistic type.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":MissingLastSimIDStatisticType")
		return None

	lastSimIDStatistic = targetSimInfo.get_statistic(lastSimIDStatisticType, add = True)  # type: statistic.Statistic

	if lastSimIDStatistic is None:
		Debug.Log("Could not retrieve a sim's last sim id statistic", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":MissingLastSimIDStatistic")
		return None

	lastSimID = lastSimIDStatistic.get_value()  # type: int

	if lastSimID == 0:
		return None
	else:
		return lastSimID

def UpdateLastSimID (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	lastSimIDStatisticType = services.get_instance_manager(resources.Types.STATISTIC).get(LastSimIDStatisticID, None)  # type: typing.Optional[typing.Type[statistic.Statistic]]

	if lastSimIDStatisticType is None:
		Debug.Log("Could not find the last sim id statistic type.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":MissingLastSimIDStatisticType")
		return

	lastSimIDStatistic = targetSimInfo.get_statistic(lastSimIDStatisticType, add = True)  # type: statistic.Statistic

	if lastSimIDStatistic is None:
		Debug.Log("Could not retrieve a sim's last sim id statistic", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":MissingLastSimIDStatistic")
		return

	lastSimIDStatistic.set_value(targetSimInfo.id)
