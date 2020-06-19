import typing

import game_services
import services
from NeonOcean.S4.Cycle import Insemination, Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Main import Debug, LoadingShared
from server_commands import argument_helpers
from sims import sim_info

AddSpermCommand: Command.ConsoleCommand
ClearSpermCommand: Command.ConsoleCommand
AddOvumCommand: Command.ConsoleCommand
ClearOvaCommand: Command.ConsoleCommand

def _Setup () -> None:
	global AddSpermCommand, ClearSpermCommand, AddOvumCommand, ClearOvaCommand

	commandPrefix = This.Mod.Namespace.lower()  # type: str

	AddSpermCommand = Command.ConsoleCommand(_AddSperm, commandPrefix + ".add_sperm", showHelp = False)
	ClearSpermCommand = Command.ConsoleCommand(_ClearSperm, commandPrefix + ".clear_sperm", showHelp = False)
	AddOvumCommand = Command.ConsoleCommand(_AddOvum, commandPrefix + ".add_ovum", showHelp = False)
	ClearOvaCommand = Command.ConsoleCommand(_ClearOva, commandPrefix + ".clear_ova", showHelp = False)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	AddSpermCommand.RegisterCommand()
	ClearSpermCommand.RegisterCommand()
	AddOvumCommand.RegisterCommand()
	ClearOvaCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	AddSpermCommand.UnregisterCommand()
	ClearSpermCommand.UnregisterCommand()
	AddOvumCommand.UnregisterCommand()
	ClearOvaCommand.UnregisterCommand()

def _AddSperm (targetSimHandler: argument_helpers.RequiredTargetParam, sourceSimHandler: argument_helpers.RequiredTargetParam, tryingForBaby: bool = True, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())
		sourceSimInfo = sourceSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		if not isinstance(sourceSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the source sim, %s is not a valid sim id." % sourceSimHandler.target_id)

		Insemination.AutoInseminate(targetSimInfo, sourceSimInfo, tryingForBaby = tryingForBaby, generateGenericSperm = True)
	except Exception as e:
		Debug.Log("Failed to add sperm to a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

def _ClearSperm (targetSimHandler: argument_helpers.RequiredTargetParam, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)


		targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if targetSimSystem is None:
			return

		targetSimSpermTracker = targetSimSystem.GetTracker(FemalesShared.SpermTrackerIdentifier)

		if targetSimSpermTracker is None:
			return

		targetSimSpermTracker.ClearAllSperm()
	except Exception as e:
		Debug.Log("Failed to clear sperm from a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

def _AddOvum (targetSimHandler: argument_helpers.RequiredTargetParam, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if targetSimSystem is None:
			return

		targetSimOvumTracker = targetSimSystem.GetTracker(FemalesShared.OvumTrackerIdentifier)

		if targetSimOvumTracker is None:
			return

		targetSimOvumTracker.GenerateAndReleaseOvum()
	except Exception as e:
		Debug.Log("Failed to add an ovum to a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

def _ClearOva (targetSimHandler: argument_helpers.RequiredTargetParam, clearFertilized: bool = True , _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if targetSimSystem is None:
			return

		targetSimOvumTracker = targetSimSystem.GetTracker(FemalesShared.OvumTrackerIdentifier)

		if targetSimOvumTracker is None:
			return

		targetSimOvumTracker.ClearAllOva(clearFertilized = clearFertilized)
	except Exception as e:
		Debug.Log("Failed to clear sperm from a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

_Setup()
