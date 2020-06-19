from __future__ import annotations

from sims import sim_info, sim_info_types
from NeonOcean.S4.Cycle.GuideGroups import Base as GuideGroupsBase
from NeonOcean.S4.Main import LoadingShared

def HumanGuideGroupMatcher (simInfo: sim_info.SimInfo) -> bool:
	if simInfo.species == sim_info_types.Species.HUMAN:
		return True

	return False

def _OnStartLate (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	GuideGroupsBase.RegisterGuideGroup(HumanGuideGroup)

HumanGuideGroup = GuideGroupsBase.GuideGroup(HumanGuideGroupMatcher)  # type: GuideGroupsBase.GuideGroup