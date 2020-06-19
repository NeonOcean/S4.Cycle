from __future__ import annotations

import enum_lib
import typing
from NeonOcean.S4.Cycle import Biology, Settings
from NeonOcean.S4.Cycle import ReproductionShared
from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info, sim_info_types

CycleTrackerIdentifier = "CycleTracker"  # type: str
OvumTrackerIdentifier = "OvumTracker"  # type: str
PregnancyTrackerIdentifier = "PregnancyTracker"  # type: str
SpermTrackerIdentifier = "SpermTracker"  # type: str

OvumQuickModeMinimumTimeMultiplier = 0.2  # type: float
SpermQuickModeMinimumTimeMultiplier = 0.2  # type: float

class PregnancyTrimester(enum_lib.IntEnum):
	First = 1  # type: PregnancyTrimester
	Second = 2  # type: PregnancyTrimester
	Third = 3  # type: PregnancyTrimester

def ShouldHaveFemaleTrackers (simInfo: sim_info.SimInfo) -> bool:
	"""
	Get whether or not this sim should have female reproductive trackers.
	:param simInfo: The target sim's info.
	:type simInfo: sim_info.SimInfo
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	if simInfo.lod == sim_info.SimInfoLODLevel.MINIMUM:
		return False

	if simInfo.species != sim_info_types.Species.HUMAN:
		return False

	return Biology.SimCanBeImpregnated(simInfo)

def GetFemaleTrackerIdentifiers () -> typing.Set[str]:
	return {
		CycleTrackerIdentifier,
		OvumTrackerIdentifier,
		PregnancyTrackerIdentifier,
		SpermTrackerIdentifier
	}

def GetCycleTrackerReproductiveTimeMultiplier () -> float:
	return ReproductionShared.GetGeneralReproductiveTimeMultiplier()

def GetOvumTrackerReproductiveTimeMultiplier () -> float:
	multiplier = ReproductionShared.GetGeneralReproductiveTimeMultiplier()

	if multiplier < OvumQuickModeMinimumTimeMultiplier:
		multiplier = OvumQuickModeMinimumTimeMultiplier

	return multiplier

def GetPregnancyTrackerReproductiveTimeMultiplier () -> float:
	return Settings.PregnancySpeed.Get()

def GetSpermTrackerReproductiveTimeMultiplier () -> float:
	multiplier = ReproductionShared.GetGeneralReproductiveTimeMultiplier()

	if multiplier < SpermQuickModeMinimumTimeMultiplier:
		multiplier = SpermQuickModeMinimumTimeMultiplier

	return multiplier