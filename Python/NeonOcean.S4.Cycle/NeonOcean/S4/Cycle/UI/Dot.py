from __future__ import annotations

import typing

import clock
import date_and_time
import services
from NeonOcean.S4.Cycle import Dot, This
from NeonOcean.S4.Cycle.Females.Cycle import Shared as CycleShared
from NeonOcean.S4.Cycle.UI import Resources as CycleUIResources
from NeonOcean.S4.Main import Debug, Language
from NeonOcean.S4.Main.Tools import Exceptions, TextBuilder
from NeonOcean.S4.Main.UI import Notifications
from distributor import shared_messages
from sims import sim_info
from sims4 import localization, resources

StatusNotificationTitle = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Title")  # type: Language.String

StatusNotificationTextTimePeriodStartingToday = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Time_Period.Starting.Today")  # type: Language.String
StatusNotificationTextTimePeriodStartingTomorrow = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Time_Period.Starting.Tomorrow")  # type: Language.String
StatusNotificationTextTimePeriodStartingInDays = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Time_Period.Starting.In_Days")  # type: Language.String
StatusNotificationTextTimePeriodEndingToday = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Time_Period.Ending.Today")  # type: Language.String
StatusNotificationTextTimePeriodEndingTomorrow = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Time_Period.Ending.Tomorrow")  # type: Language.String
StatusNotificationTextTimePeriodEndingInDays = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Time_Period.Ending.In_Days")  # type: Language.String

StatusNotificationTextFollicular = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Follicular")  # type: Language.String
StatusNotificationTextLuteal = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Luteal")  # type: Language.String

StatusNotificationTextOvulationStarting = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Ovulation.Starting")  # type: Language.String
StatusNotificationTextOvulationEnding = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Ovulation.Ending")  # type: Language.String

StatusNotificationTextMenstruationStarting = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Menstruation.Starting")  # type: Language.String
StatusNotificationTextMenstruationEnding = Language.String(This.Mod.Namespace + ".Dot.Status_Notification.Text.Menstruation.Ending")  # type: Language.String

ErrorNotificationTitle = Language.String(This.Mod.Namespace + ".Dot.Error_Notification.Title")  # type: Language.String
ErrorNotificationText = Language.String(This.Mod.Namespace + ".Dot.Error_Notification.Text")  # type: Language.String

FertilityNotificationsEnabledNotificationTitle = Language.String(This.Mod.Namespace + ".Dot.Fertility_Notifications_Enabled_Notification.Title")  # type: Language.String
FertilityNotificationsEnabledNotificationText = Language.String(This.Mod.Namespace + ".Dot.Fertility_Notifications_Enabled_Notification.Text")  # type: Language.String

FertilityNotificationTitle = Language.String(This.Mod.Namespace + ".Dot.Fertility_Notification.Title")  # type: Language.String
FertilityNotificationText = Language.String(This.Mod.Namespace + ".Dot.Fertility_Notification.Text")  # type: Language.String

