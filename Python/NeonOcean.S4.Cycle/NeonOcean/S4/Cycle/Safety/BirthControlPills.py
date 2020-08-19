from __future__ import annotations

import typing

import services
from NeonOcean.S4.Cycle import Reproduction, ReproductionShared
from NeonOcean.S4.Cycle.Effects import BirthControlPills as EffectsBirthControlPills, Shared as EffectsShared
from NeonOcean.S4.Cycle.Safety import Resources as SafetyResources
from NeonOcean.S4.Cycle.UI import BirthControlPills as UIBirthControlPills
from NeonOcean.S4.Cycle.Universal import EffectTracker, Shared as UniversalShared
from NeonOcean.S4.Main.Tools import Exceptions
from objects import definition_manager, script_object
from objects.components import inventory as ComponentsInventory, types as ComponentsTypes
from sims import sim, sim_info
from sims4 import resources
from sims4.tuning import instance_manager
from statistics import statistic, statistic_tracker

def OnBirthControlPills (targetSimInfo: sim_info.SimInfo) -> bool:
	"""
	Get Whether or not the input sim is officially considered to be on birth control pills.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	targetSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

	if targetSystem is None:
		return False

	targetEffectsTracker = targetSystem.GetTracker(UniversalShared.EffectTrackerIdentifier)  # type: typing.Optional[EffectTracker.EffectTracker]

	if targetEffectsTracker is None:
		return False

	targetBirthControlPillsEffect = targetEffectsTracker.GetEffect(EffectsShared.BirthControlPillsEffectTypeIdentifier)  # type: typing.Optional[EffectsBirthControlPills.BirthControlPillsEffect]

	if targetBirthControlPillsEffect is None:
		return False

	return targetBirthControlPillsEffect.OnBirthControlPills()

def TakePill (
		targetSimInfo: sim_info.SimInfo,
		pillsObject: typing.Optional[script_object.ScriptObject],
		requiresPill: bool = True,
		removePill: bool = True,
		showGeneralFeedback: bool = True,
		showWarningFeedback: bool = True) -> bool:
	"""
	Update the birth control pills effect for the target sim and show feedback notifications. Nothing will happen if the target has no reproductive system,
	or has no birth control pill effect in that system.
	:param targetSimInfo: The sim that is taking the pill.
	:type targetSimInfo: sim_info.SimInfo
	:param pillsObject: The pills object the sim is taking a pill from. This can be none if the 'requiresPill' and 'removePill' parameters are false.
	:type pillsObject: typing.Optional[script_object.ScriptObject]
	:param requiresPill: If true, this function must find a pill for the sim to take or nothing will happen.
	:type requiresPill: bool
	:param removePill: If true, this function will remove a pill from the sim's inventory. This will be ignored if a pill is not required and there are no pills
	to remove.
	:type removePill: bool
	:param showGeneralFeedback: Whether or not we should show non warning feedback. This should be false for automatically taken pills.
	:type showGeneralFeedback: bool
	:param showWarningFeedback: Show the warnings that should appear when a sim has forgotten to take one or more pills or that the sim is out of medicine.
	:type showWarningFeedback: bool
	:return: True or false, depending on whether or not the sim was actually able to take a pill.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	if not isinstance(pillsObject, script_object.ScriptObject) and pillsObject is not None:
		raise Exceptions.IncorrectTypeException(pillsObject, "pillsObject", (script_object.ScriptObject, None))

	if not isinstance(requiresPill, bool):
		raise Exceptions.IncorrectTypeException(requiresPill, "requiresPill", (bool,))

	if not isinstance(removePill, bool):
		raise Exceptions.IncorrectTypeException(removePill, "removePill", (bool,))

	if pillsObject is None and (requiresPill or removePill):
		raise ValueError("The 'pillsObject' parameter cannot be none if the requires pill or remove pill parameters are true.")

	if not isinstance(showGeneralFeedback, bool):
		raise Exceptions.IncorrectTypeException(showGeneralFeedback, "showGeneralFeedback", (bool,))

	if not isinstance(showWarningFeedback, bool):
		raise Exceptions.IncorrectTypeException(showWarningFeedback, "showWarningFeedback", (bool,))

	targetSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

	if targetSystem is None:
		return False

	targetEffectsTracker = targetSystem.GetTracker(UniversalShared.EffectTrackerIdentifier)  # type: typing.Optional[EffectTracker.EffectTracker]

	if targetEffectsTracker is None:
		return False

	targetBirthControlPillsEffect = targetEffectsTracker.GetEffect(EffectsShared.BirthControlPillsEffectTypeIdentifier)  # type: typing.Optional[EffectsBirthControlPills.BirthControlPillsEffect]

	if targetBirthControlPillsEffect is None:
		return False

	currentPillsLeft = GetPillsLeftInObject(pillsObject)  # type: int

	if requiresPill and currentPillsLeft <= 0:
		return False

	missedPills = targetBirthControlPillsEffect.GetAmountOfMissedPills()  # type: typing.Optional[int]
	missedPillsIntentional = targetBirthControlPillsEffect.MissedPillsIntentional()  # type: bool

	targetBirthControlPillsEffect.NotifyOfTakenPill()

	if removePill:
		RemovePillFromObject(pillsObject)

	if not missedPillsIntentional and missedPills > 0:
		UIBirthControlPills.ShowMissedPillNotification(targetSimInfo, missedPills)  # TODO pills remaining dialogs

