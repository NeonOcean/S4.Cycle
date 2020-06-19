from __future__ import annotations

import sys
import types
import typing

from NeonOcean.S4.Cycle import Debug, Saving, This
from NeonOcean.S4.Main import Debug, Language, LoadingShared
from NeonOcean.S4.Main.Abstract import Settings as AbstractSettings
from NeonOcean.S4.Main.Data import Persistence, PersistenceBranched
from NeonOcean.S4.Main.Tools import Events, Exceptions, Types, Version
from NeonOcean.S4.Main.UI import Settings as UISettings, SettingsShared as UISettingsShared
from sims4 import localization

SettingsPersistence = None  # type: typing.Optional[PersistenceBranched.PersistentBranchedSection]
DefaultSettings = None  # type: typing.Optional[Persistence.PersistentSection]

AllSettings = list()  # type: typing.List[typing.Type[Setting]]

_previousValues = dict()  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

_onUpdateWrapper = Events.EventHandler()  # type: Events.EventHandler
_onLoadWrapper = Events.EventHandler()  # type: Events.EventHandler

class UpdateEventArguments(Events.EventArguments):
	def __init__ (self, changedValues: typing.Dict[str, typing.Set[str]]):
		self.ChangedValues = changedValues  # type: typing.Dict[str, typing.Set[str]]

	def Changed (self, branch: str, key: str) -> bool:
		"""
		Get whether or not a value has been changed between the last update and this one.
		"""

		changedBranches = self.ChangedValues.get(key, None)  # type: typing.Optional[typing.Set[str]]

		if changedBranches is None:
			return False

		return branch in changedBranches

