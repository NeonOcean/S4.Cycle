from __future__ import annotations

import types
import typing

from NeonOcean.S4.Cycle.Settings import Base as SettingsBase, Dialogs as SettingsDialogs, Types as SettingsTypes
from NeonOcean.S4.Cycle.Settings.Contraceptives import ImmediateContraceptiveArrival, ShowPurchaseContraceptivesInteractions
from NeonOcean.S4.Cycle.Settings.Debug import DebugMode
from NeonOcean.S4.Cycle.Settings.LifeSpan import HandleLifeSpan, LifeSpanLongMultiplier, LifeSpanNormalMultiplier, LifeSpanShortMultiplier
from NeonOcean.S4.Cycle.Settings.Reproduction import EasyFertilization, EnableWoohooChanges, WoohooIsAlwaysSafe
from NeonOcean.S4.Cycle.Settings.Time import HandlePregnancySpeed, PregnancySpeed, QuickMode, ReproductiveSpeed
from NeonOcean.S4.Main.Tools import Events

def GetSettingsFilePath () -> str:
	return SettingsBase.SettingsFilePath

def GetAllSettings () -> typing.List[typing.Type[SettingsBase.Setting]]:
	return list(SettingsBase.AllSettings)

def Load () -> None:
	SettingsBase.Load()

def Save () -> None:
	SettingsBase.Save()

def Update () -> None:
	SettingsBase.Update()

def RegisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SettingsBase.UpdateEventArguments], None]) -> None:
	SettingsBase.RegisterOnUpdateCallback(updateCallback)

def UnregisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SettingsBase.UpdateEventArguments], None]) -> None:
	SettingsBase.UnregisterOnUpdateCallback(updateCallback)

def RegisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SettingsBase.RegisterOnLoadCallback(loadCallback)

def UnregisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SettingsBase.UnregisterOnLoadCallback(loadCallback)
