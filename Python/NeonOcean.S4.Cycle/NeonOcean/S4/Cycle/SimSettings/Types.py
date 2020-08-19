from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.SimSettings import Base as SettingsBase, Dialogs as SettingsDialogs
from NeonOcean.S4.Main import Language
from NeonOcean.S4.Main.Tools import Exceptions, Version
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

class BooleanYesNoSetting (BooleanSetting):
	@classmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Yes_No." + valueString, fallbackText = valueString)

class BooleanYesNoDialogSetting(BooleanYesNoSetting):
	Dialog = SettingsDialogs.BooleanYesNoDialog

class WoohooSafetyMethodUseSetting(SettingsBase.Setting):
	Type = dict

	@classmethod
	def Verify (cls, value: dict, lastChangeVersion: Version.Version = None) -> dict:
		if not isinstance(value, dict):
			raise Exceptions.IncorrectTypeException(value, "value", (dict,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		for methodID, usingMethod in value.items():  # type: typing.Union[int, str], bool
			if isinstance(methodID, str):
				try:
					methodID = int(methodID)
				except ValueError as e:
					raise ValueError("Cannot convert the method id value '%s' to integer." % methodID) from e

			if not isinstance(methodID, int):
				raise Exceptions.IncorrectTypeException(methodID, "value<Key>", (int,))

			if not isinstance(usingMethod, int):
				raise Exceptions.IncorrectTypeException(usingMethod, "value[%s]" % methodID, (bool,))

		return value