def ShowStatusNotification (targetSimInfo: sim_info.SimInfo) -> None:  # TODO create quick glance notification, only show the times?
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	targetDotInformation = Dot.GetDotInformation(targetSimInfo)  # type: typing.Optional[Dot.DotInformation]

	if targetDotInformation is None:
		Debug.Log("Attempted to show a dot app status notification on a sim missing a dot information object.\nSim ID: %s" % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	if not targetDotInformation.Enabled:
		Debug.Log("Attempted to show a dot app status notification on a sim its not enabled for.\nSim ID: %s" % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	dotCycle = targetDotInformation.GetCurrentCycle()  # type: typing.Optional[Dot.DotCycle]

	if dotCycle is None:
		ShowErrorNotification(targetSimInfo)
		return

	text = Language.MakeLocalizationStringCallable(_BuildStatusText(targetSimInfo, dotCycle))

	notificationArguments = {
		"owner": targetSimInfo,
		"title": StatusNotificationTitle.GetCallableLocalizationString(),
		"text": text,
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(icon_resource = resources.ResourceKeyWrapper(CycleUIResources.DotAppIconKey)),
		"secondary_icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo),
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def ShowErrorNotification (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	notificationArguments = {
		"owner": targetSimInfo,
		"title": ErrorNotificationTitle.GetCallableLocalizationString(),
		"text": ErrorNotificationText.GetCallableLocalizationString(),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(icon_resource = resources.ResourceKeyWrapper(CycleUIResources.DotAppIconKey)),
		"secondary_icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo),
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def ShowFertilityNotificationsEnabledNotification (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	notificationArguments = {
		"owner": targetSimInfo,
		"title": FertilityNotificationsEnabledNotificationTitle.GetCallableLocalizationString(),
		"text": FertilityNotificationsEnabledNotificationText.GetCallableLocalizationString(),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(icon_resource = resources.ResourceKeyWrapper(CycleUIResources.DotAppIconKey)),
		"secondary_icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo),
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def ShowFertilityNotification (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	notificationArguments = {
		"owner": targetSimInfo,
		"title": FertilityNotificationTitle.GetCallableLocalizationString(),
		"text": FertilityNotificationText.GetCallableLocalizationString(),
		"icon": lambda *args, **kwargs: shared_messages.IconInfoData(icon_resource = resources.ResourceKeyWrapper(CycleUIResources.DotAppIconKey)),
		"secondary_icon": lambda *args, **kwargs: shared_messages.IconInfoData(obj_instance = targetSimInfo),
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

def _BuildStatusText (targetSimInfo: sim_info.SimInfo, dotCycle: Dot.DotCycle) -> localization.LocalizedString:
	if typing.TYPE_CHECKING:
		majorPhaseText: localization.LocalizedString
		majorPhaseTimePeriodText: localization.LocalizedString

		minorPhaseText: localization.LocalizedString
		minorPhaseTimePeriodText: localization.LocalizedString

	if dotCycle.GetPhaseIsActive(CycleShared.MenstrualCyclePhases.Follicular):
		majorPhaseText = StatusNotificationTextFollicular.GetLocalizationString()
		majorPhaseTimePeriodText = _GetStatusTimePeriodEndingText(dotCycle.GetTimeUntilPhaseEnds(CycleShared.MenstrualCyclePhases.Follicular))
	elif dotCycle.GetPhaseIsActive(CycleShared.MenstrualCyclePhases.Luteal):
		majorPhaseText = StatusNotificationTextLuteal.GetLocalizationString()
		majorPhaseTimePeriodText = _GetStatusTimePeriodEndingText(dotCycle.GetTimeUntilPhaseEnds(CycleShared.MenstrualCyclePhases.Luteal))
	else:
		majorPhaseText = StatusNotificationTextLuteal.GetLocalizationString()
		majorPhaseTimePeriodText = _GetStatusTimePeriodEndingText(dotCycle.GetTimeUntilPhaseEnds(CycleShared.MenstrualCyclePhases.Luteal))
		Debug.Log("The follicular and luteal phases were both inactive, according to dot.\nTarget Sim ID: %s" % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

	if dotCycle.GetPhaseIsActive(CycleShared.MenstrualCyclePhases.Ovulation):
		minorPhaseText = StatusNotificationTextOvulationEnding.GetLocalizationString()
		minorPhaseTimePeriodText = _GetStatusTimePeriodEndingText(dotCycle.GetTimeUntilPhaseEnds(CycleShared.MenstrualCyclePhases.Ovulation))
	elif dotCycle.GetPhaseIsActive(CycleShared.MenstrualCyclePhases.Menstruation):
		minorPhaseText = StatusNotificationTextMenstruationEnding.GetLocalizationString()
		minorPhaseTimePeriodText = _GetStatusTimePeriodEndingText(dotCycle.GetTimeUntilPhaseEnds(CycleShared.MenstrualCyclePhases.Menstruation))
	else:
		timeUntilOvulation = dotCycle.GetTimeUntilPhaseStarts(CycleShared.MenstrualCyclePhases.Ovulation)  # type: float
		timeUntilMenstruation = dotCycle.GetTimeUntilPhaseStarts(CycleShared.MenstrualCyclePhases.Menstruation)  # type: float

		if timeUntilOvulation > 0:
			minorPhaseText = StatusNotificationTextOvulationStarting.GetLocalizationString()
			minorPhaseTimePeriodText = _GetStatusTimePeriodStartingText(dotCycle.GetTimeUntilPhaseStarts(CycleShared.MenstrualCyclePhases.Ovulation))
		elif timeUntilMenstruation > 0:
			minorPhaseText = StatusNotificationTextMenstruationStarting.GetLocalizationString()
			minorPhaseTimePeriodText = _GetStatusTimePeriodStartingText(dotCycle.GetTimeUntilPhaseStarts(CycleShared.MenstrualCyclePhases.Menstruation))
		else:
			minorPhaseText = StatusNotificationTextMenstruationStarting.GetLocalizationString()
			minorPhaseTimePeriodText = _GetStatusTimePeriodStartingText(dotCycle.GetTimeUntilPhaseStarts(CycleShared.MenstrualCyclePhases.Menstruation))
			Debug.Log("The ovulation and menstruation phases have both finished, according to dot. The cycle was supposed to end at the same time menstruation did.\nTarget Sim ID: %s" % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

	statusText = TextBuilder.BuildText(
		[
			majorPhaseText,
			"\n",
			majorPhaseTimePeriodText,
			"\n\n",
			minorPhaseText,
			"\n",
			minorPhaseTimePeriodText
		]
	)

	return statusText

def _GetStatusTimePeriodStartingText (minutesUntil: float) -> localization.LocalizedString:
	return _GetStatusTimePeriodText(minutesUntil, StatusNotificationTextTimePeriodStartingToday, StatusNotificationTextTimePeriodStartingTomorrow, StatusNotificationTextTimePeriodStartingInDays)

def _GetStatusTimePeriodEndingText (minutesUntil: float) -> localization.LocalizedString:
	return _GetStatusTimePeriodText(minutesUntil, StatusNotificationTextTimePeriodEndingToday, StatusNotificationTextTimePeriodEndingTomorrow, StatusNotificationTextTimePeriodEndingInDays)

def _GetStatusTimePeriodText (minutesUntil: float, todayString: Language.String, tomorrowString: Language.String, inDaysString: Language.String) -> localization.LocalizedString:
	currentTime = services.time_service().sim_now  # type: date_and_time.DateAndTime

	timeSpanToMidnight = clock.time_until_hour_of_day(currentTime, 24)  # type: date_and_time.TimeSpan

	minutesUntilMidnight = timeSpanToMidnight.in_minutes()  # type: float
	minutesUntilNextMidnight = (timeSpanToMidnight + clock.interval_in_sim_time(24, date_and_time.TimeUnit.HOURS)).in_minutes()  # type: float

	if minutesUntil < 0:
		Debug.Log("Tried to get a status time period text with a negative 'minutesUntil' value.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
		minutesUntil = 0

	if minutesUntil <= minutesUntilMidnight:
		return todayString.GetLocalizationString()
	elif minutesUntil <= minutesUntilNextMidnight:
		return tomorrowString.GetLocalizationString()
	else:
		daysUntil = (minutesUntil + minutesUntilMidnight) / (date_and_time.MINUTES_PER_HOUR * date_and_time.HOURS_PER_DAY)  # type: float
		daysUntil = round(daysUntil)  # type: int

		return inDaysString.GetLocalizationString(daysUntil)
