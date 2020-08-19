from NeonOcean.S4.Cycle import SimSettings, This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.SimSettings import Base as SettingsBase, List as SettingsList
from NeonOcean.S4.Main import Debug, LoadingShared
from sims4 import commands

PrintNamesCommand: Command.ConsoleCommand
ShowDialogCommand: Command.ConsoleCommand
ShowListCommand: Command.ConsoleCommand

def _Setup () -> None:
	global PrintNamesCommand, ShowDialogCommand, ShowListCommand

	commandPrefix = This.Mod.Namespace.lower() + ".sim_settings"

	PrintNamesCommand = Command.ConsoleCommand(_PrintNames, commandPrefix + ".print_names", showHelp = True)
	ShowDialogCommand = Command.ConsoleCommand(_ShowDialog, commandPrefix + ".show_dialog", showHelp = True, helpInput = "{ setting name }")
	ShowListCommand = Command.ConsoleCommand(_ShowList, commandPrefix + ".show_list", showHelp = True)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	PrintNamesCommand.RegisterCommand()
	ShowDialogCommand.RegisterCommand()
	ShowListCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	PrintNamesCommand.UnregisterCommand()
	ShowDialogCommand.UnregisterCommand()
	ShowListCommand.UnregisterCommand()

def _PrintNames (_connection: int = None) -> None:
	try:
		allSettings = SimSettings.GetAllSettings()

		settingKeysString = ""

		for setting in allSettings:  # type: SettingsBase.Setting
			if len(settingKeysString) == 0:
				settingKeysString += setting.Key
			else:
				settingKeysString += "\n" + setting.Key

		commands.cheat_output(settingKeysString + "\n", _connection)
	except Exception as e:
		commands.cheat_output("Failed to print setting names.", _connection)
		Debug.Log("Failed to print setting names.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

def _ShowDialog (key: str, branch: str, _connection: int = None) -> None:
	try:
		allSettings = SimSettings.GetAllSettings()

		for setting in allSettings:  # type: SettingsBase.Setting
			if setting.Key.lower() == key:
				setting.ShowDialog(branch)
				return

	except Exception as e:
		commands.cheat_output("Failed to show dialog for setting '" + key + "'.", _connection)
		Debug.Log("Failed to show dialog for setting '" + key + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

	commands.cheat_output("Cannot find setting '" + key + "'.\n", _connection)

def _ShowList (branch: str, _connection: int = None) -> None:
	try:
		SettingsList.ShowListDialog(branch)
	except Exception:
		commands.cheat_output("Failed to show settings list dialog.", _connection)
		Debug.Log("Failed to show settings list dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
		return

_Setup()
