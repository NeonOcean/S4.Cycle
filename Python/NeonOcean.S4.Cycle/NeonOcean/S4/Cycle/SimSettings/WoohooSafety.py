from __future__ import annotations

from NeonOcean.S4.Cycle.SimSettings import Types as SettingsTypes
from NeonOcean.S4.Main.Tools import Exceptions

class AutonomouslyUseWoohooSafetyMethods(SettingsTypes.BooleanYesNoDialogSetting):# TODO use
	IsSetting = True  # type: bool

	Key = "Autonomously_Use_Woohoo_Safety_Methods"  # type: str
	Default = True  # type: bool

	@classmethod
	def IsHidden (cls, simID: str) -> bool:
		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		return True

class WoohooSafetyMethodUse(SettingsTypes.WoohooSafetyMethodUseSetting):
	IsSetting = True  # type: bool

	Key = "Woohoo_Safety_Method_Use"  # type: str
	Default = dict()  # type: dict

	@classmethod
	def IsHidden (cls, simID: str) -> bool:
		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		return True


