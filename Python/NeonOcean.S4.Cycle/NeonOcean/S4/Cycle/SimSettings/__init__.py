from __future__ import annotations

import types
import typing

from NeonOcean.S4.Cycle.SimSettings import Base as SimSettingsBase
from NeonOcean.S4.Cycle.SimSettings.WoohooSafety import WoohooSafetyMethodUse
from NeonOcean.S4.Cycle.SimSettings.Menstruation import ExperiencesPMS
from NeonOcean.S4.Main.Tools import Events

def GetAllSettings () -> typing.List[typing.Type[SimSettingsBase.Setting]]:
	return SimSettingsBase.GetAllSettings()

def Update () -> None:
	SimSettingsBase.Update()

def RegisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SimSettingsBase.UpdateEventArguments], None]) -> None:
	SimSettingsBase.RegisterOnUpdateCallback(updateCallback)

def UnregisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SimSettingsBase.UpdateEventArguments], None]) -> None:
	SimSettingsBase.UnregisterOnUpdateCallback(updateCallback)

def RegisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SimSettingsBase.RegisterOnLoadCallback(loadCallback)

def UnregisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SimSettingsBase.UnregisterOnLoadCallback(loadCallback)
