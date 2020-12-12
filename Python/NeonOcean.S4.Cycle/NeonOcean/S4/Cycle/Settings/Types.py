from __future__ import annotations

import math
import numbers
import typing

from NeonOcean.S4.Cycle import Guides, This
from NeonOcean.S4.Cycle.Settings import Base as SettingsBase, Dialogs as SettingsDialogs
from NeonOcean.S4.Main import Language
from NeonOcean.S4.Main.Tools import Exceptions, Numbers as ToolsNumbers, Version
from sims4 import localization

class BooleanSetting(SettingsBase.Setting):
	Type = bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def GetValueText (cls, value: bool) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean." + valueString, fallbackText = valueString)

class BooleanDialogSetting(BooleanSetting):
	Dialog = SettingsDialogs.BooleanDialog

class BooleanEnabledDisabledSetting(BooleanSetting):
	@classmethod
	def GetValueText (cls, value: bool) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Enabled_Disabled." + valueString, fallbackText = valueString)

class BooleanEnabledDisabledDialogSetting(BooleanEnabledDisabledSetting):
	Dialog = SettingsDialogs.BooleanEnabledDisabledDialog

class BooleanYesNoSetting(BooleanSetting):
	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Yes_No." + valueString, fallbackText = valueString)

class BooleanYesNoDialogSetting(BooleanYesNoSetting):
	Dialog = SettingsDialogs.BooleanYesNoDialog

class RealNumberSetting(SettingsBase.Setting):
	Type = numbers.Real

	@classmethod
	def Verify (cls, value: typing.Union[float, int], lastChangeVersion: Version.Version = None) -> typing.Union[float, int]:
		cls._TypeCheckValue(value)

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def GetValueText (cls, value: typing.Union[float, int]) -> localization.LocalizedString:
		cls._TypeCheckValue(value)

		valueString = str(value)  # type: str
		return Language.CreateLocalizationString(valueString)

	@classmethod
	def _TypeCheckValue (cls, value: typing.Union[float, int]) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "value", (float, int))

		if not ToolsNumbers.IsRealNumber(value):
			raise ValueError("Value is not a real number.")

class RealNumberDialogSetting(RealNumberSetting):
	Dialog = SettingsDialogs.RealNumberDialog

class ReproductiveSpeedSetting(SettingsBase.Setting):
	Type = numbers.Real

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		if not isinstance(value, numbers.Real):
			raise Exceptions.IncorrectTypeException(value, "value", (numbers.Real,))

		if math.isnan(value):
			raise ValueError("Value cannot be 'not a number'.")

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		humanCycleDays = str(round(value * cls._GetHumanCycleRealDays(), 1))  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Reproductive_Speed.Value", humanCycleDays, fallbackText = humanCycleDays)

	@classmethod
	def _GetHumanCycleRealDays (cls) -> float:
		humanCycleGuide = Guides.HumanCycleMenstrualGuide.Guide
		return (humanCycleGuide.FollicularLength.Mean + humanCycleGuide.LutealLength.Mean) / 1440

class ReproductiveSpeedDialogSetting(ReproductiveSpeedSetting):
	Dialog = SettingsDialogs.ReproductiveSpeedDialog

class PregnancySpeedSetting(SettingsBase.Setting):
	Type = numbers.Real

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		if not isinstance(value, numbers.Real):
			raise Exceptions.IncorrectTypeException(value, "value", (numbers.Real,))

		if math.isnan(value):
			raise ValueError("Value cannot be 'not a number'.")

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		humanPregnancyDays = str(round(value * cls._GetHumanPregnancyRealDays(), 1))  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Pregnancy_Speed.Value", humanPregnancyDays, fallbackText = humanPregnancyDays)

	@classmethod
	def _GetHumanPregnancyRealDays (cls) -> float:
		return Guides.HumanPregnancyGuide.Guide.PregnancyTime / 1440

class PregnancySpeedDialogSetting(PregnancySpeedSetting):
	Dialog = SettingsDialogs.PregnancySpeedDialog
