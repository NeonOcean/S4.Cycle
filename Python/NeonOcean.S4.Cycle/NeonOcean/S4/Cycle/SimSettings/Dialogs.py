from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Language, Websites
from NeonOcean.S4.Main.UI import Settings as UISettings, SettingsShared as UISettingsShared
from sims4 import localization
from ui import ui_dialog

class BooleanDialog(UISettings.StandardDialog):
	HostNamespace = This.Mod.Namespace  # type: str
	HostName = This.Mod.Name  # type: str

	Values = [True, False]  # type: typing.List[bool]

	def _GetDescriptionSettingText (self, setting: UISettingsShared.SettingStandardWrapper) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Sim_Settings.Values." + setting.Key + ".Description")

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingStandardWrapper) -> typing.Optional[str]:
		return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

	def _GetValueText (self, value: bool) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean." + str(value), fallbackText = str(value))

	def _CreateButtons (self,
						setting: UISettingsShared.SettingStandardWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs):

		buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[UISettings.DialogButton]

		for valueIndex in range(len(self.Values)):  # type: int
			def CreateValueButtonCallback (value: typing.Any) -> typing.Callable:

				# noinspection PyUnusedLocal
				def ValueButtonCallback (dialog: ui_dialog.UiDialog) -> None:
					self._ShowDialogInternal(setting, value, showDialogArguments, returnCallback = returnCallback)

				return ValueButtonCallback

			valueButtonArguments = {
				"responseID": 50000 + valueIndex * -5,
				"sortOrder": -(500 + valueIndex * -5),
				"callback": CreateValueButtonCallback(self.Values[valueIndex]),
				"text": self._GetValueText(self.Values[valueIndex]),
			}

			if currentValue == self.Values[valueIndex]:
				valueButtonArguments["selected"] = True

			valueButton = UISettings.ChoiceDialogButton(**valueButtonArguments)
			buttons.append(valueButton)

		return buttons

class BooleanEnabledDisabledDialog(BooleanDialog):
	def _GetValueText (self, value: bool) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Enabled_Disabled." + str(value), fallbackText = str(value))

class BooleanYesNoDialog(BooleanDialog):
	def _GetValueText (self, value: bool) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Yes_No." + str(value), fallbackText = str(value))
