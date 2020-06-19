from __future__ import annotations

from NeonOcean.S4.Cycle.Settings import Types as SettingsTypes
from NeonOcean.S4.Main.Tools import Version

class ReproductiveSpeed(SettingsTypes.ReproductiveSpeedDialogSetting): # TODO make the dialog's limits text fixed in the stbl text.
	IsSetting = True  # type: bool

	Key = "Reproductive_Speed"  # type: str
	Default = 0.15  # type: float

	ListPath = "Root/Time"  # type: str
	ListPriority = 100  # type: float

	Minimum = 0.035  # type: float
	Maximum = 2  # type: float

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if not (cls.Minimum <= value <= cls.Maximum):
			raise ValueError("Value must be greater than '" + str(cls.Minimum) + "' and less than '" + str(cls.Maximum) + "'.")

		return value

class HandlePregnancySpeed(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Handle_Pregnancy_Speed"  # type: str
	Default = False  # type: bool

	ListPath = "Root/Time"  # type: str
	ListPriority = 55  # type: float

class PregnancySpeed(SettingsTypes.PregnancySpeedDialogSetting): # TODO make the dialog's limits text fixed in the stbl text.
	IsSetting = True  # type: bool

	Key = "Pregnancy_Speed"  # type: str
	Default = 0.015  # type: float

	ListPath = "Root/Time"  # type: str
	ListPriority = 50  # type: float

	Minimum = 0.0035  # type: float
	Maximum = 2  # type: float

	@classmethod
	def IsHidden(cls) -> bool:
		return not HandlePregnancySpeed.Get()

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if not (cls.Minimum <= value <= cls.Maximum):
			raise ValueError("Value must be greater than '" + str(cls.Minimum) + "' and less than '" + str(cls.Maximum) + "'.")

		return value

class QuickMode(SettingsTypes.BooleanEnabledDisabledDialogSetting):
	IsSetting = True  # type: bool

	Key = "Quick_Mode"  # type: str
	Default = False  # type: bool

	ListPath = "Root/Time"  # type: str
	ListPriority = 25  # type: float
