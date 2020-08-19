import services
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.UI import PregnancyTest as UIPregnancyTest
from NeonOcean.S4.Main import Debug, LoadingShared
from server_commands import argument_helpers
from sims import sim_info
from sims4 import commands

ShowTestResultsCommand: Command.ConsoleCommand

def _Setup () -> None:
	global ShowTestResultsCommand

	commandPrefix = This.Mod.Namespace.lower() + ".pregnancy_test"  # type: str

	ShowTestResultsCommand = Command.ConsoleCommand(_ShowTestResults, commandPrefix + ".show_test_results")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ShowTestResultsCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	ShowTestResultsCommand.UnregisterCommand()

def _ShowTestResults (targetSimHandler: argument_helpers.RequiredTargetParam, _connection: int = None) -> None:
	try:
		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		UIPregnancyTest.ShowTestResultNotification(targetSimInfo)
	except:
		output = commands.CheatOutput(_connection)
		output("Failed to show the pregnancy test results notification for the target sim.")

		Debug.Log("Failed to show the pregnancy test results notification for the target sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

_Setup()
