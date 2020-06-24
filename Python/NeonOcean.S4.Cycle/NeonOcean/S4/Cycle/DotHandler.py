import indexed_manager
import services
import zone
from NeonOcean.S4.Cycle import Dot, Saving, This
from NeonOcean.S4.Main import Debug, Director, LoadingShared
from NeonOcean.S4.Main.Saving import SectionBranched
from sims import sim_info, sim_info_manager

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		_ResetZoneHandling()
		_SetupZoneHandling()

	@classmethod
	def ZoneOnToreDown (cls, *args, **kwargs) -> None:
		_ResetZoneHandling()

# noinspection PyUnusedLocal
def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	Saving.GetSimsSection().RegisterLoadCallback(_SimsSectionLoadCallback)
	Saving.GetSimsSection().RegisterSaveCallback(_SimsSectionSaveCallback)
	Saving.GetSimsSection().RegisterResetCallback(_SimsSectionResetCallback)

	if services.current_zone() is not None:
		_SetupZoneHandling()

# noinspection PyUnusedLocal
def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	Saving.GetSimsSection().UnregisterLoadCallback(_SimsSectionLoadCallback)
	Saving.GetSimsSection().UnregisterSaveCallback(_SimsSectionSaveCallback)
	Saving.GetSimsSection().UnregisterResetCallback(_SimsSectionResetCallback)

	if services.current_zone() is not None:
		_ResetZoneHandling()

def _SetupZoneHandling () -> None:
	simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager

	if simInfoManager is not None:
		simInfoManager.register_callback(indexed_manager.CallbackTypes.ON_OBJECT_ADD, _OnSimAddCallback)
		simInfoManager.register_callback(indexed_manager.CallbackTypes.ON_OBJECT_REMOVE, _OnSimRemoveCallback)

def _ResetZoneHandling () -> None:
	simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager

	if simInfoManager is not None:
		# noinspection PyProtectedMember
		onObjectAddCallbacks = simInfoManager._registered_callbacks.get(indexed_manager.CallbackTypes.ON_OBJECT_ADD, None)

		if onObjectAddCallbacks is not None:
			onObjectAddCallbackIndex = 0
			while onObjectAddCallbackIndex < len(onObjectAddCallbacks):
				onObjectAddCallback = onObjectAddCallbacks[onObjectAddCallbackIndex]

				if onObjectAddCallback == _OnSimAddCallback:
					onObjectAddCallbacks.pop(onObjectAddCallbackIndex)
					continue

				onObjectAddCallbackIndex += 1

		# noinspection PyProtectedMember
		onObjectRemoveCallbacks = simInfoManager._registered_callbacks.get(indexed_manager.CallbackTypes.ON_OBJECT_REMOVE, None)

		if onObjectRemoveCallbacks is not None:
			onObjectRemoveCallbackIndex = 0
			while onObjectRemoveCallbackIndex < len(onObjectRemoveCallbacks):
				onObjectRemoveCallback = onObjectRemoveCallbacks[onObjectRemoveCallbackIndex]

				if onObjectRemoveCallback == _OnSimAddCallback:
					onObjectRemoveCallbacks.pop(onObjectRemoveCallbackIndex)
					continue

				onObjectRemoveCallbackIndex += 1

def _OnSimAddCallback (simInfo: sim_info.SimInfo) -> None:
	if not This.Mod.IsLoaded():
		return

	try:
		if Dot.HasDotInformation(simInfo):
			Debug.Log("Went to create a dot information object for a sim being added, but one already exists.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return

		dotInformation = Dot.CreateDotInformation(simInfo)
		simsSection = Saving.GetSimsSection()  # type: SectionBranched.SectionBranched

		if simsSection.SavingObject.Loaded:
			dotInformation.Load(simsSection)
	except:
		Debug.Log("Dot on sim add callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _OnSimRemoveCallback (simInfo: sim_info.SimInfo) -> None:
	if not This.Mod.IsLoaded():
		return

	try:
		Dot.ClearDotInformation(simInfo)
	except:
		Debug.Log("Dot on sim remove callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def _SimsSectionLoadCallback (simsSection: SectionBranched.SectionBranched) -> bool:
	return Dot.LoadAllDotInformation(simsSection = simsSection)

def _SimsSectionSaveCallback (simsSection: SectionBranched.SectionBranched) -> bool:
	return Dot.SaveAllDotInformation(simsSection = simsSection)

def _SimsSectionResetCallback (simsSection: SectionBranched.SectionBranched) -> bool:
	return Dot.ResetAllDotInformation(simsSection = simsSection)
