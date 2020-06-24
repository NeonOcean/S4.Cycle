from __future__ import annotations

import typing

import services
from NeonOcean.S4.Cycle import References, This
from NeonOcean.S4.Main import Debug, Director
from event_testing import test_base
from sims import sim_info_tests
from sims4 import resources
from sims4.tuning import instance_manager

class _Announcer(Director.Announcer):
	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager) -> None:
		if instanceManager.TYPE == resources.Types.BUFF:
			_PatchBuffs()
			return

def _PatchBuffs () -> None:
	_PatchHumanPregnancyBuff(References.PregnancyNotShowingBuffID)
	_PatchHumanPregnancyBuff(References.PregnancyFirstTrimesterBuffID)
	_PatchHumanPregnancyBuff(References.PregnancySecondTrimesterBuffID)
	_PatchHumanPregnancyBuff(References.PregnancyThirdTrimesterBuffID)
	_PatchHumanPregnancyBuff(References.PregnancyInLaborBuffID)

def _PatchHumanPregnancyBuff (buffID: int) -> None:
	buffInstanceManager = services.get_instance_manager(resources.Types.BUFF)  # type: instance_manager.InstanceManager

	pregnancyBuff = buffInstanceManager.get(buffID)

	if pregnancyBuff is None:
		Debug.Log("Went to patch a human pregnancy buff with the id '%s' but could not find it." % buffID, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
		return

	# noinspection PyProtectedMember
	buffAddTestSet = pregnancyBuff._add_test_set  # type: typing.Optional[typing.Tuple[typing.Tuple[test_base.BaseTest, ...], ...]]

	if buffAddTestSet is None:
		return

	for buffAddTestGroup in buffAddTestSet:  # type: typing.Tuple[test_base.BaseTest, ...]
		for buffAddTest in buffAddTestGroup:  # type: test_base.BaseTest
			if not isinstance(buffAddTest, sim_info_tests.SimInfoTest):
				continue

			buffAddTest.ages = None  # Makes age irrelevant. If they are pregnant, they get the buffs.
