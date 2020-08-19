import services
import typing
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Console import Command
from NeonOcean.S4.Cycle.Safety import WoohooSafety
from NeonOcean.S4.Main import Language, LoadingShared, Debug
from NeonOcean.S4.Main.UI import Notifications
from distributor import shared_messages
from server_commands import argument_helpers
from sims import sim_info

HandlePostCondomUseCommand: Command.ConsoleCommand
HandlePostCondomUseReductionCommand: Command.ConsoleCommand
HandlePostWithdrawUseCommand: Command.ConsoleCommand

CondomBrokeNotificationTitle = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Condom.Broke_Notification.Title")  # type: Language.String
CondomBrokeNotificationText = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Condom.Broke_Notification.Text")  # type: Language.String
CondomRanOutNotificationTitle = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Condom.Ran_Out_Notification.Title")  # type: Language.String
CondomRanOutNotificationText = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Condom.Ran_Out_Notification.Text")  # type: Language.String

WithdrawVeryLateWithdrawNotificationTitle = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Withdraw.Very_Late_Withdraw_Notification.Title")  # type: Language.String
WithdrawVeryLateWithdrawNotificationText = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Withdraw.Very_Late_Withdraw_Notification.Text")  # type: Language.String
WithdrawNoWithdrawNotificationTitle = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Withdraw.No_Withdraw_Notification.Title")  # type: Language.String
WithdrawNoWithdrawNotificationText = Language.String(This.Mod.Namespace + ".Woohoo_Safety_Methods.Withdraw.No_Withdraw_Notification.Text")  # type: Language.String

def _Setup () -> None:
	global HandlePostCondomUseCommand, HandlePostCondomUseReductionCommand, HandlePostWithdrawUseCommand

	commandPrefix = This.Mod.Namespace.lower() + ".woohoo_safety_methods"  # type: str

	HandlePostCondomUseCommand = Command.ConsoleCommand(_HandlePostCondomUse, commandPrefix + ".condom.handle_post_use", showHelp = False)
	HandlePostCondomUseReductionCommand = Command.ConsoleCommand(_HandlePostCondomUseReduction, commandPrefix + ".condom.handle_post_use_reduction", showHelp = False)
	HandlePostWithdrawUseCommand = Command.ConsoleCommand(_HandlePostWithdrawUse, commandPrefix + ".withdraw.handle_post_use", showHelp = False)

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	HandlePostCondomUseCommand.RegisterCommand()
	HandlePostCondomUseReductionCommand.RegisterCommand()
	HandlePostWithdrawUseCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	HandlePostCondomUseCommand.UnregisterCommand()
	HandlePostCondomUseReductionCommand.UnregisterCommand()
	HandlePostWithdrawUseCommand.UnregisterCommand()

def _ShowCondomRanOutNotification (targetSimInfo: sim_info.SimInfo) -> None:
	notificationArguments = {
		"title": CondomRanOutNotificationTitle.GetCallableLocalizationString(),
		"text": CondomRanOutNotificationText.GetCallableLocalizationString(targetSimInfo),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo)
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)


def _ShowCondomBrokeNotification (firstSimInfo: sim_info.SimInfo, secondSimInfo: sim_info.SimInfo) -> None:
	notificationArguments = {
		"title": CondomBrokeNotificationTitle.GetCallableLocalizationString(),
		"text": CondomBrokeNotificationText.GetCallableLocalizationString(firstSimInfo, secondSimInfo),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = firstSimInfo)
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def _ShowWithdrawVeryLateWithdrawNotification (firstSimInfo: sim_info.SimInfo, secondSimInfo: sim_info.SimInfo) -> None:
	notificationArguments = {
		"title": WithdrawVeryLateWithdrawNotificationTitle.GetCallableLocalizationString(),
		"text": WithdrawVeryLateWithdrawNotificationText.GetCallableLocalizationString(firstSimInfo, secondSimInfo),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = firstSimInfo)
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def _ShowWithdrawNoWithdrawNotification (firstSimInfo: sim_info.SimInfo, secondSimInfo: sim_info.SimInfo) -> None:
	notificationArguments = {
		"title": WithdrawNoWithdrawNotificationTitle.GetCallableLocalizationString(),
		"text": WithdrawNoWithdrawNotificationText.GetCallableLocalizationString(firstSimInfo, secondSimInfo),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = firstSimInfo)
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

# noinspection PyUnusedLocal
def _HandlePostCondomUse (
		woohooSafetyMethodGUID: int,
		inseminatedSimHandler: argument_helpers.OptionalSimInfoParam,
		sourceSimHandler: argument_helpers.OptionalSimInfoParam,
		performanceType: str,
		_connection = None) -> None:

	try:
		inseminatedSimInfo = services.sim_info_manager().get(inseminatedSimHandler.target_id)  # type: typing.Optional[sim_info.SimInfo]

		if not isinstance(inseminatedSimInfo, sim_info.SimInfo):
			return

		sourceSimInfo = services.sim_info_manager().get(sourceSimHandler.target_id)  # type: typing.Optional[sim_info.SimInfo]

		if not isinstance(sourceSimInfo, sim_info.SimInfo):
			return

		if WoohooSafety.SuppressWoohooSafetyMethodFailureWarnings(inseminatedSimInfo) or WoohooSafety.SuppressWoohooSafetyMethodFailureWarnings(sourceSimInfo):
			return

		if performanceType == "Broke":
			_ShowCondomBrokeNotification(inseminatedSimInfo, sourceSimInfo)
	except Exception as e:
		Debug.Log("Failed to handle post condom use.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

# noinspection PyUnusedLocal
def _HandlePostCondomUseReduction (
		woohooSafetyMethodGUID: int,
		targetSimHandler: argument_helpers.OptionalSimInfoParam,
		usesRemaining: int,
		_connection = None) -> None:

	try:
		targetSimInfo = services.sim_info_manager().get(targetSimHandler.target_id)  # type: typing.Optional[sim_info.SimInfo]

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			return

		if usesRemaining <= 0:
			_ShowCondomRanOutNotification(targetSimInfo)
	except Exception as e:
		Debug.Log("Failed to handle post condom use reduction.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

# noinspection PyUnusedLocal
def _HandlePostWithdrawUse (
		woohooSafetyMethodGUID: int,
		inseminatedSimHandler: argument_helpers.OptionalSimInfoParam,
		sourceSimHandler: argument_helpers.OptionalSimInfoParam,
		performanceType: str,
		_connection = None) -> None:

	try:
		inseminatedSimInfo = services.sim_info_manager().get(inseminatedSimHandler.target_id)  # type: typing.Optional[sim_info.SimInfo]

		if not isinstance(inseminatedSimInfo, sim_info.SimInfo):
			return

		sourceSimInfo = services.sim_info_manager().get(sourceSimHandler.target_id)  # type: typing.Optional[sim_info.SimInfo]

		if not isinstance(sourceSimInfo, sim_info.SimInfo):
			return

		if WoohooSafety.SuppressWoohooSafetyMethodFailureWarnings(inseminatedSimInfo) or WoohooSafety.SuppressWoohooSafetyMethodFailureWarnings(sourceSimInfo):
			return

		if performanceType == "VeryLateWithdraw":
			_ShowWithdrawVeryLateWithdrawNotification(inseminatedSimInfo, sourceSimInfo)
		elif performanceType == "NoWithdraw":
			_ShowWithdrawNoWithdrawNotification(inseminatedSimInfo, sourceSimInfo)
	except Exception as e:
		Debug.Log("Failed to handle post withdraw use.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		raise e

_Setup()
