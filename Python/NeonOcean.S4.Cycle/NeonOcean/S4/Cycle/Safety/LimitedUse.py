from __future__ import annotations

import typing

import services
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Safety import WoohooSafety
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Exceptions
from objects import definition
from objects.components import inventory as ComponentsInventory, types as ComponentsTypes
from sims import sim, sim_info
from sims4 import commands, resources
from sims4.tuning import tunable
from statistics import statistic

if typing.TYPE_CHECKING:
	from objects import game_object

class UseReductionBase:
	def GetUseCount (self, targetSimInfo: sim_info.SimInfo) -> int:
		"""
		Get the number of uses of this woohoo safety method the target sim has left.
		:param targetSimInfo: The sim who we are getting the use count of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: The number of uses of this woohoo safety method the target sim has left.
		:rtype: bool
		"""

		raise NotImplementedError()

	def RemoveUse (self, targetSimInfo: sim_info.SimInfo) -> bool:
		"""
		Remove one or more uses from this woohoo safety method.
		:param targetSimInfo: The sim who we are removing a use of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: Whether or not we could remove a use from the target sim.
		:rtype: bool
		"""

		raise NotImplementedError()

class UseReductionInventoryStatistic(UseReductionBase, tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
	FACTORY_TUNABLES = {
		"TargetObject": tunable.TunableReference(description = "The type of object for which we should reduce the target statistic.", manager = services.get_instance_manager(resources.Types.OBJECT), pack_safe = True),
		"TargetStatistic": tunable.TunableReference(description = "The statistic that counts how many uses this woohoo method has available.", manager = services.get_instance_manager(resources.Types.STATISTIC), pack_safe = True),
	}

	TargetObject: typing.Optional[definition.Definition]
	TargetStatistic: typing.Optional[typing.Type[statistic.Statistic]]

	def GetUseCount (self, targetSimInfo: sim_info.SimInfo) -> int:
		"""
		Get the number of uses of this woohoo safety method the target sim has left.
		:param targetSimInfo: The sim who we are getting the use count of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: The number of uses of this woohoo safety method the target sim has left. This will always return 0 if the sim is not instanced; we
		cannot read the inventory of sims not instanced.
		:rtype: bool
		"""

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

		if self.TargetObject is None or self.TargetStatistic is None:
			return 0

		if not targetSimInfo.is_instanced():
			return 0

		targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

		inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent

		if not inventoryComponent.has_item_with_definition(self.TargetObject):
			return 0

		useCount = 0  # type: int

		for matchingObject in inventoryComponent.get_items_with_definition_gen(self.TargetObject):  # type: game_object.GameObject
			matchingStatistic = matchingObject.statistic_tracker.get_statistic(self.TargetStatistic, add = True)  # type: statistic.BaseStatistic
			matchingStatisticValue = int(matchingStatistic.get_value())  # type: int

			if matchingStatisticValue <= 0:
				continue

			useCount += matchingStatisticValue

		return useCount

	def RemoveUse (self, targetSimInfo: sim_info.SimInfo) -> bool:
		"""
		Remove one or more uses from this woohoo safety method.
		:param targetSimInfo: The sim who we are removing a use of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: Whether or not we could remove a use from the target sim. This will return false if no matching object was found in the sim's
		inventory or all match objects found were out of uses. This will always return false if the sim is not instanced; we cannot read the
		inventory of sims not instanced.
		:rtype: bool
		"""

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

		if self.TargetObject is None or self.TargetStatistic is None:
			return False

		if not targetSimInfo.is_instanced():
			return False

		targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

		inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent

		if not inventoryComponent.has_item_with_definition(self.TargetObject):
			return False

		for matchingObject in inventoryComponent.get_items_with_definition_gen(self.TargetObject):  # type: game_object.GameObject
			matchingStatistic = matchingObject.statistic_tracker.get_statistic(self.TargetStatistic, add = True)  # type: statistic.BaseStatistic
			matchingStatisticValue = int(matchingStatistic.get_value())  # type: int

			if matchingStatisticValue <= 0:
				continue

			matchingStatistic.set_value(matchingStatisticValue - 1)
			break

		return True

class UseReductionInventoryObject(UseReductionBase, tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
	FACTORY_TUNABLES = {
		"TargetObject": tunable.TunableReference(description = "The type of object for which we should remove from the sim's inventory.", manager = services.get_instance_manager(resources.Types.OBJECT), pack_safe = True),
	}

	TargetObject: typing.Optional[definition.Definition]

	def GetUseCount (self, targetSimInfo: sim_info.SimInfo) -> int:
		"""
		Get the number of uses of this woohoo safety method the target sim has left.
		:param targetSimInfo: The sim who we are getting the use count of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: The number of uses of this woohoo safety method the target sim has left. This will always return 0 if the sim is not instanced; we
		cannot read the inventory of sims not instanced.
		:rtype: bool
		"""

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

		if self.TargetObject is None:
			return 0

		if not targetSimInfo.is_instanced():
			return 0

		targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

		inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent
		return inventoryComponent.get_item_quantity_by_definition(self.TargetObject)

	def RemoveUse (self, targetSimInfo: sim_info.SimInfo) -> bool:
		"""
		Remove one or more uses from this woohoo safety method.
		:param targetSimInfo: The sim who we are removing a use of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: Whether or not we could remove a use from the target sim. This will return false if no matching object was found in the sim's
		inventory or all match objects found were out of uses. This will always return false if the sim is not instanced; we cannot read the
		inventory of sims not instanced.
		:rtype: bool
		"""

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

		if self.TargetObject is None:
			return False

		if not targetSimInfo.is_instanced():
			return False

		targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

		inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent
		return inventoryComponent.try_destroy_object_by_definition(self.TargetObject)

class UseReductionOptions(UseReductionBase, tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
	FACTORY_TUNABLES = {
		"Options": tunable.TunableList(
			tunable = tunable.TunableVariant(
				inventoryStatistic = UseReductionInventoryStatistic.TunableFactory(),
				inventoryObject = UseReductionInventoryObject.TunableFactory(),
			)
		)
	}

	Options: typing.Tuple[UseReductionBase]

	def GetUseCount (self, targetSimInfo: sim_info.SimInfo) -> int:
		"""
		Get the number of uses of this woohoo safety method the target sim has left.
		:param targetSimInfo: The sim who we are getting the use count of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: The number of uses of this woohoo safety method the target sim has left.
		:rtype: bool
		"""

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

		useCount = 0  # type: int

		for option in self.Options:  # type: UseReductionBase
			useCount += option.GetUseCount(targetSimInfo)

		return useCount

	def RemoveUse (self, targetSimInfo: sim_info.SimInfo) -> bool:
		"""
		Remove one or more uses from this woohoo safety method.
		:param targetSimInfo: The sim who we are removing a use of this safety method for.
		:type targetSimInfo: sim_info.SimInfo
		:return: Whether or not we could remove a use from the target sim.
		:rtype: bool
		"""
		for option in self.Options:  # type: UseReductionBase
			if option.RemoveUse(targetSimInfo):
				return True

		return False

class LimitedUseWoohooSafetyMethod(WoohooSafety.WoohooSafetyMethod):
	UseReductionBase = UseReductionBase
	UseReductionInventoryStatistic = UseReductionInventoryStatistic
	UseReductionInventoryObject = UseReductionInventoryObject
	UseReductionOptions = UseReductionOptions

	FACTORY_TUNABLES = {
		"UseReduction": tunable.TunableVariant(
			inventoryStatistic = UseReductionInventoryStatistic.TunableFactory(),
			inventoryObject = UseReductionInventoryObject.TunableFactory(),
			options = UseReductionOptions.TunableFactory()
		),
		"PreferInseminatedUses": tunable.Tunable(description = "If true, we will search the inseminated sim for uses to remove before the source sim.", tunable_type = bool, default = True),
		"HandlePostUseReduction": tunable.OptionalTunable(description = "A console command that needs to be called after a use of this safety method has been removed. This should be used to show notifications that a sim has run out of a woohoo safety method. The command should take the woohoo safety method guid, the target sim's id (the sim using the woohoo method), and the amount of uses remaining, in that order. The method GUID, and target sim id parameters may not actually get valid ids.", tunable = tunable.Tunable(tunable_type = str, default = None))

	}

	UseReduction: UseReductionBase
	PreferInseminatedUses: bool
	HandlePostUseReduction: typing.Optional[str]

	def HandlePostUse (self, inseminatedSimInfo: typing.Optional[sim_info.SimInfo], sourceSimInfo: typing.Optional[sim_info.SimInfo], performanceType: str) -> None:
		"""
		Handle the after effects of using this woohoo safety method.
		"""

		if not isinstance(inseminatedSimInfo, sim_info.SimInfo) and inseminatedSimInfo is not None:
			raise Exceptions.IncorrectTypeException(inseminatedSimInfo, "inseminatedSimInfo", (sim_info.SimInfo,))

		if not isinstance(inseminatedSimInfo, sim_info.SimInfo) and inseminatedSimInfo is not None:
			raise Exceptions.IncorrectTypeException(inseminatedSimInfo, "inseminatedSimInfo", (sim_info.SimInfo,))

		if not isinstance(performanceType, str):
			raise Exceptions.IncorrectTypeException(performanceType, "performanceType", (str,))

		primaryReductionSimInfo = inseminatedSimInfo if self.PreferInseminatedUses else sourceSimInfo
		secondaryReductionSimInfo = sourceSimInfo if self.PreferInseminatedUses else inseminatedSimInfo

		reducedSimInfo = None  # type: typing.Optional[sim_info.SimInfo]

		if primaryReductionSimInfo is not None and self.UseReduction.RemoveUse(primaryReductionSimInfo):
			reducedSimInfo = primaryReductionSimInfo
		elif secondaryReductionSimInfo is not None and self.UseReduction.RemoveUse(secondaryReductionSimInfo):
			reducedSimInfo = secondaryReductionSimInfo

		super().HandlePostUse(inseminatedSimInfo, sourceSimInfo, performanceType)

		if reducedSimInfo is not None:
			reducedSimUsesRemaining = self.UseReduction.GetUseCount(reducedSimInfo)  # type: int

			if self.HandlePostUseReduction is not None:
				methodGUID = self.GUID if self.GUID is not None else 0  # type: int
				reducedSimID = reducedSimInfo.id if reducedSimInfo is not None else 0

				try:
					consoleCommand = " ".join((self.HandlePostUseReduction, str(methodGUID), str(reducedSimID), str(reducedSimUsesRemaining)))
					commands.execute(consoleCommand, None)
				except:
					Debug.Log("Failed to call handle post use reduction command for woohoo safety method '%s'." % str(self.GUID), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
