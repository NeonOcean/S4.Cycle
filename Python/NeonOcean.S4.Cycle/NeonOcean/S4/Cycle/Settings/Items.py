from __future__ import annotations

from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes

class PregnancyTestRequiresItem(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Pregnancy_Test_Requires_Item"  # type: str
	Default = True  # type: bool

	ListPath = "Root/Items/PregnancyTest"  # type: str