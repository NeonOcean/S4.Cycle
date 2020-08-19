import typing

from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared, PregnancyTracker
from NeonOcean.S4.Main.Tools import Exceptions
from NeonOcean.S4.Main import Language
from NeonOcean.S4.Main.UI import Notifications
from distributor import shared_messages
from sims import sim_info

PositiveTestResultNotificationTitle = Language.String(This.Mod.Namespace + ".Pregnancy_Test.Positive_Test_Result_Notification.Title")  # type: Language.String
PositiveTestResultNotificationText = Language.String(This.Mod.Namespace + ".Pregnancy_Test.Positive_Test_Result_Notification.Text")  # type: Language.String

NegativeTestResultNotificationTitle = Language.String(This.Mod.Namespace + ".Pregnancy_Test.Negative_Test_Result_Notification.Title")  # type: Language.String
NegativeTestResultNotificationText = Language.String(This.Mod.Namespace + ".Pregnancy_Test.Negative_Test_Result_Notification.Text")  # type: Language.String

def ShowTestResultNotification (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo, ))

	targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: ReproductionShared.ReproductiveSystem

	if targetSimSystem is None:
		ShowNegativeTestResultNotification(targetSimInfo)
		return

	targetPregnancyTracker = targetSimSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)  # type: typing.Optional[PregnancyTracker.PregnancyTracker]

	if targetPregnancyTracker.GeneratePregnancyTestResults():
		ShowPositiveTestResultNotification(targetSimInfo)
	else:
		ShowNegativeTestResultNotification(targetSimInfo)

def ShowPositiveTestResultNotification (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo, ))

	notificationArguments = {
		"title": PositiveTestResultNotificationTitle.GetCallableLocalizationString(),
		"text": PositiveTestResultNotificationText.GetCallableLocalizationString(targetSimInfo),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo)
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def ShowNegativeTestResultNotification (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo, ))

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	notificationArguments = {
		"title": NegativeTestResultNotificationTitle.GetCallableLocalizationString(),
		"text": NegativeTestResultNotificationText.GetCallableLocalizationString(targetSimInfo),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo)
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)