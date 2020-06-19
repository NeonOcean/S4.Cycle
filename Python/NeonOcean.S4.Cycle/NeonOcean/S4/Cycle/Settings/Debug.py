from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes

class DebugMode(SettingsTypes.BooleanEnabledDisabledDialogSetting):
	IsSetting = True  # type: bool

	Key = "Debug_Mode"  # type: str
	Default = True  # type: bool
