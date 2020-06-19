from __future__ import annotations

from NeonOcean.S4.Cycle import Biology, ReproductionShared
from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info, sim_info_types

SpermProductionTrackerIdentifier = "SpermProductionTracker"  # type: str

def ShouldHaveMaleTrackers (simInfo: sim_info.SimInfo) -> bool:
	"""
	Get whether or not this sim should have male reproductive trackers.
	:param simInfo: The target sim's info.
	:type simInfo: sim_info.SimInfo
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	if simInfo.lod == sim_info.SimInfoLODLevel.MINIMUM:
		return False

	if simInfo.species != sim_info_types.Species.HUMAN:
		return False

	return Biology.SimCanImpregnate(simInfo)

def GetSpermProductionTrackerReproductiveTimeMultiplier () -> float:
	return ReproductionShared.GetGeneralReproductiveTimeMultiplier()