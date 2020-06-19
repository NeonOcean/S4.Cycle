from __future__ import annotations

from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes

class ImmediateContraceptiveArrival(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Immediate_Contraceptive_Arrival"  # type: str
	Default = True  # type: bool

	ListPath = "Root/Contraceptives"  # type: str

class ShowPurchaseContraceptivesInteractions (SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Show_Purchase_Contraceptives_Interactions"  # type: str
	Default = True  # type: bool

	ListPath = "Root/Contraceptives"  # type: str
