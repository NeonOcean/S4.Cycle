import typing

import services
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.Safety import EmergencyContraceptivePill as SafetyEmergencyContraceptivePill
from NeonOcean.S4.Main import Debug, LoadingShared
from server_commands import argument_helpers
from objects import script_object
from sims import sim_info
from sims4 import commands

TakePillCommand: Command.ConsoleCommand

def _Setup () -> None:
	global TakePillCommand

	commandPrefix = This.Mod.Namespace.lower() + ".emergency_contraceptive_pill"  # type: str

	TakePillCommand = Command.ConsoleCommand(_TakePill, commandPrefix + ".take_pill")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	TakePillCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	TakePillCommand.UnregisterCommand()

def _TakePill (
		targetSimHandler: argument_helpers.RequiredTargetParam,
		pillsObjectHandler: argument_helpers.RequiredTargetParam,
		requiresPill: bool = True,
		removePill: bool = True,
		showGeneralFeedback: bool = True,
		_connection: int = None) -> None:

	try:
		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		pillsObject = services.inventory_manager().get(pillsObjectHandler.target_id)  # type: typing.Optional[script_object.ScriptObject]

		if pillsObject is None:
			pillsObject = services.object_manager().get(pillsObjectHandler.target_id)  # type: typing.Optional[script_object.ScriptObject]

		if not isinstance(pillsObject, script_object.ScriptObject):
			raise ValueError("Failed to get the pills object, %s is not a valid script object id." % targetSimHandler.target_id)

		SafetyEmergencyContraceptivePill.TakePill(targetSimInfo, pillsObject = pillsObject, requiresPill = requiresPill, removePill = removePill, showGeneralFeedback = showGeneralFeedback)
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to run the take pill command for the target sim.")

		Debug.Log("Failed to run the take pill command for the target sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

_Setup()
