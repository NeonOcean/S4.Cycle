import typing

import services
from NeonOcean.S4.Cycle import Dot, This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.UI import Dot as UIDot
from NeonOcean.S4.Main import Debug, LoadingShared
from server_commands import argument_helpers
from sims import sim_info
from sims4 import commands

EnableCommand: Command.ConsoleCommand
DisableCommand: Command.ConsoleCommand
ShowStatusNotificationCommand: Command.ConsoleCommand

def _Setup () -> None:
	global EnableCommand, DisableCommand, ShowStatusNotificationCommand

	commandPrefix = This.Mod.Namespace.lower() + ".dot"  # type: str
	EnableCommand = Command.ConsoleCommand(_Install, commandPrefix + ".enable")
	DisableCommand = Command.ConsoleCommand(_Uninstall, commandPrefix + ".disable")
	ShowStatusNotificationCommand = Command.ConsoleCommand(_ShowStatusNotification, commandPrefix + ".show_status_notification")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	EnableCommand.RegisterCommand()
	DisableCommand.RegisterCommand()
	ShowStatusNotificationCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	EnableCommand.UnregisterCommand()
	DisableCommand.UnregisterCommand()
	ShowStatusNotificationCommand.UnregisterCommand()

def _Install (targetSimHandler: argument_helpers.RequiredTargetParam, _connection: int = None) -> None:
	try:
		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		dotInformation = Dot.GetDotInformation(targetSimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is None:
			raise Exception("Missing dot information object for a sim with the id %s." % targetSimInfo.id)

		dotInformation.Enabled = True
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to enable the dot app on the target sim's phone.")

		Debug.Log("Failed to enable the dot app on the target sim's phone.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _Uninstall (targetSimHandler: argument_helpers.RequiredTargetParam, _connection: int = None) -> None:
	try:
		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		dotInformation = Dot.GetDotInformation(targetSimInfo)  # type: typing.Optional[Dot.DotInformation]

		if dotInformation is None:
			raise Exception("Missing dot information object for a sim with the id %s." % targetSimInfo.id)

		dotInformation.Enabled = False
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to disable the dot app on the target sim's phone.")

		Debug.Log("Failed to disable the dot app on the target sim's phone.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _ShowStatusNotification (targetSimHandler: argument_helpers.RequiredTargetParam, _connection: int = None) -> None:
	try:
		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		UIDot.ShowStatusNotification(targetSimInfo)
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to show the dot status notification for the target sim.")

		Debug.Log("Failed to show the dot status notification for the target sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

_Setup()
