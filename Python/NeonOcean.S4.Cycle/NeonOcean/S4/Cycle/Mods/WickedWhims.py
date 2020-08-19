from __future__ import annotations

import collections
import sys
import typing

import services
from NeonOcean.S4.Cycle import Insemination, SimSettings, This
from NeonOcean.S4.Cycle.Interactions import CondomBox as InteractionsCondomBox
from NeonOcean.S4.Cycle.Safety import BirthControlPills as SafetyBirthControlPills, Resources as SafetyResources
from NeonOcean.S4.Main import Debug, Director, Language
from NeonOcean.S4.Main.Interactions.Support import DisableInteraction
from NeonOcean.S4.Main.Tools import Exceptions, Patcher, Python
from event_testing import results
from objects import script_object
from objects.components import inventory as ComponentsInventory, types as ComponentsTypes
from sims import sim, sim_info
from sims4 import resources
from sims4.tuning import instance_manager

"""
If your the creator of wicked whims - NeonOceanCreations@gmail.com - It might be better if you do some of these patches.
"""

DisabledBecauseWickedWhimsInstalledToolTip = Language.String(This.Mod.Namespace + ".Mods.WickedWhims.Disabled_Because_Installed_Tooltip")  # type: Language.String
DisabledBecauseCycleInstalledToolTip = Language.String(This.Mod.Namespace + ".Mods.Cycle.Disabled_Because_Installed_Tooltip")  # type: Language.String

WickedWhimsBirthControlPillsObjectID = 11109047836475721558  # type: int
WickedWhimsCheckCyclesInfoInteractionID = 9855519195140041011  # type: int

class _Announcer(Director.Announcer):
	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager) -> None:
		if instanceManager.TYPE != resources.Types.INTERACTION:
			return

		if ModInstalled() and WickedWhimsPatchEnabled("CheckCyclesInfo"):
			_DoWickedWhimsCheckCyclesInfoPatch()

def ModInstalled () -> bool:
	# noinspection SpellCheckingInspection
	if "wickedwhims" in sys.modules:
		return True
	else:
		try:
			# noinspection PyUnresolvedReferences
			import wickedwhims
			return True
		except ModuleNotFoundError:
			return False

def GetWickedWhimsDisablingWickedWhimsPatches () -> typing.Iterable[str]:
	"""
	Get the patches that Cycle would normally do to WickedWhims, except that WickedWhims is indicating should be skipped.
	"""

	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.main.game_handlers.neonocean.cycle import patches as WickedWhimsCyclePatches
	except ModuleNotFoundError:
		return list()

	disabledWickedWhimsPatches = WickedWhimsCyclePatches.get_wicked_whims_disabling_wicked_whims_patches()

	if not iter(disabledWickedWhimsPatches):
		raise Exceptions.IncorrectReturnTypeException(disabledWickedWhimsPatches, "get_wicked_whims_disabling_wicked_whims_patches", (collections.Iterable,))

	return disabledWickedWhimsPatches

def GetWickedWhimsDisablingCyclePatches () -> typing.Iterable[str]:
	"""
	Get the patches that Cycle would normally do to Cycle (if WickedWhims is installed), except that WickedWhims is indicating should be skipped.
	"""

	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.main.game_handlers.neonocean.cycle import patches as WickedWhimsCyclePatches
	except ModuleNotFoundError:
		return list()

	disabledCyclePatches = WickedWhimsCyclePatches.get_wicked_whims_disabling_cycle_patches()  # type: typing.Iterable[str]

	if not iter(disabledCyclePatches):
		raise Exceptions.IncorrectReturnTypeException(disabledCyclePatches, "get_wicked_whims_disabling_cycle_patches", (collections.Iterable,))

	return disabledCyclePatches

def GetCycleDisablingCyclePatches () -> typing.Iterable[str]:
	"""
	Get the patches that WickedWhims would normally do to Cycle, except that Cycle is indicating should be skipped.
	"""

	return list()

def GetCycleDisablingWickedWhimsPatches () -> list:
	"""
	Get the patches that WickedWhims would normally do to WickedWhims (if Cycle is installed), except that Cycle is indicating should be skipped.
	"""

	return list()

def CyclePatchEnabled (patchIdentifier: str) -> bool:
	"""
	Get whether a patch with this identifier is allowed by WickedWhims.
	"""

	return patchIdentifier not in GetWickedWhimsDisablingCyclePatches()