def FindValidPillsObject (targetSim: sim.Sim) -> typing.Optional[script_object.ScriptObject]:
	"""
	Get the first found pills object in the target sim's inventory that has pills remaining. This will return none if the target sim has no valid birth control
	pills objects in their inventory.
	"""

	if not isinstance(targetSim, sim.Sim):
		raise Exceptions.IncorrectTypeException(targetSim, "targetSim", (sim.Sim,))

	inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent

	statisticManager = services.get_instance_manager(resources.Types.STATISTIC)  # type: instance_manager.InstanceManager

	pillsCountStatisticType = statisticManager.get(SafetyResources.BirthControlPillsCountStatisticID)  # type: typing.Type[statistic.Statistic]

	for inventoryObject in inventoryComponent:  # type: script_object.ScriptObject
		if inventoryObject.definition.id == SafetyResources.BirthControlPillsObjectDefinitionID:
			pillsCountStatisticTracker = inventoryObject.get_tracker(pillsCountStatisticType)

			if pillsCountStatisticTracker is None:
				continue

			pillsCountStatistic = pillsCountStatisticTracker.get_statistic(pillsCountStatisticType, add = True)  # type: typing.Optional[statistic.Statistic]

			if pillsCountStatistic is None:
				continue

			pillsObjectCount = int(pillsCountStatistic.get_value())  # type: int

			if pillsObjectCount > 0:
				return inventoryObject

	return None

def GetPillsLeftInObject (pillsObject: script_object.ScriptObject) -> typing.Optional[int]:
	"""
	Get how many pills are left in this pills object. This will return none if the input object is not a pills object.
	"""

	if not isinstance(pillsObject, script_object.ScriptObject):
		raise Exceptions.IncorrectTypeException(pillsObject, "pillsObject", (script_object.ScriptObject,))

	if pillsObject.definition.id != SafetyResources.BirthControlPillsObjectDefinitionID:
		return None

	statisticManager = services.get_instance_manager(resources.Types.STATISTIC)  # type: typing.Optional[definition_manager.InstanceManager]

	pillsCountStatisticType = statisticManager.get(SafetyResources.BirthControlPillsCountStatisticID)  # type: typing.Type[statistic.Statistic]

	pillsCountStatisticTracker = pillsObject.get_tracker(pillsCountStatisticType)  # type: typing.Optional[statistic_tracker.StatisticTracker]

	if pillsCountStatisticTracker is None:
		return None

	pillsCountStatistic = pillsCountStatisticTracker.get_statistic(pillsCountStatisticType, add = True)  # type: typing.Optional[statistic.Statistic]

	if pillsCountStatistic is None:
		return None

	return int(pillsCountStatistic.get_value())

def RemovePillFromObject (pillsObject: script_object.ScriptObject) -> bool:
	"""
	Remove a pill from this pills object. The returns true if there was a pill to remove from the object.
	"""

	if not isinstance(pillsObject, script_object.ScriptObject):
		raise Exceptions.IncorrectTypeException(pillsObject, "pillsObject", (script_object.ScriptObject,))

	if pillsObject.definition.id != SafetyResources.BirthControlPillsObjectDefinitionID:
		return False

	statisticManager = services.get_instance_manager(resources.Types.STATISTIC)  # type: typing.Optional[definition_manager.InstanceManager]

	pillsCountStatisticType = statisticManager.get(SafetyResources.BirthControlPillsCountStatisticID)  # type: typing.Type[statistic.Statistic]
	pillsCountStatisticTracker = pillsObject.get_tracker(pillsCountStatisticType)  # type: typing.Optional[statistic_tracker.StatisticTracker]

	if pillsCountStatisticTracker is None:
		return False

	pillsCountStatistic = pillsCountStatisticTracker.get_statistic(pillsCountStatisticType, add = True)  # type: typing.Optional[statistic.Statistic]

	if pillsCountStatistic is None:
		return False

	pillsObjectCount = int(pillsCountStatistic.get_value())  # type: int

	if pillsObjectCount <= 0:
		return False

	pillsCountStatistic.set_value(pillsObjectCount - 1)

	return True
