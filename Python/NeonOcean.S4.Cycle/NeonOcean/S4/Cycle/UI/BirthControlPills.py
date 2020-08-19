from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Language
from NeonOcean.S4.Main.Tools import Exceptions
from NeonOcean.S4.Main.UI import Notifications
from distributor import shared_messages
from sims import sim_info
from ui import ui_dialog_notification

MissedPillNotificationTitle = Language.String(This.Mod.Namespace + ".Birth_Control_Pills.Missed_Pill_Notification.Title")  # type: Language.String
MissedPillNotificationText = Language.String(This.Mod.Namespace + ".Birth_Control_Pills.Missed_Pill_Notification.Text")  # type: Language.String

def ShowMissedPillNotification (targetSimInfo: sim_info.SimInfo, missedPills: int) -> None:
	"""
	Show a notification indicating that the target sim forgot to take this many pills.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	if not isinstance(missedPills, int):
		raise Exceptions.IncorrectTypeException(missedPills, "missedPills", (int,))

	notificationArguments = {
		"owner": targetSimInfo,
		"title": MissedPillNotificationTitle.GetCallableLocalizationString(),
		"text": MissedPillNotificationText.GetCallableLocalizationString(targetSimInfo, missedPills),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo),
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT,
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)