def WickedWhimsPatchEnabled (patchIdentifier: str) -> bool:
	"""
	Get whether a patch with this identifier is allowed by WickedWhims.
	"""

	return patchIdentifier not in GetWickedWhimsDisablingWickedWhimsPatches()

# noinspection PyUnusedLocal
def _OnStart (cause) -> None:
	if ModInstalled():
		_DoAppropriatePatches()

def _DoAppropriatePatches () -> None:
	try:
		disabledCyclePatches = GetWickedWhimsDisablingCyclePatches()  # type: typing.Iterable[str]
	except:
		Debug.Log("Failed to get the Cycle patches that WickedWhims wants to be disabled.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		disabledCyclePatches = list()

	try:
		disabledWickedWhimsPatches = GetWickedWhimsDisablingWickedWhimsPatches()  # type: typing.Iterable[str]
	except:
		Debug.Log("Failed to get the WickedWhims patches that WickedWhims wants to be disabled.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		disabledWickedWhimsPatches = list()

	for cyclePatchIdentifier, cyclePatcher in CyclePatches.items():  # type: str, typing.Optional[typing.Callable]
		if cyclePatcher is None:
			continue

		if cyclePatchIdentifier in disabledCyclePatches:
			continue

		cyclePatcher()

	for wickedWhimsPatchIdentifier, wickedWhimsPatcher in WickedWhimsPatches.items():  # type: str, typing.Optional[typing.Callable]
		if wickedWhimsPatcher is None:
			continue

		if wickedWhimsPatchIdentifier in disabledWickedWhimsPatches:
			continue

		wickedWhimsPatcher()

def _DoCycleResetCondomMethodUseSettingPatch () -> None:
	try:

		for simIDString, woohooSafetyMethodUse in SimSettings.WoohooSafetyMethodUse.GetAllBranches():  # type: str, typing.Dict[str, bool]
			woohooSafetyMethodUse.pop(str(SafetyResources.CondomWoohooSafetyMethodID))

			SimSettings.WoohooSafetyMethodUse.Set(simIDString, woohooSafetyMethodUse, autoSave = False, autoUpdate = False)

		SimSettings.Update()
	except:
		Debug.Log("Could not complete Cycle reset condom method use setting patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoCycleDisableCondomMethodUseChangePatch () -> None:
	try:
		InteractionsCondomBox.StartUsingInteraction.add_additional_test(DisableInteraction.DisabledInteractionTest(reasonToolTip = DisabledBecauseWickedWhimsInstalledToolTip))
		InteractionsCondomBox.StopUsingInteraction.add_additional_test(DisableInteraction.DisabledInteractionTest(reasonToolTip = DisabledBecauseWickedWhimsInstalledToolTip))
	except:
		Debug.Log("Could not complete Cycle disable condom method use change patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoCycleFindValidPillsObjectPatch () -> None:
	try:
		Patcher.Patch(SafetyBirthControlPills, "FindValidPillsObject", _CycleFindValidPillsObjectPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete Cycle find valid pills object patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoCycleGetPillsLeftInObjectPatch () -> None:
	try:
		Patcher.Patch(SafetyBirthControlPills, "GetPillsLeftInObject", _CycleGetPillsLeftInObjectPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete Cycle get pills left in object patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoCycleRemovePillFromObjectPatch () -> None:
	try:
		Patcher.Patch(SafetyBirthControlPills, "RemovePillFromObject", _CycleRemovePillFromObjectPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete Cycle remove pill from object patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsImpregnationPatch () -> None:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.integral.sex_handlers.active_sex.helpers import pregnancy as WickedWhimsPregnancy
		Patcher.Patch(WickedWhimsPregnancy.SexInstancePregnancyHelper, "_try_impregnate_sim", _WickedWhimsTryImpregnateSimPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims impregnation patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsMenstruationPatch () -> None:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex import sex_settings as WickedWhimsSexSettings
		Patcher.Patch(WickedWhimsSexSettings, "update_sex_settings_to_general_save_data", _WickedWhimsUpdateSexSettingsToGeneralSaveDataPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims menstruation patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsTakeBirthControlPillPatch () -> None:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import pills
		Patcher.Patch(pills, "take_birth_control_pill", _WickedWhimsTakeBirthControlPillPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims take birth control pill patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsTakeBirthControlPillInteractionTestPatch () -> None:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import interactions
		Patcher.Patch(interactions.TakeBirthControlPillInteraction, "on_interaction_test", _WickedWhimsTakeBirthControlPillInteractionTestPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims take birth control pill interaction test patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsAllowBirthControlPillsAutoUseInteractionTestPatch () -> None:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import interactions
		Patcher.Patch(interactions.AllowBirthControlPillsAutoUseInteraction, "on_interaction_test", _WickedWhimsAllowBirthControlPillsAutoUseInteractionTestPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims allow birth control pills auto use interaction test patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsDisallowBirthControlPillsAutoUseInteractionTestPatch () -> None:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import interactions
		Patcher.Patch(interactions.DisallowBirthControlPillsAutoUseInteraction, "on_interaction_test", _WickedWhimsDisallowBirthControlPillsAutoUseInteractionTestPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims disallow birth control pills auto use interaction test patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _DoWickedWhimsCheckCyclesInfoPatch () -> None:
	try:
		interactionManager = services.get_instance_manager(resources.Types.INTERACTION)
		checkCyclesInfoInteraction = interactionManager.get(WickedWhimsCheckCyclesInfoInteractionID)

		checkCyclesInfoInteraction.add_additional_test(DisableInteraction.DisabledInteractionTest(reasonToolTip = DisabledBecauseCycleInstalledToolTip.GetCallableLocalizationString()))
	except:
		Debug.Log("Could not complete WickedWhims check cycles info interaction patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _CycleFindValidPillsObjectPatch (originalCallable: typing.Callable, targetSim: sim.Sim) -> typing.Optional[script_object.ScriptObject]:
	foundPillsObject = originalCallable(targetSim)  # type: typing.Optional[script_object.ScriptObject]

	if foundPillsObject is not None:
		return foundPillsObject

	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import pills

		inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent

		for inventoryObject in inventoryComponent:  # type: script_object.ScriptObject
			if inventoryObject.definition is None:
				continue

			if inventoryObject.definition.id == pills.BIRTH_CONTROL_PILL_OBJECT_ID:
				return inventoryObject

		return foundPillsObject
	except:
		Debug.Log("Failed to handle Cycle's find valid pills object method.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return foundPillsObject

def _CycleGetPillsLeftInObjectPatch (originalCallable: typing.Callable, pillsObject: script_object.ScriptObject) -> typing.Optional[int]:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import pills

		if pillsObject.definition is not None:
			if pillsObject.definition.id == pills.BIRTH_CONTROL_PILL_OBJECT_ID:
				return 1
	except:
		Debug.Log("Failed to handle Cycle's find valid pills object method.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	return originalCallable(pillsObject)

def _CycleRemovePillFromObjectPatch (originalCallable: typing.Callable, pillsObject: script_object.ScriptObject) -> bool:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex.pregnancy.birth_control import pills

		if pillsObject.definition is not None:
			if pillsObject.definition.id == pills.BIRTH_CONTROL_PILL_OBJECT_ID:
				pillsObjectContainingInventory = pillsObject.get_inventory()  # type: typing.Optional[ComponentsInventory.InventoryComponent]

				if pillsObjectContainingInventory is not None:
					return pillsObjectContainingInventory.try_destroy_object(pillsObject)
				else:
					pillsObject.destroy()

				return True
	except:
		Debug.Log("Failed to handle Cycle's remove pill from object method.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	return originalCallable(pillsObject)

def _WickedWhimsTryImpregnateSimPatch (originalCallable: typing.Callable, self, sim_actor_id, turbo_sim, *args, **kwargs) -> bool:
	try:
		# noinspection PyUnresolvedReferences
		from turbolib2.wrappers.sim import sim as TurboSimWrapper

		inseminatedSimInfo = turbo_sim.get_sim_info()  # type: typing.Optional[sim_info.SimInfo]

		if inseminatedSimInfo is None:
			return False

		for sourceSimID, spermArriving in self._get_possible_partners(sim_actor_id, turbo_sim):  # type: int, bool
			if not spermArriving:
				return False

			sourceSimInfo = services.sim_info_manager().get(sourceSimID)  # type: typing.Optional[sim_info.SimInfo]

			if sourceSimInfo is None:
				continue

			sourceSimWickedWhimsWrapper = TurboSimWrapper.TurboSim(sourceSimInfo)

			if self._is_sim_on_birth_control(sourceSimWickedWhimsWrapper):
				continue

			Insemination.AutoInseminate(inseminatedSimInfo, sourceSimInfo)
	except:
		Debug.Log("Failed to handle WickedWhim's try impregnate sim method.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(self, sim_actor_id, turbo_sim, *args, **kwargs)

def _WickedWhimsUpdateSexSettingsToGeneralSaveDataPatch (originalCallable: typing.Callable, *args, **kwargs) -> bool:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex import sex_settings as WickedWhimsSexSettings

		if WickedWhimsSexSettings.get_sex_setting(WickedWhimsSexSettings.SexSetting.PREGNANCY_MODE) != WickedWhimsSexSettings.PregnancyModeSetting.SIMPLE:
			# noinspection PyProtectedMember
			WickedWhimsSexSettings._sex_settings_data[WickedWhimsSexSettings.SexSetting.PREGNANCY_MODE] = WickedWhimsSexSettings.PregnancyModeSetting.SIMPLE

		return originalCallable(*args, **kwargs)
	except:
		Debug.Log("Failed to handle WickedWhim's update sex settings to general save data function.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(*args, **kwargs)

def _WickedWhimsTakeBirthControlPillPatch (originalCallable: typing.Callable, turbo_sim: typing.Any, no_inventory: bool = False, *args, **kwargs) -> bool:
	try:
		targetSimInfo = turbo_sim.get_sim_info()  # type: typing.Optional[sim_info.SimInfo]

		if targetSimInfo is None:
			return False

		if no_inventory:
			SafetyBirthControlPills.TakePill(targetSimInfo, None, requiresPill = False, removePill = False)
	except:
		Debug.Log("Failed to handle WickedWhim's take birth control pill function.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(turbo_sim, no_inventory = no_inventory, *args, **kwargs)

def _WickedWhimsTakeBirthControlPillInteractionTestPatch (originalCallable: typing.Callable, *args, **kwargs) -> typing.Union[bool, results.TestResult]:
	try:
		return results.TestResult(False)
	except:
		Debug.Log("Failed to handle WickedWhim's take birth control pill interaction test method.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(*args, **kwargs)

def _WickedWhimsAllowBirthControlPillsAutoUseInteractionTestPatch (originalCallable: typing.Callable, *args, **kwargs) -> typing.Union[bool, results.TestResult]:
	try:
		return results.TestResult(False, tooltip = DisabledBecauseCycleInstalledToolTip.GetCallableLocalizationString())
	except:
		Debug.Log("Failed to handle WickedWhim's allow birth control pills auto use interaction test method.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(*args, **kwargs)

def _WickedWhimsDisallowBirthControlPillsAutoUseInteractionTestPatch (originalCallable: typing.Callable, *args, **kwargs) -> typing.Union[bool, results.TestResult]:
	try:
		return results.TestResult(False, tooltip = DisabledBecauseCycleInstalledToolTip.GetCallableLocalizationString())
	except:
		Debug.Log("Failed to handle WickedWhim's disallow birth control pills auto use interaction test method.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(*args, **kwargs)

CyclePatches = {
	"ResetCondomMethodUse": _DoCycleResetCondomMethodUseSettingPatch,
	"DisableCondomMethodUseChange": _DoCycleDisableCondomMethodUseChangePatch,
	"AddUnpackCondomBoxInteraction": None,
	"AddTakeBirthControlPillInteraction": None,
	"AddReadBirthControlPillInstructionsInteraction": None,
	"FindValidPillsObject": _DoCycleFindValidPillsObjectPatch,
	"GetPillsLeftInObject": _DoCycleGetPillsLeftInObjectPatch,
	"RemovePillFromObject": _DoCycleRemovePillFromObjectPatch
}  # type: typing.Dict[str, typing.Optional[typing.Callable]]

WickedWhimsPatches = {
	"Impregnation": _DoWickedWhimsImpregnationPatch,
	"Menstruation": _DoWickedWhimsMenstruationPatch,
	"TakeBirthControlPill": _DoWickedWhimsTakeBirthControlPillPatch,
	"TakeBirthControlPillInteractionTest": _DoWickedWhimsTakeBirthControlPillInteractionTestPatch,
	"AllowBirthControlPillsAutoUseInteractionTest": _DoWickedWhimsAllowBirthControlPillsAutoUseInteractionTestPatch,
	"DisallowBirthControlPillsAutoUseInteractionTest": _DoWickedWhimsDisallowBirthControlPillsAutoUseInteractionTestPatch,
	"CheckCyclesInfo": None,
}  # type: typing.Dict[str, typing.Optional[typing.Callable]]
