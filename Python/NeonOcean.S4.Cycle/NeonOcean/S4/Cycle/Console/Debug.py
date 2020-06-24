import typing

import game_services
import services
from NeonOcean.S4.Cycle import Debug as CycleDebug, Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.Females import CycleTracker, Shared as FemalesShared
from NeonOcean.S4.Main import Debug, Language, LoadingShared
from NeonOcean.S4.Main.UI import Dialogs
from server_commands import argument_helpers
from sims import sim_info
from sims4 import collections
from ui import ui_dialog, ui_dialog_generic, ui_text_input

ShowReproductiveInfoCommand: Command.ConsoleCommand
ShowSetCycleProgressDialogCommand: Command.ConsoleCommand
MakePregnantCommand: Command.ConsoleCommand
EndPregnancyCommand: Command.ConsoleCommand

SetCycleProgressDialogText = Language.String(This.Mod.Namespace + ".Set_Cycle_Progress_Dialog.Text", fallbackText = "Set_Cycle_Progress_Dialog.Text")  # type: Language.String
SetCycleProgressDialogTitle = Language.String(This.Mod.Namespace + ".Set_Cycle_Progress_Dialog.Title", fallbackText = "Set_Cycle_Progress_Dialog.Title")  # type: Language.String
SetCycleProgressDialogOkButton = Language.String(This.Mod.Namespace + ".Set_Cycle_Progress_Dialog.Ok_Button", fallbackText = "Ok_Button")  # type: Language.String
SetCycleProgressDialogCancelButton = Language.String(This.Mod.Namespace + ".Set_Cycle_Progress_Dialog.Cancel_Button", fallbackText = "Cancel_Button")  # type: Language.String

def _Setup () -> None:
	global ShowReproductiveInfoCommand, ShowSetCycleProgressDialogCommand, MakePregnantCommand, EndPregnancyCommand

	commandPrefix = This.Mod.Namespace.lower() + ".debug"  # type: str

	ShowReproductiveInfoCommand = Command.ConsoleCommand(_ShowReproductiveInfo, commandPrefix + ".show_reproductive_info", showHelp = False)
	ShowSetCycleProgressDialogCommand = Command.ConsoleCommand(_ShowSetCycleProgressDialog, commandPrefix + ".show_set_cycle_progress_dialog", showHelp = False)
	MakePregnantCommand = Command.ConsoleCommand(_MakePregnant, commandPrefix + ".make_pregnant", showHelp = False)
	EndPregnancyCommand = Command.ConsoleCommand(_EndPregnancy, commandPrefix + ".end_pregnancy", showHelp = False)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ShowReproductiveInfoCommand.RegisterCommand()
	ShowSetCycleProgressDialogCommand.RegisterCommand()
	MakePregnantCommand.RegisterCommand()
	EndPregnancyCommand.RegisterCommand()



def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	ShowReproductiveInfoCommand.UnregisterCommand()
	ShowSetCycleProgressDialogCommand.UnregisterCommand()
	MakePregnantCommand.UnregisterCommand()
	EndPregnancyCommand.UnregisterCommand()

def _ShowReproductiveInfo (targetSimHandler: argument_helpers.RequiredTargetParam, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		CycleDebug.ShowReproductiveInfoNotifications(targetSimInfo)
	except Exception as e:
		Debug.Log("Failed to show reproductive info for a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

def _ShowSetCycleProgressDialog (targetSimHandler: argument_helpers.RequiredTargetParam, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if targetSimSystem is None:
			return

		targetSimCycleTracker = targetSimSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)  # type: typing.Optional[CycleTracker.CycleTracker]

		if targetSimCycleTracker is None:
			return

		targetSimCycle = targetSimCycleTracker.CurrentCycle

		if targetSimCycle is None:
			return

		currentProgress = round(targetSimCycle.Progress, 3)  # type: float

		def dialogCallback (dialogReference: ui_dialog_generic.UiDialogTextInputOkCancel):
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				nextProgressString = dialogReference.text_input_responses["Input"]  # type: str

				try:
					nextProgress = float(nextProgressString)  # type: float
				except:
					return

				if currentProgress != nextProgress:
					targetSimCycle.Progress = nextProgress

		textInputKey = "Input"  # type: str

		textInputLockedArguments = {
			"sort_order": 0,
		}

		textInput = ui_text_input.UiTextInput.TunableFactory(locked_args = textInputLockedArguments).default  # type: ui_text_input.UiTextInput
		textInputInitialValue = Language.MakeLocalizationStringCallable(Language.CreateLocalizationString(str(currentProgress)))

		textInput.initial_value = textInputInitialValue

		textInputs = collections.make_immutable_slots_class([textInputKey])
		textInputs = textInputs({
			textInputKey: textInput
		})

		dialogArguments = {
			"title": SetCycleProgressDialogTitle.GetCallableLocalizationString(),
			"text": SetCycleProgressDialogText.GetCallableLocalizationString(),
			"text_ok": SetCycleProgressDialogOkButton.GetCallableLocalizationString(),
			"text_cancel": SetCycleProgressDialogCancelButton.GetCallableLocalizationString(),
			"text_inputs": textInputs
		}

		Dialogs.ShowOkCancelInputDialog(callback = dialogCallback, queue = False, **dialogArguments)
	except Exception as e:
		Debug.Log("Failed to show the set cycle progress dialog for a sim.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

def _MakePregnant (targetSimHandler: argument_helpers.RequiredTargetParam, fatherSimHandler: argument_helpers.RequiredTargetParam, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())
		fatherSimInfo = fatherSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		if not isinstance(fatherSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the source sim, %s is not a valid sim id." % fatherSimHandler.target_id)

		targetSimInfo.pregnancy_tracker.clear_pregnancy()
		targetSimInfo.pregnancy_tracker.start_pregnancy(targetSimInfo, fatherSimInfo)
	except Exception as e:
		Debug.Log("Failed to make a sim pregnant.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

def _EndPregnancy (targetSimHandler: argument_helpers.RequiredTargetParam, _connection = None) -> None:
	try:
		if game_services.service_manager is None:
			return

		targetSimInfo = targetSimHandler.get_target(services.sim_info_manager())

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise ValueError("Failed to get the target sim, %s is not a valid sim id." % targetSimHandler.target_id)

		targetSimInfo.pregnancy_tracker.clear_pregnancy()
	except Exception as e:
		Debug.Log("Failed to end a sim's pregnancy.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

_Setup()
