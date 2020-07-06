from __future__ import annotations

import collections
import sys
import typing

import services
from NeonOcean.S4.Cycle import Insemination, This
from NeonOcean.S4.Cycle import SimSettings
from NeonOcean.S4.Cycle.Interactions import CondomBox as InteractionsCondomBox
from NeonOcean.S4.Cycle.Safety import Resources as SafetyResources
from NeonOcean.S4.Main import Debug, Language
from NeonOcean.S4.Main.Tools import Exceptions, Patcher, Python
from NeonOcean.S4.Main.Interactions.Support import DisableInteraction
from sims import sim_info

"""
If your the creator of wicked whims - NeonOceanCreations@gmail.com - It might be better if you do some of these patches.
"""

DisabledBecauseWickedWhimsInstalledToolTip = Language.String(This.Mod.Namespace + ".Mods.WickedWhims.Disabled_Because_Installed_Tooltip")

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
	for simIDString, woohooSafetyMethodUse in SimSettings.WoohooSafetyMethodUse.GetAllBranches():  # type: str, typing.Dict[str, bool]
		woohooSafetyMethodUse.pop(str(SafetyResources.CondomWoohooSafetyMethodID))

		SimSettings.WoohooSafetyMethodUse.Set(simIDString, woohooSafetyMethodUse, autoSave = False, autoUpdate = False)

	SimSettings.Update()

def _DoCycleDisableCondomMethodUseChangePatch () -> None:
	InteractionsCondomBox.StartUsingInteraction.add_additional_test(DisableInteraction.DisabledInteractionTest(reasonToolTip = DisabledBecauseWickedWhimsInstalledToolTip))
	InteractionsCondomBox.StopUsingInteraction.add_additional_test(DisableInteraction.DisabledInteractionTest(reasonToolTip = DisabledBecauseWickedWhimsInstalledToolTip))

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
		Patcher.Patch(WickedWhimsSexSettings, "get_sex_setting", _WickedWhimsGetSexSettingPatch, patchType = Patcher.PatchTypes.Custom)
	except:
		Debug.Log("Could not complete WickedWhims impregnation patch.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

# noinspection PyUnusedLocal
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

# noinspection PyUnusedLocal
def _WickedWhimsGetSexSettingPatch (originalCallable: typing.Callable, variable, *args, **kwargs) -> bool:
	try:
		# noinspection PyUnresolvedReferences
		from wickedwhims.sex import sex_settings as WickedWhimsSexSettings

		if variable == WickedWhimsSexSettings.SexSetting.PREGNANCY_MODE:
			return WickedWhimsSexSettings.PregnancyModeSetting.SIMPLE
		else:
			return originalCallable(variable, *args, **kwargs)
	except:
		Debug.Log("Failed to handle WickedWhim's get sex setting function.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		return originalCallable(variable, *args, **kwargs)

CyclePatches = {
	"ResetCondomMethodUse": _DoCycleResetCondomMethodUseSettingPatch,
	"DisableCondomMethodUseChange": _DoCycleDisableCondomMethodUseChangePatch,
	"AddUnpackCondomBoxInteraction": None
}  # type: typing.Dict[str, typing.Optional[typing.Callable]]

WickedWhimsPatches = {
	"Impregnation": _DoWickedWhimsImpregnationPatch,
	"Menstruation": _DoWickedWhimsMenstruationPatch
}  # type: typing.Dict[str, typing.Optional[typing.Callable]]
