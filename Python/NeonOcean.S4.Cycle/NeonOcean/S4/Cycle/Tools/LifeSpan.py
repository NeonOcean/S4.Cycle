from __future__ import annotations

import typing

from sims import sim_info_types
from NeonOcean.S4.Main.Tools import Exceptions
from sims.aging import aging_tuning, aging_data, aging_transition
from sims4.tuning import tunable

def GetAverageLifeSpan (species: sim_info_types.Species) -> typing.Union[float, int]:
	"""
	Get the average life span of any member of this species.
	:param species: The species to get the average life span of.
	:type species: sim_info_types.Species
	:return: The average life span of any member of this species. This value will be unmodified by the game's lifespan settings, as if
	it was set to "normal".
	:rtype: typing.Union[float, int]
	"""

	if not isinstance(species, sim_info_types.Species):
		raise Exceptions.IncorrectTypeException(species, "species", (sim_info_types.Species, ))

	speciesAgingData = aging_tuning.AgingTuning.get_aging_data(species)  # type: aging_data.AgingData

	# noinspection PyUnresolvedReferences
	speciesAges = speciesAgingData.ages  # type: typing.Dict[sim_info_types.Age, aging_transition.AgingTransition]
	speciesLifeSpan = 0  # type: typing.Union[float, int]

	for speciesAge in speciesAges.values():  # type: aging_transition.AgingTransition
		# noinspection PyUnresolvedReferences, PyProtectedMember
		ageDurationInterval = speciesAge.transition._age_duration  # type: tunable.TunedInterval
		speciesLifeSpan += (ageDurationInterval.lower_bound + ageDurationInterval.upper_bound) / 2

	return speciesLifeSpan