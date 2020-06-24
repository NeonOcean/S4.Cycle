from __future__ import annotations

from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes

class NeutralPregnancyBuffs(SettingsTypes.BooleanEnabledDisabledDialogSetting):
	IsSetting = True  # type: bool

	Key = "Neutral_Pregnancy_Buffs"  # type: str
	Default = True  # type: bool

	#ListPath = "Root/Pregnancy"  # type: str

	@classmethod
	def IsHidden(cls) -> bool:
		return True

