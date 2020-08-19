from __future__ import annotations

import typing
import services

from NeonOcean.S4.Cycle import SimSettings, This
from NeonOcean.S4.Cycle.SimSettings import Base as SettingsBase
from NeonOcean.S4.Main import Language
from NeonOcean.S4.Main.UI import SettingsList as UISettingsList, SettingsShared as UISettingsShared
from sims4 import localization
from sims import sim_info

SettingsListRoot = "Root"  # type: str

class SettingsList(UISettingsList.SettingsList):
	TitleStandard = Language.String(This.Mod.Namespace + ".Sim_Settings.List.Title")  # type: Language.String

	def _GetTitleText (self, listPath: str) -> localization.LocalizedString:
		return self._GetTitleStandardText()

	def _GetTitleStandardText(self) -> localization.LocalizedString:
		return self.TitleStandard.GetLocalizationString()

	def _GetTitleListPathText (self, listPath: str) -> localization.LocalizedString:
		listPathIdentifier = listPath.replace(self.ListPathSeparator, "_")  # type: str
		fallbackText = "List.Paths." + listPathIdentifier + ".Title"  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Sim_Settings.List.Paths." + listPathIdentifier + ".Title", fallbackText = fallbackText)

	def _GetDescriptionText (self, listPath: str) -> localization.LocalizedString:
		listPathIdentifier = listPath.replace(self.ListPathSeparator, "_")  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Sim_Settings.List.Paths." + listPathIdentifier + ".Description")

def GetListDialogSettingsSystem (branch: str) -> UISettingsShared.SettingsSystemBranchWrapper:
	return UISettingsShared.SettingsSystemBranchWrapper(SettingsBase, GetListDialogSettings(branch), lambda *args, **kwargs: None, SettingsBase.Update)

def GetListDialogSettings (branch: str) -> typing.List[UISettingsShared.SettingBranchWrapper]:
	return [UISettingsShared.SettingBranchWrapper(setting, branch) for setting in SimSettings.GetAllSettings()]

def ShowListDialog (branch: str, returnCallback: typing.Callable[[], None] = None) -> None:
	"""
	Open the settings list dialog. A lot must be loaded or nothing will happen.
	:param branch: The branch this list dialog is opening for.
	:type branch: str
	:param returnCallback: The return callback will be triggered after the settings list dialog has completely closed.
	:type returnCallback: typing.Callable[[], None] | None
	"""

	dialogArguments = dict()  # type: typing.Dict[str, typing.Any]

	try:
		branchNumber = int(branch)  # type: int

		branchSimInfo = services.sim_info_manager().get(branchNumber)  # type: typing.Optional[sim_info.SimInfo]

		if branchSimInfo is not None:
			dialogArguments["owner"] = branchSimInfo
	except:
		pass

	settingsSystem = GetListDialogSettingsSystem(branch)  # type: UISettingsShared.SettingsSystemBranchWrapper
	settingsList = SettingsList(This.Mod.Namespace, settingsSystem)  # type: SettingsList
	settingsList.ShowDialog(SettingsListRoot, returnCallback = returnCallback, **dialogArguments)
