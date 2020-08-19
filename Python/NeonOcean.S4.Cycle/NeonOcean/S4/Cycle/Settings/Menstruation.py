from __future__ import annotations

from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes

class AllSimsExperiencePMS(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "All_Sims_Experience_PMS"  # type: str
	Default = False  # type: bool

	ListPath = "Root/Menstruation"  # type: str