class Setting(AbstractSettings.SettingBranchedAbstract):
	IsSetting = False  # type: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Dialog: typing.Type[UISettings.SettingDialogBase]

	ListPath = "Root"  # type: str
	ListPriority = 0  # type: typing.Union[float, int]

	_overrides = None  # type: typing.Optional[typing.Dict[str, typing.List[_SettingOverride]]]
	_universalOverrides = None  # type: typing.Optional[typing.List[_SettingOverride]]

	def __init_subclass__ (cls, **kwargs):
		super().OnInitializeSubclass()

		if cls.IsSetting:
			cls.SetDefault()
			AllSettings.append(cls)

	@classmethod
	def Setup (cls) -> None:
		"""
		Setup this setting with the underlying persistence object.
		"""

		_Setup(cls.Key,
			   cls.Type,
			   cls.Default,
			   cls.Verify)

	@classmethod
	def IsSetup (cls) -> bool:
		return _isSetup(cls.Key)

	@classmethod
	def IsHidden (cls, simID: str) -> bool:
		"""
		Get whether or not this setting should be visible to the user.
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		return False

	@classmethod
	def Get (cls, simID: str, ignoreOverride: bool = False) -> typing.Any:
		"""
		Get the setting's value.
		:param simID: The ID of the sim who's setting value is requested.
		:type simID: str
		:param ignoreOverride: If true we will ignore any value overrides will be ignored when retrieving the value.
		:type ignoreOverride: bool
		:return: The setting's value.
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if not isinstance(ignoreOverride, bool):
			raise Exceptions.IncorrectTypeException(ignoreOverride, "ignoreOverride", (bool,))

		if ignoreOverride:
			return _Get(simID, cls.Key)

		if not cls.IsOverridden(simID):
			return _Get(simID, cls.Key)

		activeOverrideIdentifier = cls.GetActiveOverrideIdentifier(simID)  # type: str
		activeOverrideValue = cls.GetOverrideValue(activeOverrideIdentifier)  # type: typing.Any
		return activeOverrideValue

	@classmethod
	def GetAllBranches (cls, ignoreOverrides: bool = False) -> typing.Dict[str, typing.Any]:
		"""
		Get the setting's value in every active branch. Branches will not be active unless a value is saved to it.
		:param ignoreOverrides: If true we will ignore any value overrides will be ignored when retrieving the values.
		:return:
		"""

		if not isinstance(ignoreOverrides, bool):
			raise Exceptions.IncorrectTypeException(ignoreOverrides, "ignoreOverrides", (bool,))

		allBranches = cls.GetAllBranchIdentifiers()  # type: typing.Set[str]
		allValues = dict()  # type: typing.Dict[str, typing.Any]

		for branch in allBranches:  # type: str
			allValues[branch] = cls.Get(branch, ignoreOverride = ignoreOverrides)

		return allValues

	@classmethod
	def GetAllBranchIdentifiers (cls) -> typing.Set[str]:
		"""
		Get a set of all active branches in this setting. Branches will not be active unless a value is saved to it.
		:return:
		"""

		return SettingsPersistence.GetAllBranchIdentifiers(cls.Key)

	@classmethod
	def Set (cls, simID: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		Set the setting's value.
		:param simID: The ID of the sim who's setting value is being changed.
		:type simID: str
		:param value: The new setting value. An exception will be raised if this doesn't match the setting's type or has an incorrect
		value.
		:type value: typing.Any
		:param autoSave: If true we will automatically save changes to the save file.
		:type autoSave: bool
		:param autoUpdate: If true we will automatically trigger update callbacks.
		:type autoUpdate: bool
		"""

		return _Set(simID, cls.Key, value, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls, simID: str = None, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		Reset to the default value.
		"""

		_Reset(simID = simID, key = cls.Key, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion: Version.Version = None) -> typing.Any:
		"""
		Check whether a value is valid. This method should return the value if it is correct, return a corrected version, or raise
		an exception if the value cannot reasonably be fixed.
		:param value: A value to be verified.
		:type value: typing.Any
		:param lastChangeVersion: The last version of the mod that the value was checked.
		:type lastChangeVersion: Version.Version
		:return: The input value or a corrected version of it.
		:rtype: typing.Any
		"""

		return value

	@classmethod
	def Override (cls, simID: str, value: typing.Any, overrideIdentifier: str, overridePriority: typing.Union[float, int],
				  overrideReasonText: typing.Optional[typing.Callable[[], localization.LocalizedString]] = None) -> None:
		"""
		Create a branch override, forcing this setting to take on a value temporarily. The setting must be setup before this method can be called.
		:param simID: The ID of the sim who's setting value is being overridden.
		:type simID: str
		:param value: The value forced onto the setting, this must be able to pass the verify method's tests.
		:type value: typing.Any
		:param overrideIdentifier: A unique identifier for this override. This needs to be unique within this setting, no two branch or universal
		overrides can share an identifier.
		:type overrideIdentifier: str
		:param overridePriority: The priority of this override. If multiple overrides are imposed on this setting at once the one with the
		highest priority will be active.
		:type overridePriority: float | int
		:param overrideReasonText: A function that will return a sims 4 localization string explaining to the player why this setting cannot
		be changed.
		:type overrideReasonText: typing.Optional[typing.Callable[[], localization.LocalizedString]]
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if not isinstance(value, cls.Type):
			raise Exceptions.IncorrectTypeException(value, "value", (cls.Type,))

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if not isinstance(overridePriority, (float, int)):
			raise Exceptions.IncorrectTypeException(overridePriority, "overridePriority", (float, int))

		if not isinstance(overrideReasonText, typing.Callable) and overrideReasonText is not None:
			raise Exceptions.IncorrectTypeException(overrideReasonText, "reasonText", ("Callable", None))

		if not cls.IsSetup():
			raise Exception("Cannot override the non setup setting '%s'." % cls.Key)

		value = cls.Verify(value)

		if cls._overrides is None:
			cls._overrides = dict()

		if cls._universalOverrides is not None:
			if any(universalOverride.Identifier == overrideIdentifier for universalOverride in cls._universalOverrides):
				raise Exception("The identifier '" + overrideIdentifier + "' has already been taken by a universal override.")

		for testingBranch, testingOverrides in cls._overrides.items():  # type: str, typing.List[_SettingOverride]
			for testingOverride in testingOverrides:  # type: _SettingOverride
				if testingOverride.Identifier == overrideIdentifier:
					raise Exception("The identifier '" + overrideIdentifier + "' has already been taken by a override for the branch '" + testingBranch + "'.")

		if not simID in cls._overrides:
			branchOverrides = list()  # type: typing.List[_SettingOverride]

			cls._overrides[simID] = branchOverrides
			branchOverrides.append(_SettingOverride(value, overrideIdentifier, overridePriority, overrideReasonText))
		else:
			branchOverrides = cls._overrides[simID]  # type: typing.List[_SettingOverride]
			branchOverrides.append(_SettingOverride(value, overrideIdentifier, overridePriority, overrideReasonText))

		branchOverrides.sort(key = lambda sortingOverride: sortingOverride.Priority, reverse = True)
		Update()

	@classmethod
	def OverrideAll (cls, value: typing.Any, overrideIdentifier: str, overridePriority: typing.Union[float, int],
					 overrideReasonText: typing.Optional[typing.Callable[[], localization.LocalizedString]] = None) -> None:

		"""
		Create a universal override, forcing all branches of this setting to take on a value temporarily. The setting must be setup before
		this method can be called.
		:param value: The value forced onto the setting, this must be able to pass the verify method's tests.
		:type value: typing.Any
		:param overrideIdentifier: A unique identifier for this override. This needs to be unique within this setting, no two branch or universal
		overrides can share an identifier.
		:type overrideIdentifier: str
		:param overridePriority: The priority of this override. If multiple overrides are imposed on this setting at once the one with the
		highest priority will be active.
		:type overridePriority: float | int
		:param overrideReasonText: A function that will return a sims 4 localization string explaining to the player why this setting cannot
		be changed.
		:type overrideReasonText: typing.Optional[typing.Callable[[], localization.LocalizedString]]
		"""

		if not isinstance(value, cls.Type):
			raise Exceptions.IncorrectTypeException(value, "value", (cls.Type,))

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if not isinstance(overridePriority, (float, int)):
			raise Exceptions.IncorrectTypeException(overridePriority, "overridePriority", (float, int))

		if not isinstance(overrideReasonText, typing.Callable) and overrideReasonText is not None:
			raise Exceptions.IncorrectTypeException(overrideReasonText, "reasonText", ("Callable", None))

		if not cls.IsSetup():
			raise Exception("Cannot override the non setup setting '%s'." % cls.Key)

		value = cls.Verify(value)

		if cls._universalOverrides is None:
			cls._universalOverrides = list()

		if any(universalOverride.Identifier == overrideIdentifier for universalOverride in cls._universalOverrides):
			raise Exception("The identifier '" + overrideIdentifier + "' has already been taken by a universal override.")

		if cls._overrides is not None:
			for testingBranch, testingOverrides in cls._overrides.items():  # type: str, typing.List[_SettingOverride]
				for testingOverride in testingOverrides:  # type: _SettingOverride
					if testingOverride.Identifier == overrideIdentifier:
						raise Exception("The identifier '" + overrideIdentifier + "' has already been taken by a override for the branch '" + testingBranch + "'.")

		cls._universalOverrides.append(_SettingOverride(value, overrideIdentifier, overridePriority, overrideReasonText))
		cls._universalOverrides.sort(key = lambda sortingOverride: sortingOverride.Priority, reverse = True)
		Update()

	@classmethod
	def RemoveOverride (cls, overrideIdentifier: str) -> None:
		"""
		Deactivate an override. If no such override is set nothing will happen. The setting must be setup before this method can be called.
		:param overrideIdentifier: The identifier given to the override to be removed.
		:type overrideIdentifier: str
		"""

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if not cls.IsSetup():
			raise Exception("Cannot remove override of the non setup setting '%s'." % cls.Key)

		if cls._overrides is not None:
			for testingBranch, testingBranchOverrides in cls._overrides.items():  # type: str, typing.List[_SettingOverride]
				for testingBranchOverrideIndex in range(len(testingBranchOverrides)):  # type: int
					testingBranchOverride = testingBranchOverrides[testingBranchOverrideIndex]  # type: _SettingOverride

					if testingBranchOverride.Identifier == overrideIdentifier:
						testingBranchOverrides.pop(testingBranchOverrideIndex)
						Update()
						return

		if cls._universalOverrides is not None:
			for testingUniversalOverrideIndex in range(len(cls._universalOverrides)):  # type: int
				testingUniversalOverride = cls._universalOverrides[testingUniversalOverrideIndex]  # type: _SettingOverride

				if testingUniversalOverride.Identifier == overrideIdentifier:
					cls._universalOverrides.pop(testingUniversalOverrideIndex)
					Update()
					return

	@classmethod
	def ClearAllOverrides (cls) -> None:
		"""
		Clear all set overrides.
		"""

		cls._overrides = None
		cls._universalOverrides = None

	@classmethod
	def IsOverridden (cls, simID: str) -> bool:
		"""
		Whether or not this setting's value is overridden.
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if cls._overrides is None and cls._universalOverrides is None:
			return False

		if len(cls._overrides) == 0 and len(cls._universalOverrides) == 0:
			return False

		return True

	@classmethod
	def IsOverriddenBy (cls, simID: str, overrideIdentifier: str) -> bool:
		"""
		Whether or not this sim's setting has an override with this identifier.
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if not cls.IsOverridden(simID):
			return False

		if cls._overrides is not None:
			for branchOverrides in cls._overrides.values():  # type: typing.List[_SettingOverride]
				for branchOverride in branchOverrides:  # type: _SettingOverride
					if branchOverride.Identifier == overrideIdentifier:
						return True

		if cls._universalOverrides is not None:
			for universalOverride in cls._universalOverrides:
				if universalOverride.Identifier == overrideIdentifier:
					return True

		return False

	@classmethod
	def GetActiveOverrideIdentifier (cls, simID: str) -> str:
		"""
		Get the active override's identifier. An exception will be raised if no override is active.
		:param simID: The ID of the sim who's override we are looking for.
		:type simID: str
		:return: The active override's identifier.
		:rtype: str
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if not cls.IsOverridden(simID):
			raise Exception("No overrides exist for the setting '" + cls.Key + "' and branch '" + simID + "'.")

		branchOverrideCandidate = None  # type: typing.Optional[_SettingOverride]
		universalOverrideCandidate = None  # type: typing.Optional[_SettingOverride]

		if cls._overrides is not None and simID in cls._overrides:
			branchOverrides = cls._overrides[simID]  # type: typing.List[_SettingOverride]

			if len(branchOverrides) != 0:
				branchOverrideCandidate = cls._overrides[simID][0]

		if cls._universalOverrides is not None and len(cls._universalOverrides) != 0:
			universalOverrideCandidate = cls._universalOverrides[0]

		if branchOverrideCandidate is None and universalOverrideCandidate is None:
			raise Exception("The 'IsOverride' method signaled true but we failed to find a valid override.")

		if branchOverrideCandidate is None:
			return universalOverrideCandidate.Identifier
		elif universalOverrideCandidate is None:
			return branchOverrideCandidate.Identifier

		if branchOverrideCandidate.Priority >= universalOverrideCandidate.Priority:
			return branchOverrideCandidate.Identifier
		else:
			return universalOverrideCandidate.Identifier

	@classmethod
	def GetAllOverrideIdentifiers (cls) -> typing.Set[str]:
		"""
		Get the identifier of all registered overrides in this setting as a set.
		"""

		allIdentifiers = set()  # type: typing.Set[str]

		if cls._overrides is not None:
			for branchOverrides in cls._overrides.values():  # type: typing.List[_SettingOverride]
				for branchOverride in branchOverrides:  # type: _SettingOverride
					allIdentifiers.add(branchOverride.Identifier)

		if cls._universalOverrides is not None:
			for universalOverride in cls._universalOverrides:  # type: _SettingOverride
				allIdentifiers.add(universalOverride.Identifier)

		return allIdentifiers

	@classmethod
	def GetOverrideValue (cls, overrideIdentifier: str) -> typing.Any:
		"""
		Get the value of the targeted override. An exception will be raised if no such override is set.
		:param overrideIdentifier: The identifier of the targeted override.
		:type overrideIdentifier: str
		:return: The value of the override specified.
		:rtype: str
		"""

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if cls._overrides is not None:
			for branchOverrides in cls._overrides.values():  # type: typing.List[_SettingOverride]
				for branchOverride in branchOverrides:  # type: _SettingOverride
					if branchOverride.Identifier == overrideIdentifier:
						return branchOverride.Value

		if cls._universalOverrides is not None:
			for universalOverride in cls._universalOverrides:
				if universalOverride.Identifier == overrideIdentifier:
					return universalOverride.Value

		raise Exception("No override with the identifier '" + overrideIdentifier + "' in the setting '" + cls.Key + "'.")

	@classmethod
	def GetOverridePriority (cls, overrideIdentifier: str) -> typing.Union[float, int]:
		"""
		Get the priority of the targeted override. An exception will be raised if no such override is set.
		:param overrideIdentifier: The identifier of the targeted override.
		:type overrideIdentifier: str
		:return: The priority of the override specified.
		:rtype: float | int
		"""

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if cls._overrides is not None:
			for branchOverrides in cls._overrides.values():  # type: typing.List[_SettingOverride]
				for branchOverride in branchOverrides:  # type: _SettingOverride
					if branchOverride.Identifier == overrideIdentifier:
						return branchOverride.Priority

		if cls._universalOverrides is not None:
			for universalOverride in cls._universalOverrides:
				if universalOverride.Identifier == overrideIdentifier:
					return universalOverride.Priority

		raise Exception("No override with the identifier '" + overrideIdentifier + "' in the setting '" + cls.Key + "'.")

	@classmethod
	def GetOverrideReasonText (cls, overrideIdentifier: str) -> typing.Callable[[], localization.LocalizedString]:
		"""
		Get the reason text of the targeted override. An exception will be raised if no such override is set.
		:param overrideIdentifier: The identifier of the targeted override.
		:type overrideIdentifier: str
		:return: The reason text function of the override specified.
		:rtype: typing.Callable[[], localization.LocalizedString]
		"""

		if not isinstance(overrideIdentifier, str):
			raise Exceptions.IncorrectTypeException(overrideIdentifier, "overrideIdentifier", (str,))

		if cls._overrides is not None:
			for branchOverrides in cls._overrides.values():  # type: typing.List[_SettingOverride]
				for branchOverride in branchOverrides:  # type: _SettingOverride
					if branchOverride.Identifier == overrideIdentifier:
						return branchOverride.ReasonText

		if cls._universalOverrides is not None:
			for universalOverride in cls._universalOverrides:
				if universalOverride.Identifier == overrideIdentifier:
					return universalOverride.ReasonText

		raise Exception("No override with the identifier '" + overrideIdentifier + "' in the setting '" + cls.Key + "'.")

	@classmethod
	def CanShowDialog (cls, simID: str) -> bool:
		"""
		Get whether or not this setting can show a dialog to change it.
		:param simID: The ID of the sim who's setting value the dialog would be changing.
		:type simID: str
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if not hasattr(cls, "Dialog"):
			return False

		return True

	@classmethod
	def ShowDialog (cls, simID: str, returnCallback: typing.Callable[[], None] = None) -> None:
		"""
		Show the dialog to change this setting.
		:param simID: The ID of the sim who's setting value the dialog would be changing.
		:type simID: str
		:param returnCallback: The return callback will be triggered after the setting dialog is closed.
		:type returnCallback: typing.Callable[[], None]
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		if not isinstance(returnCallback, typing.Callable) and returnCallback is not None:
			raise Exceptions.IncorrectTypeException(returnCallback, "returnCallback", ("Callable", None))

		if not hasattr(cls, "Dialog"):
			return

		if cls.Dialog is None:
			return

		settingWrapper = UISettingsShared.SettingBranchWrapper(cls, simID)  # type: UISettingsShared.SettingBranchWrapper
		settingDialog = cls.Dialog()  # type: UISettings.SettingDialogBase
		settingDialog.ShowDialog(settingWrapper, returnCallback = returnCallback)

	@classmethod
	def GetNameText (cls) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Sim_Settings.Values." + cls.Key + ".Name", fallbackText = cls.Key)

	@classmethod
	def GetDescriptionText (cls) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Sim_Settings.Values." + cls.Key + ".Description")

	@classmethod
	def GetDefaultText (cls) -> localization.LocalizedString:
		return Language.CreateLocalizationString("**")

	@classmethod
	def GetValueText (cls, branch: str) -> localization.LocalizedString:
		return Language.CreateLocalizationString("**")

	@classmethod
	def GetSettingIconKey (cls, branch: str) -> typing.Optional[str]:
		return None

	@classmethod
	def _OnLoad (cls) -> None:
		pass

class _SettingOverride:
	def __init__ (self,
				  value: typing.Any,
				  identifier: str,
				  priority: typing.Union[float, int],
				  reasonText: typing.Optional[typing.Callable[[], localization.LocalizedString]] = None):

		self.Value = value  # type: typing.Any
		self.Identifier = identifier  # type: str
		self.Priority = priority  # type: typing.Union[float, int]

		if reasonText is not None:
			self.ReasonText = reasonText  # type: typing.Callable[[], localization.LocalizedString]
		else:
			self.ReasonText = lambda *args, **kwargs: Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Misc.Override.Unknown_Reason")  # type: typing.Callable[[], localization.LocalizedString]

def GetAllSettings () -> typing.List[typing.Type[Setting]]:
	return list(AllSettings)

def Update () -> None:
	SettingsPersistence.Update()

def RegisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, UpdateEventArguments], None]) -> None:
	global _onUpdateWrapper
	_onUpdateWrapper += updateCallback

def UnregisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, UpdateEventArguments], None]) -> None:
	global _onUpdateWrapper
	_onUpdateWrapper -= updateCallback

def RegisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	global _onLoadWrapper
	_onLoadWrapper += loadCallback

def UnregisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	global _onLoadWrapper
	_onLoadWrapper -= loadCallback

def _OnInitiate (cause: LoadingShared.LoadingCauses) -> None:
	global SettingsPersistence, DefaultSettings

	if cause:
		pass

	if SettingsPersistence is None:
		SettingsPersistence = PersistenceBranched.PersistentBranchedSection(Saving.GetSimsSection(), "Settings", This.Mod.Version, hostNamespace = This.Mod.Namespace)
		DefaultSettings = Persistence.PersistentSection(Saving.GetAllSimsSection(), "DefaultSettings", This.Mod.Version, hostNamespace = This.Mod.Namespace)

		for setting in AllSettings:
			setting.Setup()

		SettingsPersistence.OnUpdate += _OnUpdateCallback
		SettingsPersistence.OnLoad += _OnLoadCallback

def _OnReset () -> None:
	for setting in GetAllSettings():  # type: Setting
		setting.Reset()

def _OnResetSettings () -> None:
	for setting in GetAllSettings():  # type: Setting
		setting.Reset()

