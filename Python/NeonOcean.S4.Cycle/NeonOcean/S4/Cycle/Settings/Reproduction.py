from __future__ import annotations

from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes

class EnableWoohooChanges(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Enable_Woohoo_Changes"  # type: str
	Default = True  # type: bool

	ListPath = "Root/Reproduction"  # type: str

class WoohooIsAlwaysSafe(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Woohoo_Is_Always_Safe"  # type: str
	Default = False  # type: bool

	ListPath = "Root/Reproduction"  # type: str

class EasyFertilization(SettingsTypes.BooleanEnabledDisabledDialogSetting):
	IsSetting = True  # type: bool

	Key = "Easy_Fertilization"  # type: str
	Default = False  # type: bool

	ListPath = "Root/Reproduction"  # type: str