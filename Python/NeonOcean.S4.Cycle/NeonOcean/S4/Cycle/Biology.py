from __future__ import annotations

from NeonOcean.S4.Main.Tools import Exceptions
from sims import sim_info

CanBeImpregnatedTraitID = 136875  # type: int
CanNotBeImpregnatedTraitID = 137716  # type: int

CanImpregnateTraitID = 136874  # type: int
CanNotImpregnateTraitID = 137717  # type: int

def SimCanBeImpregnated (simInfo: sim_info.SimInfo) -> bool:
	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	hasAllowTrait = False  # type: bool
	hasDisallowTrait = False  # type: bool

	for simTrait in simInfo.get_traits():
		if hasattr(simTrait, "guid64"):

			if simTrait.guid64 == CanBeImpregnatedTraitID:
				hasAllowTrait = True

			if simTrait.guid64 == CanNotBeImpregnatedTraitID:
				hasDisallowTrait = True

	if not hasAllowTrait and not hasDisallowTrait:
		# noinspection PyPropertyAccess
		return simInfo.gender == sim_info.Gender.FEMALE

	if hasAllowTrait:
		return True
	else:
		return False

def SimCanImpregnate (simInfo: sim_info.SimInfo) -> bool:
	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	hasAllowTrait = False  # type: bool
	hasDisallowTrait = False  # type: bool

	for simTrait in simInfo.get_traits():
		if hasattr(simTrait, "guid64"):

			if simTrait.guid64 == CanImpregnateTraitID:
				hasAllowTrait = True

			if simTrait.guid64 == CanNotImpregnateTraitID:
				hasDisallowTrait = True

	if not hasAllowTrait and not hasDisallowTrait:
		# noinspection PyPropertyAccess
		return simInfo.gender == sim_info.Gender.MALE

	if hasAllowTrait:
		return True
	else:
		return False
