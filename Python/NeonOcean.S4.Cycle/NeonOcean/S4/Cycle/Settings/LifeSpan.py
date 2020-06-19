from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Settings import Dialogs as SettingsDialogs, Types as SettingsTypes
from NeonOcean.S4.Cycle.Tools import LifeSpan as ToolsLifeSpan
from NeonOcean.S4.Main import Language, Websites
from NeonOcean.S4.Main.Tools import Version
from NeonOcean.S4.Main.UI import Settings as UISettings, SettingsShared as UISettingsShared
from sims import sim_info_types
from sims4 import localization
from ui import ui_dialog

class LifeSpanMultiplierPresetDialog(UISettings.PresetDialog):
	HostNamespace = This.Mod.Namespace  # type: str
	HostName = This.Mod.Name  # type: str

	def _GetDescriptionValuesParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		valuesParts = super()._GetDescriptionValuesParts(setting)  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		settingValue = setting.Get(ignoreOverride = True)  # type: typing.Union[float, int]
		roundedSettingValue = round(settingValue, 6)  # type: typing.Union[float, int]

		def _AddSpeciesPart (species: sim_info_types.Species, speciesNamePart: localization.LocalizedString) -> None:
			if len(valuesParts) != 0:
				valuesParts.insert(0, "\n")

			speciesPart = self._GetDescriptionPartsLifeSpanText()  # type: localization.LocalizedString
			averageLifespan = int(ToolsLifeSpan.GetAverageLifeSpan(species))  # type: int
			adjustedLifespan = int(averageLifespan / settingValue)  # type: int
			Language.AddTokens(speciesPart, speciesNamePart, str(adjustedLifespan), str(averageLifespan), str(roundedSettingValue))
			valuesParts.insert(0, speciesPart)

		_AddSpeciesPart(sim_info_types.Species.DOG, self._GetDescriptionPartsLifeSpanDogText())
		_AddSpeciesPart(sim_info_types.Species.CAT, self._GetDescriptionPartsLifeSpanCatText())
		_AddSpeciesPart(sim_info_types.Species.HUMAN, self._GetDescriptionPartsLifeSpanHumanText())

		return valuesParts

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingStandardWrapper) -> typing.Optional[str]:
		return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

	def _GetDescriptionPartsLifeSpanText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span")

	def _GetDescriptionPartsLifeSpanHumanText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span.Human")

	def _GetDescriptionPartsLifeSpanCatText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span.Cat")

	def _GetDescriptionPartsLifeSpanDogText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span.Dog")

	def _GetRealTimeButtonText (self) -> localization.LocalizedString:  # TODO change to 365 days a year.
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Preset_Dialog.Real_Time_Button", fallbackText = "Real_Time_Button")

	def _GetYearLength112ButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Preset_Dialog.Year_Length_112_Button", fallbackText = "Year_Length_112_Button")

	def _GetDefaultButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Preset_Dialog.Default_Button", fallbackText = "Default_Button")

	# noinspection PyUnusedLocal
	def _CreateSetValueButtonCallback (self,
									   newValue: typing.Union[float, int],
									   setting: typing.Any,
									   currentValue: typing.Union[float, int],
									   showDialogArguments: typing.Dict[str, typing.Any],
									   returnCallback: typing.Callable[[], None] = None,
									   *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:
		# noinspection PyUnusedLocal
		def SetValueButtonCallback (dialog: ui_dialog.UiDialog) -> None:

			# noinspection PyUnusedLocal
			def SetValueButtonConfirmCallback (confirmDialog: ui_dialog.UiDialog) -> None:
				if confirmDialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
					setting.Set(newValue)
					self._ShowDialogInternal(setting, newValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)
				else:
					self._ShowDialogInternal(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)

			UISettings.ShowPresetConfirmDialog(SetValueButtonConfirmCallback)

		return SetValueButtonCallback

	def _CreateCustomizeButtonCallback (self,
										setting: typing.Any,
										currentValue: typing.Any,
										showDialogArguments: typing.Dict[str, typing.Any],
										returnCallback: typing.Callable[[], None] = None,
										*args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:
		# noinspection PyUnusedLocal
		def CustomizeButtonCallback (dialog: ui_dialog.UiDialog) -> None:
			# noinspection PyUnusedLocal
			def CustomizeDialogReturnCallback () -> None:
				self.ShowDialog(setting, returnCallback = returnCallback)

			settingValueDialog = setting.Setting.ValueDialog()  # type: UISettings.SettingDialogBase
			settingValueDialog.ShowDialog(setting, returnCallback = CustomizeDialogReturnCallback)

		return CustomizeButtonCallback

	def _CreateButtons (self,
						setting: UISettingsShared.SettingWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[UISettings.DialogButton]:

		buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[UISettings.DialogButton]

		settingValue = setting.Get(ignoreOverride = True)  # type: typing.Union[float, int]

		realTimeValue = 0.0032  # type: float
		realTimeSelected = False  # type: bool

		if realTimeValue == settingValue:
			realTimeSelected = True

		realTimeButtonArguments = {
			"responseID": 50000,
			"sortOrder": -500,
			"callback": self._CreateSetValueButtonCallback(realTimeValue, setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs),
			"text": self._GetRealTimeButtonText(),
			"selected": realTimeSelected
		}

		realTimeButton = UISettings.ChoiceDialogButton(**realTimeButtonArguments)
		buttons.append(realTimeButton)

		yearLength112Value = 0.0105  # type: float
		yearLength112Selected = False  # type: bool

		if yearLength112Value == settingValue:
			yearLength112Selected = True

		yearLength112ButtonArguments = {
			"responseID": 50001,
			"sortOrder": -499,
			"callback": self._CreateSetValueButtonCallback(yearLength112Value, setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs),
			"text": self._GetYearLength112ButtonText(),
			"selected": yearLength112Selected
		}

		yearLength112Button = UISettings.ChoiceDialogButton(**yearLength112ButtonArguments)
		buttons.append(yearLength112Button)

		defaultValue = setting.GetDefault()  # type: float
		defaultSelected = False  # type: bool

		if defaultValue == settingValue:
			defaultSelected = True

		defaultButtonArguments = {
			"responseID": 50100,
			"sortOrder": -400,
			"callback": self._CreateSetValueButtonCallback(defaultValue, setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs),
			"text": self._GetDefaultButtonText(),
			"selected": defaultSelected
		}

		defaultButton = UISettings.ChoiceDialogButton(**defaultButtonArguments)
		buttons.append(defaultButton)

		return buttons

class LifeSpanMultiplierValueDialog(SettingsDialogs.RealNumberDialog):
	def _GetDescriptionValuesParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		valuesParts = super()._GetDescriptionValuesParts(setting)  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		settingValue = setting.Get(ignoreOverride = True)  # type: typing.Union[float, int]
		roundedSettingValue = round(settingValue, 6)  # type: typing.Union[float, int]

		def _AddSpeciesPart (species: sim_info_types.Species, speciesNamePart: localization.LocalizedString) -> None:
			if len(valuesParts) != 0:
				valuesParts.insert(0, "\n")

			speciesPart = self._GetDescriptionPartsLifeSpanText()  # type: localization.LocalizedString
			averageLifespan = int(ToolsLifeSpan.GetAverageLifeSpan(species))  # type: int
			adjustedLifespan = int(averageLifespan / settingValue)  # type: int
			Language.AddTokens(speciesPart, speciesNamePart, str(adjustedLifespan), str(averageLifespan), str(roundedSettingValue))
			valuesParts.insert(0, speciesPart)

		_AddSpeciesPart(sim_info_types.Species.DOG, self._GetDescriptionPartsLifeSpanDogText())
		_AddSpeciesPart(sim_info_types.Species.CAT, self._GetDescriptionPartsLifeSpanCatText())
		_AddSpeciesPart(sim_info_types.Species.HUMAN, self._GetDescriptionPartsLifeSpanHumanText())

		return valuesParts

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingStandardWrapper) -> typing.Optional[str]:
		return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

	def _GetDescriptionPartsLifeSpanText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span")

	def _GetDescriptionPartsLifeSpanHumanText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span.Human")

	def _GetDescriptionPartsLifeSpanCatText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span.Cat")

	def _GetDescriptionPartsLifeSpanDogText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Life_Span_Multiplier.Description_Parts.Life_Span.Dog")

class LifeSpanMultiplierSetting(SettingsTypes.RealNumberSetting):
	@classmethod
	def Verify (cls, value: typing.Union[float, int], lastChangeVersion: Version.Version = None) -> typing.Union[float, int]:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if value <= 0:
			raise ValueError("Value must be greater than 0.")

		return value

class LifeSpanMultiplierDialogSetting(LifeSpanMultiplierSetting):
	Dialog = LifeSpanMultiplierPresetDialog
	ValueDialog = LifeSpanMultiplierValueDialog

class HandleLifeSpan(LifeSpanMultiplierDialogSetting):
	IsSetting = True  # type: bool

	Key = "Handle_Life_Span"  # type: str
	Default = 2.0  # type: float

	#ListPath = "Root/Time/Life_Span"  #TODO add back this line / setting dialogs shouldn't show a path if none of its settings are visible.
	ListPriority = 500

	Minimum = 0.0016  # type: float
	Maximum = 2  # type: float

	@classmethod
	def IsHidden(cls) -> bool: #TODO fix up the lifespan settings and remove this method.
		return True

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if not (cls.Minimum <= value <= cls.Maximum):
			raise ValueError("Value must be greater than '" + str(cls.Minimum) + "' and less than '" + str(cls.Maximum) + "'.")

		return value

class LifeSpanShortMultiplier(LifeSpanMultiplierDialogSetting):
	IsSetting = True  # type: bool

	Key = "Life_Span_Short_Multiplier"  # type: str
	Default = 2.0  # type: float

	#ListPath = "Root/Time/Life_Span" #TODO add back this line / setting dialogs shouldn't show a path if none of its settings are visible.
	ListPriority = 5

	Minimum = 0.0016  # type: float
	Maximum = 2  # type: float

	@classmethod
	def IsHidden(cls) -> bool: #TODO fix up the lifespan settings and remove this method.
		return True

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if not (cls.Minimum <= value <= cls.Maximum):
			raise ValueError("Value must be greater than '" + str(cls.Minimum) + "' and less than '" + str(cls.Maximum) + "'.")

		return value

class LifeSpanNormalMultiplier(LifeSpanMultiplierDialogSetting): # TODO make a setting that changes the game setting.
	IsSetting = True  # type: bool

	Key = "Life_Span_Normal_Multiplier"  # type: str
	Default = 1.0  # type: float

	#ListPath = "Root/Time/Life_Span" #TODO add back this line / setting dialogs shouldn't show a path if none of its settings are visible.
	ListPriority = 0

	Minimum = 0.0016  # type: float
	Maximum = 2  # type: float

	@classmethod
	def IsHidden(cls) -> bool: #TODO fix up the lifespan settings and remove this method.
		return True

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if not (cls.Minimum <= value <= cls.Maximum):
			raise ValueError("Value must be greater than '" + str(cls.Minimum) + "' and less than '" + str(cls.Maximum) + "'.")

		return value

class LifeSpanLongMultiplier(LifeSpanMultiplierDialogSetting):
	IsSetting = True  # type: bool

	Key = "Life_Span_Long_Multiplier"  # type: str
	Default = 0.25  # type: float

	#ListPath = "Root/Time/Life_Span" #TODO add back this line / setting dialogs shouldn't show a path if none of its settings are visible.
	ListPriority = -5

	Minimum = 0.0016  # type: float
	Maximum = 2  # type: float

	@classmethod
	def IsHidden(cls) -> bool: #TODO fix up the lifespan settings and remove this method.
		return True

	@classmethod
	def Verify (cls, value: float, lastChangeVersion: Version.Version = None) -> float:
		value = super().Verify(value, lastChangeVersion = lastChangeVersion)

		if not (cls.Minimum <= value <= cls.Maximum):
			raise ValueError("Value must be greater than '" + str(cls.Minimum) + "' and less than '" + str(cls.Maximum) + "'.")

		return value
