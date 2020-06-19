from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, This
from NeonOcean.S4.Main import Debug, Language
from NeonOcean.S4.Main.Tools import Exceptions
from NeonOcean.S4.Main.UI import Notifications
from sims import sim_info

def ShowReproductiveInfoNotifications (targetSimInfo: sim_info.SimInfo) -> None:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

	if targetSimSystem is None:
		return

	notificationText = targetSimSystem.GetDebugNotificationString()

	notificationArguments = {
		"title": Language.MakeLocalizationStringCallable(Language.CreateLocalizationString("")),
		"text": Language.MakeLocalizationStringCallable(Language.CreateLocalizationString(notificationText)),
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)

	Debug.Log("Collected and reported debug info from a sim's reproductive system by request.\n\n%s" % notificationText, This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
