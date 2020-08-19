from __future__ import annotations

import indexed_manager
import services
import game_services
import typing
import random
import zone
from NeonOcean.S4.Cycle import Settings, This, Guides as CycleGuides, GuideGroups as CycleGuideGroups, Reproduction, ReproductionShared
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Cycle.Settings import Base as ModSettingsBase
from NeonOcean.S4.Cycle.SimSettings import Types as SettingsTypes
from NeonOcean.S4.Main import Debug, Director, Language
from NeonOcean.S4.Main.Tools import Events, Exceptions
from sims import sim_info, sim_info_manager, sim_info_types

_AllSimsExperiencePMSOverrideIdentifier = "AllSimsExperiencePMS"  # type: str
_AllSimsExperiencePMSOverrideReason = Language.String(This.Mod.Namespace + ".Sim_Settings.Values.Experiences_PMS.All_Sims_Experience_PMS_Override_Reason", fallbackText = "All_Sims_Experience_PMS_Override_Reason")

_experiencesPMSRollSeed = 519490138  # type: int

class ExperiencesPMS(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Experiences_PMS"  # type: str
	Default = True  # type: dict

	ListPath = "Root/Menstruation"  # type: str

	@classmethod
	def IsHidden(cls, simID: str) -> bool:
		"""
		Get whether or not this setting should be visible to the user.
		"""

		if not isinstance(simID, str):
			raise Exceptions.IncorrectTypeException(simID, "simID", (str,))

		try:
			simIDNumber = int(simID)  # type: int
		except ValueError:
			return True

		if game_services.service_manager is None:
			return True

		simInfoManager = services.sim_info_manager()  # type: typing.Optional[sim_info_manager.SimInfoManager]

		if simInfoManager is None:
			return True

		simInfo = simInfoManager.get(simIDNumber)  # type: typing.Optional[sim_info.SimInfo]

		if simInfo is None:
			return True

		if simInfo.species != sim_info_types.Species.HUMAN:
			return True

		simSystem = Reproduction.GetSimSystem(simInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

		if simSystem is None:
			return True

		if not simSystem.HasTracker(FemalesShared.CycleTrackerIdentifier):
			return True

		return False

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
def _OnStart (cause) -> None:
	Settings.RegisterOnUpdateCallback(_SettingsOnUpdatedCallback)
	Settings.RegisterOnLoadCallback(_SettingsOnLoadedCallback)

	_RollAllSimsExperiencesPMSValues()
	_HandleAllSimsExperiencePMSOverride()

	if services.current_zone() is not None:
		_SetupZoneHandling()

# noinspection PyUnusedLocal
def _OnStop (cause) -> None:
	Settings.UnregisterOnUpdateCallback(_SettingsOnUpdatedCallback)
	Settings.UnregisterOnLoadCallback(_SettingsOnLoadedCallback)

	if services.current_zone() is not None:
		_ResetZoneHandling()

def _HandleAllSimsExperiencePMSOverride () -> None:
	if Settings.AllSimsExperiencePMS.Get():
		ExperiencesPMS.RemoveOverride(_AllSimsExperiencePMSOverrideIdentifier)
		ExperiencesPMS.OverrideAll(True, _AllSimsExperiencePMSOverrideIdentifier, 0, overrideReasonText = _AllSimsExperiencePMSOverrideReason.GetCallableLocalizationString())
	else:
		ExperiencesPMS.RemoveOverride(_AllSimsExperiencePMSOverrideIdentifier)

def _RollAllSimsExperiencesPMSValues () -> None:
	if game_services.service_manager is None:
		return

	simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager

	if simInfoManager is None:
		return

	for simInfo in simInfoManager.values():  # type: sim_info.SimInfo
		_RollSimExperiencesPMSValue(simInfo)

def _RollSimExperiencesPMSValue (simInfo: sim_info.SimInfo) -> None:
	simID = simInfo.id  # type: int
	simIDString = str(simID)  # type: str

	if not ExperiencesPMS.ValueIsSet(simIDString):
		simGuideGroup = CycleGuideGroups.FindGuideGroup(simInfo)  # type: typing.Optional[CycleGuideGroups.GuideGroup]

		if simGuideGroup is None:
			ExperiencesPMS.Set(simIDString, False)
			return

		simMenstrualEffect = CycleGuides.MenstrualEffectGuide.GetGuide(simGuideGroup)  # type: CycleGuides.MenstrualEffectGuide

		random.seed(simID + _experiencesPMSRollSeed)
		experiencesPMSRoll = random.random()  # type: float

		ExperiencesPMS.Set(simIDString, experiencesPMSRoll <= simMenstrualEffect.ExperiencesPMSProbability)

def _SetupZoneHandling () -> None:
	simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager

	if simInfoManager is not None:
		simInfoManager.register_callback(indexed_manager.CallbackTypes.ON_OBJECT_ADD, _OnSimAddCallback)

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

def _OnSimAddCallback (simInfo: sim_info.SimInfo) -> None:
	if not This.Mod.IsLoaded():
		return

	try:
		_RollSimExperiencesPMSValue(simInfo)
	except:
		Debug.Log("Dot on sim add callback failed.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

# noinspection PyUnusedLocal
def _SettingsOnUpdatedCallback (settingsModule, eventArguments: ModSettingsBase.UpdateEventArguments) -> None:
	if eventArguments.Changed(Settings.AllSimsExperiencePMS.Key):
		_HandleAllSimsExperiencePMSOverride()

# noinspection PyUnusedLocal
def _SettingsOnLoadedCallback (settingsModule, eventArguments: Events.EventArguments) -> None:
	_RollAllSimsExperiencesPMSValues()
	_HandleAllSimsExperiencePMSOverride()
