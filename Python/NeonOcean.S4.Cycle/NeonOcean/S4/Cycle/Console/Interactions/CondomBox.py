import random
import typing

import services
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.Mods import WickedWhims
from NeonOcean.S4.Main import Debug, LoadingShared
from objects import script_object, system
from server_commands import argument_helpers
from sims import sim, sim_info
from sims4 import commands, resources
from statistics import statistic

AddUnpackedWickedWhimsCondomsCommand: Command.ConsoleCommand

WickedWhimsCondomDefinitionIDs = [
	11033454205624062315,
	11033454205624062316,
	11033454205624062317,
	11033454205624062318,
	11033454205624062319,
	11033454205624062320,
	11033454205624062321
]  # type: typing.List[int]

CondomBoxCountStatisticID = 6354205262159876328  # type: int

def _Setup () -> None:
	global AddUnpackedWickedWhimsCondomsCommand

	commandPrefix = This.Mod.Namespace.lower() + ".condom_box"  # type: str

	AddUnpackedWickedWhimsCondomsCommand = Command.ConsoleCommand(_AddUnpackedWickedWhimsCondoms, commandPrefix + ".add_unpacked_wicked_whims_condoms")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	AddUnpackedWickedWhimsCondomsCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	AddUnpackedWickedWhimsCondomsCommand.UnregisterCommand()

def _AddUnpackedWickedWhimsCondoms (targetSimHandler: argument_helpers.RequiredTargetParam, unpackedObject: argument_helpers.RequiredTargetParam, _connection: int = None) -> None:
	try:
		if not WickedWhims.ModInstalled():
			raise Exception("WickedWhims is not installed.")

		if len(WickedWhimsCondomDefinitionIDs) == 0:
			raise Exception("Cannot add WickedWhims condoms while the condom definitions list is empty.")

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())  # type: typing.Optional[sim_info.SimInfo]

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

		if targetSim is None:
			raise Exception("Cannot add condoms to the inventory of a sim that is not instanced.")

		unpackedObject = unpackedObject.get_target()  # type: typing.Optional[script_object.ScriptObject]

		if not isinstance(unpackedObject, script_object.ScriptObject):
			raise ValueError("Failed to get the unpacked object, %s is not a valid object id." % unpackedObject.target_id)

		condomCountStatisticType = services.get_instance_manager(resources.Types.STATISTIC).get(CondomBoxCountStatisticID, None)  # type: typing.Optional[typing.Type[statistic.Statistic]]

		if condomCountStatisticType is None:
			raise ValueError("Failed to get the condom count statistic type, %s is not a valid statistic id." % CondomBoxCountStatisticID)

		condomCountStatisticTracker = unpackedObject.get_tracker(condomCountStatisticType)

		if condomCountStatisticTracker is None:
			raise Exception("Could not find an appropriate condom count statistic tracker in the unpacked object.")

		condomCountStatistic = condomCountStatisticTracker.get_statistic(condomCountStatisticType, add = True)  # type: statistic.Statistic

		condomCount = condomCountStatistic.get_value()  # type: int

		targetSimInventoryComponent = targetSim.inventory_component

		for condomIndex in range(condomCount):
			condomObject = system.create_object(random.choice(WickedWhimsCondomDefinitionIDs))

			if condomObject is not None:
				targetSimInventoryComponent.player_try_add_object(condomObject)

	except:
		output = commands.CheatOutput(_connection)
		output("Failed to add WickedWhim's unpacked condom objects to a sim.")

		Debug.Log("Failed to add WickedWhim's unpacked condom objects to a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

_Setup()
