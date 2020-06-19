from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Main import LoadingShared
from server_commands import argument_helpers

HandlePostCondomUseCommand: Command.ConsoleCommand

def _Setup () -> None:
	global HandlePostCondomUseCommand

	commandPrefix = This.Mod.Namespace.lower() + ".safety"  # type: str

	HandlePostCondomUseCommand = Command.ConsoleCommand(_HandlePostCondomUse, commandPrefix + ".handle_post_condom_use", showHelp = False)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	HandlePostCondomUseCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	HandlePostCondomUseCommand.UnregisterCommand()

# noinspection PyUnusedLocal
def _HandlePostCondomUse (
		woohooSafetyMethodGUID: int,
		inseminatedSimInfo: argument_helpers.OptionalTargetParam,
		sourceSimInfo: argument_helpers.OptionalTargetParam,
		performanceType: str,
		_connection = None) -> None:
	pass

_Setup()