def _Setup (key: str, valueType: type, default, verify: typing.Callable) -> None:
	SettingsPersistence.Setup(key, valueType, default, verify)
	DefaultSettings.Setup(key, valueType, default, verify)

def _isSetup (key: str) -> bool:
	if SettingsPersistence is None:
		return False

	return SettingsPersistence.IsSetup(key)

def _isDefaultSetup (key: str) -> bool:
	return SettingsPersistence.IsSetup(key)

def _Get (simID: str, key: str) -> typing.Any:  # TODO make versions of these for the default settings. / Draw from the default settings if its not set in the regular.
	return SettingsPersistence.Get(simID, key)

def _Set (simID: str, key: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
	SettingsPersistence.Set(simID, key, value, autoSave = autoSave, autoUpdate = autoUpdate)

def _Reset (simID: str = None, key: str = None, autoSave: bool = True, autoUpdate: bool = True) -> None:
	SettingsPersistence.Reset(branch = simID, key = key, autoSave = autoSave, autoUpdate = autoUpdate)

def _InvokeOnUpdateWrapperEvent (changedSettings: typing.Dict[str, typing.Set[str]]) -> UpdateEventArguments:
	updateEventArguments = UpdateEventArguments(changedSettings)  # type: UpdateEventArguments

	for updateCallback in _onUpdateWrapper:  # type: typing.Callable[[types.ModuleType, Events.EventArguments], None]
		try:
			updateCallback(sys.modules[__name__], updateEventArguments)
		except:
			Debug.Log("Failed to run the 'OnUpdateWrapper' callback '" + Types.GetFullName(updateCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return updateEventArguments

def _InvokeOnLoadWrapperEvent () -> Events.EventArguments:
	eventArguments = Events.EventArguments()  # type: Events.EventArguments

	for updateCallback in _onUpdateWrapper:  # type: typing.Callable[[types.ModuleType, Events.EventArguments], None]
		try:
			updateCallback(sys.modules[__name__], eventArguments)
		except:
			Debug.Log("Failed to run the 'OnLoadWrapper' callback '" + Types.GetFullName(updateCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return eventArguments

# noinspection PyUnusedLocal
def _OnUpdateCallback (owner: Persistence.Persistent, eventArguments: Events.EventArguments) -> None:
	global _previousValues

	allSettings = GetAllSettings()  # type: typing.List[typing.Type[Setting]]

	currentValues = dict()  # type: typing.Dict[str, typing.Dict[str, typing.Any]]
	changedSettings = dict()  # type: typing.Dict[str, typing.Set[str]]

	for setting in allSettings:  # type: typing.Type[Setting]
		settingValues = setting.GetAllBranches()  # type: typing.Dict[str, typing.Any]
		currentValues[setting.Key] = settingValues

		if not setting.Key in _previousValues:
			settingAllBranches = setting.GetAllBranchIdentifiers()  # type: typing.Set[str]
			changedSettings[setting.Key] = settingAllBranches
			continue

		changedBranches = set()  # type: typing.Set[str]

		settingPreviousValues = _previousValues[setting.Key]  # type: typing.Dict[str, typing.Any]

		for settingBranch, settingValue in settingValues.items():  # type: str, typing.Any
			if settingBranch not in settingPreviousValues:
				changedBranches.add(settingBranch)
				continue

			if settingValue != settingPreviousValues[settingBranch]:
				changedBranches.add(setting.Key)
				continue

		for settingPreviousBranch, settingPreviousValue in settingPreviousValues.items():  # type: str, typing.Any
			if settingPreviousBranch not in settingValues:
				changedBranches.add(settingPreviousBranch)
				continue

		changedSettings[setting.Key] = changedBranches

	_previousValues = currentValues

	_InvokeOnUpdateWrapperEvent(changedSettings)

# noinspection PyUnusedLocal
def _OnLoadCallback (owner: Persistence.Persistent, eventArguments: Events.EventArguments) -> None:
	for setting in AllSettings:  # type: Setting
		try:
			# noinspection PyProtectedMember
			setting._OnLoad()
		except Exception:
			Debug.Log("Failed to notify the setting '" + setting.Key + "' of a load event.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	_InvokeOnLoadWrapperEvent()
