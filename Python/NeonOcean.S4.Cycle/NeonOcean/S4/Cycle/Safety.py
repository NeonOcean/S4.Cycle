from __future__ import annotations

import random
import typing

import services
import snippets
from NeonOcean.S4.Cycle import SimSettings, This
from NeonOcean.S4.Cycle.Tools import Distribution, Probability
from NeonOcean.S4.Main import Debug, Snippets as MainSnippets
from NeonOcean.S4.Main.Tools import Exceptions
from event_testing import resolver, tests
from objects import definition
from objects.components import inventory as ComponentsInventory, types as ComponentsTypes
from sims import sim, sim_info
from sims4 import commands, resources
from sims4.tuning import tunable
from statistics import statistic

if typing.TYPE_CHECKING:
	from objects import game_object
	from sims4.testing import unit as TestingUnit

_woohooSafetyMethodSnippetName = This.Mod.Namespace.replace(".", "_") + "_Woohoo_Safety_Method"  # type: str
_limitedUseWoohooSafetyMethodSnippetName = This.Mod.Namespace.replace(".", "_") + "_Limited_Use_Woohoo_Safety_Method"  # type: str

_woohooSafetyMethods = dict()  # type: typing.Dict[int, WoohooSafetyMethod]

class WoohooSafetyMethod(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
	class Requirement:
		def RequirementMet (self, targetSim: sim.Sim) -> bool:
			"""
			Whether or not the target sim meets the requirements.
			"""

			raise NotImplementedError()

	class ObjectRequirement(Requirement, tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
		FACTORY_TUNABLES = {
			"RequiredObject": tunable.TunableReference(description = "A sim must have this object in their inventory in order to meet this requirement.", manager = services.get_instance_manager(resources.Types.OBJECT)),
			"RequiredObjectTests": tests.TunableTestSet(description = "A set of tests the object must pass in order to this requirement to be meet.")
		}

		RequiredObject: definition.Definition
		RequiredObjectTests: tests.CompoundTestList

		def RequirementMet (self, targetSim: sim.Sim) -> bool:
			"""
			Whether or not the target sim meets the requirements.
			"""

			if not isinstance(targetSim, sim.Sim):
				raise Exceptions.IncorrectTypeException(targetSim, "targetSim", (sim.Sim,))

			inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent

			if not inventoryComponent.has_item_with_definition(self.RequiredObject):
				return False
			else:
				if len(self.RequiredObjectTests) == 0:
					return True

			for matchingObject in inventoryComponent.get_items_with_definition_gen(self.RequiredObject):  # type: game_object.GameObject
				requiredObjectResolver = resolver.SingleObjectResolver(matchingObject)
				testResults = self.RequiredObjectTests.run_tests(requiredObjectResolver)  # type: typing.Optional[TestingUnit.TestResult]

				if not testResults:
					return False

			return True

	class PerformanceTypeInfo(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
		FACTORY_TUNABLES = {
			"ArrivingPercentage": tunable.TunableVariant(
				description = "The options to select the percentage of sperm that will arrive for this performance type. These values should be from 0 to 1.",
				default = "fixed",
				fixed = tunable.Tunable(description = "A fixed arriving percentage for this performance type.", tunable_type = float, default = 0.5),
				random = tunable.TunableInterval(description = "An arriving percentage, between the upper and lower bounds, will be randomly selected.", tunable_type = float, default_lower = 0.5, default_upper = 0.5, minimum = 0, maximum = 1),
				normalDistribution = Distribution.TunableNormalDistribution(description = "An arriving percentage will be randomly selected based on a normal distribution.", meanDefault = 0.5, standardDeviationDefault = 0),
			)
		}

		ArrivingPercentage: typing.Union[float, tunable.TunableInterval, Distribution.NormalDistribution]

		def GenerateSpermArrivingPercentage (self, seed: typing.Optional[int] = None) -> float:
			"""
			Get the percentage of sperm that should get past this woohoo device and make it from one sim to another. This will return a number from 0 to 1.
			"""

			if seed is None:
				seed = random.randint(-1000000000, 1000000000)  # type: int

			if not isinstance(seed, int):
				raise Exceptions.IncorrectTypeException(seed, "seed", (int, None))

			if isinstance(self.ArrivingPercentage, tunable.TunedInterval):
				arrivingPercentage = self.ArrivingPercentage.random_float(seed = seed + -712214524)  # type: float
			elif isinstance(self.ArrivingPercentage, Distribution.NormalDistribution):
				arrivingPercentage = self.ArrivingPercentage.GenerateValue(seed = seed + 38190718, minimum = 0, maximum = 1)  # type: float
			else:
				arrivingPercentage = self.ArrivingPercentage

			return arrivingPercentage

	FACTORY_TUNABLES = {
		"Requirements": tunable.TunableList(
			description = "A list of requirements to determine if a sim can use this method. Requirements may be split into groups, only one group needs to be valid for a sim to met the requirements. If there are no requirements we will assume this method can always be used.",
			tunable = tunable.TunableList(
				description = "An individual group for requirements. For this method to be usable, every criteria in at least one of these groups must be met.",
				tunable = tunable.TunableVariant(
					objectRequirement = ObjectRequirement.TunableFactory(),
				)
			)
		),
		"UsingByDefault": tunable.Tunable(description = "Whether or not sims will use this method if its available by default.", tunable_type = bool, default = True),

		"PerformanceTypes": tunable.TunableMapping(
			description = "A set of performance types that denote how effective this safety method was. A performance type will be randomly selected for a woohoo using the 'PerformanceTypeChances' value.",
			key_type = tunable.Tunable(tunable_type = str, default = "UNKNOWN_PERFORMANCE_TYPE"),
			value_type = PerformanceTypeInfo.TunableFactory()
		),
		"PerformanceTypeChances": Probability.TunableProbability(description = "The chances that each performance type will be selected. Each option's identifier should correspond with a performance type."),

		"CompoundingMethod": tunable.Tunable(description = "Whether or not this method may be used at the same time as another method. If more than one non-compound method are to be used, we will select the first method found.", tunable_type = bool, default = True),

		"HandleUseCommand": tunable.OptionalTunable(description = "A console command that needs to be called after this safety method is used. This command should take the woohoo safety method guid, the inseminated sim id, the source sim id, and the performance type, in that order. The method GUID, inseminated sim id, and source sim id parameters may not actually get valid ids.", tunable = tunable.Tunable(tunable_type = str, default = None))
	}

	Requirements: typing.Tuple[typing.Tuple[Requirement, ...], ...]
	UsingByDefault: bool

	PerformanceTypes: typing.Dict[str, PerformanceTypeInfo]
	PerformanceTypeChances: Probability.Probability

	CompoundingMethod: bool

	HandleUseCommand: typing.Optional[str]

	GUID = None  # type: typing.Optional[int]

	@property
	def HasRequirement (self) -> bool:
		"""
		Whether or not this safety method has requirements.
		"""

		if len(self.Requirements) == 0:
			return False

		for requirementGroup in self.Requirements:  # type: typing.Tuple[WoohooSafetyMethod.Requirement, ...]
			if len(requirementGroup) != 0:
				return True

		return False

	def GetUniqueSeed (self) -> int:
		"""
		Get a unique randomization seed for this woohoo safety method.
		"""

		random.seed(self.GUID)
		return random.randint(-1000000000, 1000000000)  # type: int

	def IsAvailable (self, targetSimInfo: sim_info.SimInfo) -> bool:
		"""
		Get whether or not the target sim can use this safety method. This may incorrectly return false for non-instanced sims; we cannot read the inventory
		of sims not instanced.
		"""

		if not isinstance(targetSimInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

		if not self.HasRequirement:
			return True

		if not targetSimInfo.is_instanced():
			return False

		targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

		for requirementGroup in self.Requirements:  # type: typing.Tuple[WoohooSafetyMethod.Requirement, ...]
			if len(requirementGroup) == 0:
				continue

			groupRequirementsMet = True  # type: bool

			for requirement in requirementGroup:  # type: WoohooSafetyMethod.Requirement
				if not requirement.RequirementMet(targetSim):
					groupRequirementsMet = False
					break

			if groupRequirementsMet:
				return True

		return False

	def SelectPerformanceType (self, seed: typing.Optional[int] = None) -> typing.Tuple[str, PerformanceTypeInfo]:
		"""
		Randomly select one of the performance type in this woohoo safety method.
		"""

		if seed is None:
			seed = random.randint(-1000000000, 1000000000)  # type: int

		if not isinstance(seed, int):
			raise Exceptions.IncorrectTypeException(seed, "seed", (int, None))

		if len(self.PerformanceTypes) == 0:
			raise Exception("Could not find any safety method performance type to select.\nGUID: %s" % self.GUID)

		if len(self.PerformanceTypeChances.Options) == 0:
			raise Exception("Could not select a performance type 'PerformanceTypeChances' has no options.\nGUID: %s" % self.GUID)

		performanceType = self.PerformanceTypeChances.ChooseOption(seed = seed + -443757754).Identifier  # type: str
		performanceTypeInfo = self.PerformanceTypes.get(performanceType, None)  # type: WoohooSafetyMethod.PerformanceTypeInfo

		if performanceTypeInfo is None:
			Debug.Log("Randomly selected performance type that doesn't exist.\nGUID: %s, Performance Type: %s" % (str(self.GUID), performanceType), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
			return random.choice(self.PerformanceTypes)

		return performanceType, performanceTypeInfo

	def GenerateSpermArrivingPercentage (self, seed: typing.Optional[int] = None) -> float:
		"""
		Get the percentage of sperm that should get past this woohoo device and make it from one sim to another. This will return a number from 0 to 1.
		"""

		if seed is None:
			seed = random.randint(-1000000000, 1000000000)  # type: int

		if not isinstance(seed, int):
			raise Exceptions.IncorrectTypeException(seed, "seed", (int, None))

		performanceType, performanceTypeInfo = self.SelectPerformanceType(seed = seed + -443757754)  # type: str, WoohooSafetyMethod.PerformanceTypeInfo
		arrivingPercentage = performanceTypeInfo.GenerateSpermArrivingPercentage(seed + -16160599)  # type: float

		if arrivingPercentage < 0:
			Debug.Log("Safety method performance type generated an arriving percentage is less than 0.\nGUID: %s, Performance Type: %s" % (str(self.GUID), performanceType), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
			arrivingPercentage = 0

		if arrivingPercentage > 1:
			Debug.Log("Safety method performance type generated an arriving percentage is greater than 1.\nGUID: %s, Performance Type: %s" % (str(self.GUID), performanceType), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
			arrivingPercentage = 1

		return arrivingPercentage

	def HandlePostUse (self, inseminatedSimInfo: typing.Optional[sim_info.SimInfo], sourceSimInfo: typing.Optional[sim_info.SimInfo], performanceType: str) -> None:
		"""
		Handle the after effects of using this woohoo safety method.
		"""

		if not isinstance(inseminatedSimInfo, sim_info.SimInfo) and inseminatedSimInfo is not None:
			raise Exceptions.IncorrectTypeException(inseminatedSimInfo, "inseminatedSimInfo", (sim_info.SimInfo, ))

		if not isinstance(inseminatedSimInfo, sim_info.SimInfo) and inseminatedSimInfo is not None:
			raise Exceptions.IncorrectTypeException(inseminatedSimInfo, "inseminatedSimInfo", (sim_info.SimInfo, ))

		if not isinstance(performanceType, str):
			raise Exceptions.IncorrectTypeException(performanceType, "performanceType", (str, ))

		if self.HandleUseCommand is not None:
			methodGUID = self.GUID if self.GUID is not None else 0  # type: int
			inseminatedSimID = inseminatedSimInfo.id if inseminatedSimInfo is not None else 0
			sourceSimID = sourceSimInfo.id if sourceSimInfo is not None else 0

			consoleCommand = self.HandleUseCommand + " " + str(methodGUID) + str(inseminatedSimID) + " " + str(sourceSimID) + " " + performanceType
			commands.execute(consoleCommand, None)

class LimitedUseWoohooSafetyMethod(WoohooSafetyMethod):
	class UseReductionBase:
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
			"TargetObject": tunable.TunableReference(description = "The type of object for which we should reduce the target statistic.", manager = services.get_instance_manager(resources.Types.OBJECT)),
			"TargetStatistic": tunable.TunableReference(description = "The statistic that counts how many uses this woohoo method has available.", manager = services.get_instance_manager(resources.Types.STATISTIC)),
		}

		TargetObject: definition.Definition
		TargetStatistic: typing.Type[statistic.Statistic]

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

			if not targetSimInfo.is_instanced():
				return False

			targetSim = targetSimInfo.get_sim_instance()  # type: sim.Sim

			inventoryComponent = targetSim.get_component(ComponentsTypes.INVENTORY_COMPONENT)  # type: ComponentsInventory.InventoryComponent

			if not inventoryComponent.has_item_with_definition(self.TargetObject):
				return False

			for matchingObject in inventoryComponent.get_items_with_definition_gen(self.TargetObject):  # type: game_object.GameObject
				matchingStatistic = matchingObject.statistic_tracker.get_statistic(self.TargetStatistic)  # type: statistic.BaseStatistic
				matchingStatisticValue = matchingStatistic.get_value()

				if matchingStatisticValue <= 0:
					continue

				matchingStatistic.set_value(matchingStatisticValue - 1)
				break

			return True

	FACTORY_TUNABLES = {
		"UseReduction": tunable.TunableVariant(
			inventoryStatistic = UseReductionInventoryStatistic.TunableFactory(),
		),
		"PreferInseminatedUses": tunable.Tunable(description = "If true, we will search the inseminated sim for uses to remove before the source sim.", tunable_type = bool, default = True)
	}
	#TODO used last (condom) message?

	UseReduction: UseReductionBase
	PreferInseminatedUses: bool

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

		if primaryReductionSimInfo is not None and self.UseReduction.RemoveUse(primaryReductionSimInfo):
			pass
		elif secondaryReductionSimInfo is not None and self.UseReduction.RemoveUse(secondaryReductionSimInfo):
			pass

		super().HandlePostUse(inseminatedSimInfo, sourceSimInfo, performanceType)

class MethodPerformanceSelection:
	def __init__ (self, woohooSafetyMethod: WoohooSafetyMethod, autoSelectPerformance: bool = True, autoSelectSeed: typing.Optional[int] = None):
		"""
		An object to choose a woohoo safety method performance type and keep track of the selection.
		:param woohooSafetyMethod: The woohoo safety method from which we are selecting a performance type.
		:type woohooSafetyMethod: WoohooSafetyMethod
		:param autoSelectPerformance: Whether or not we should automatically select a performance type from this safety method.
		:type autoSelectPerformance: bool
		:param autoSelectSeed: The seed that will be used to randomly select a performance type.
		:type autoSelectSeed: typing.Optional[int]
		"""

		if not isinstance(woohooSafetyMethod, WoohooSafetyMethod):
			raise Exceptions.IncorrectTypeException(woohooSafetyMethod, "woohooSafetyMethod", (WoohooSafetyMethod,))

		if not isinstance(autoSelectPerformance, bool):
			raise Exceptions.IncorrectTypeException(autoSelectPerformance, "autoSelectPerformance", (bool,))

		if not isinstance(autoSelectSeed, int) and autoSelectSeed is not None:
			raise Exceptions.IncorrectTypeException(autoSelectSeed, "autoSelectSeed", (int,))

		self.WoohooSafetyMethod = woohooSafetyMethod  # type: WoohooSafetyMethod

		self.SelectedPerformanceType = None  # type: typing.Optional[str]
		self.SelectedPerformanceTypeInfo = None  # type: typing.Optional[WoohooSafetyMethod.PerformanceTypeInfo]

		if autoSelectPerformance:
			if autoSelectSeed is None:
				autoSelectSeed = woohooSafetyMethod.GetUniqueSeed() + -443757754

			try:
				self.SelectPerformanceType(seed = autoSelectSeed)
			except:
				Debug.Log("Failed to select performance type.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	def SelectPerformanceType (self, seed: typing.Optional[int] = None) -> None:
		"""
		Randomly select a performance type from this object's woohoo safety method. This will return an exception if no performance types were
		defined by the woohoo safety method's tuning.
		"""

		self.SelectedPerformanceType, self.SelectedPerformanceTypeInfo = self.WoohooSafetyMethod.SelectPerformanceType(seed)

class MethodPerformanceSelectionSet(list):
	def __init__ (self, woohooSafetyMethods: typing.List[WoohooSafetyMethod], autoSelectBaseSeed: typing.Optional[int] = None):
		if not isinstance(woohooSafetyMethods, typing.List):
			raise Exceptions.IncorrectTypeException(woohooSafetyMethods, "woohooSafetyMethods", (typing.List,))

		if autoSelectBaseSeed is None:
			autoSelectBaseSeed = random.randint(-1000000000, 1000000000)

		if not isinstance(autoSelectBaseSeed, int):
			raise Exceptions.IncorrectTypeException(autoSelectBaseSeed, "autoSelectBaseSeed", (int, None))

		performanceSelections = list()  # type: typing.List[MethodPerformanceSelection]

		for woohooSafetyMethodIndex in range(len(woohooSafetyMethods)):  # type: int
			woohooSafetyMethod = woohooSafetyMethods[woohooSafetyMethodIndex]  # type: WoohooSafetyMethod

			if not isinstance(woohooSafetyMethod, WoohooSafetyMethod):
				raise Exceptions.IncorrectTypeException(woohooSafetyMethods, "woohooSafetyMethods[%s]" % woohooSafetyMethodIndex, (WoohooSafetyMethod,))

			autoSelectSeed = autoSelectBaseSeed + woohooSafetyMethod.GetUniqueSeed()
			performanceSelections.append(MethodPerformanceSelection(woohooSafetyMethod, autoSelectSeed = autoSelectSeed))

		super().__init__(performanceSelections)

	def GenerateSpermArrivingPercentage (self, generationBaseSeed: typing.Optional[int] = None) -> float:
		"""
		Get the percentage of sperm that should get past the woohoo devices and make it from one sim to another. This will return a number from 0 to 1.
		:param generationBaseSeed: The seed being used to generate a random sperm reduction. This will be combined with other seeds unique to each
		woohoo safety method before being used.
		:type generationBaseSeed: typing.Optional[int]
		"""

		if generationBaseSeed is None:
			generationBaseSeed = random.randint(-1000000000, 1000000000)

		if not isinstance(generationBaseSeed, int):
			raise Exceptions.IncorrectTypeException(generationBaseSeed, "generationBaseSeed", (int,))

		if len(self) == 0:
			return 1
		else:
			arrivingPercentage = 1  # type: float

			countedSafetyMethod = False  # type: bool

			for performanceSelectionIndex in range(len(self)):  # type: int
				performanceSelection = self[performanceSelectionIndex]  # type: MethodPerformanceSelection

				if not isinstance(performanceSelection, MethodPerformanceSelection):
					Debug.Log(Exceptions.GetIncorrectTypeExceptionText(performanceSelection, "performanceSelection[%s]" % performanceSelectionIndex, (MethodPerformanceSelection,)), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
					continue

				woohooSafetyMethod = performanceSelection.WoohooSafetyMethod  # type: WoohooSafetyMethod
				performanceTypeInfo = performanceSelection.SelectedPerformanceTypeInfo  # type: WoohooSafetyMethod.PerformanceTypeInfo

				if performanceTypeInfo is None:
					Debug.Log("Performance selection had never selected a performance type.\n Woohoo Safety Method GUID: %s" % (str(woohooSafetyMethod.GUID)), This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
					continue

				if not woohooSafetyMethod.CompoundingMethod:
					continue

				countedSafetyMethod = True

				safetyMethodSeed = woohooSafetyMethod.GetUniqueSeed()
				arrivingPercentage *= performanceTypeInfo.GenerateSpermArrivingPercentage(seed = generationBaseSeed + safetyMethodSeed)  # type: float

			if not countedSafetyMethod:
				for performanceSelection in self:  # type: MethodPerformanceSelection
					if not isinstance(performanceSelection, MethodPerformanceSelection):
						continue  # No need to log this, we would have already done so in the last loop.

					woohooSafetyMethod = performanceSelection.WoohooSafetyMethod  # type: WoohooSafetyMethod
					performanceTypeInfo = performanceSelection.SelectedPerformanceTypeInfo  # type: WoohooSafetyMethod.PerformanceTypeInfo

					if performanceTypeInfo is None:
						continue  # No need to log this, we would have already done so in the last loop.

					if woohooSafetyMethod.CompoundingMethod:
						continue

					safetyMethodSeed = woohooSafetyMethod.GetUniqueSeed()
					arrivingPercentage = performanceTypeInfo.GenerateSpermArrivingPercentage(seed = generationBaseSeed + safetyMethodSeed)  # type: float
					break

			return arrivingPercentage

	def HandlePostUse (self, inseminatedSimInfo: typing.Optional[sim_info.SimInfo], sourceSimInfo: typing.Optional[sim_info.SimInfo]) -> None:
		for performanceSelection in self:  # type: MethodPerformanceSelection
			performanceSelection.WoohooSafetyMethod.HandlePostUse(inseminatedSimInfo, sourceSimInfo, performanceSelection.SelectedPerformanceType)

def GetWoohooSafetyMethods () -> typing.List[WoohooSafetyMethod]:
	"""
	Get all methods that may be used by sims during woohoo to prevent pregnancy.
	"""

	return list(_woohooSafetyMethods.values())

def GetWoohooSafetyMethodByGUID (targetGUID: int) -> typing.Optional[WoohooSafetyMethod]:
	"""
	Get the first woohoo safety method with this GUID. This will return None if no such method exists.
	"""

	return _woohooSafetyMethods.get(targetGUID, None)

def GetAvailableWoohooSafetyMethods (targetSimInfo: sim_info.SimInfo) -> typing.List[WoohooSafetyMethod]:
	"""
	Get all woohoo safety methods that the target sim can use. This may incorrectly return false for non-instanced sims; we cannot read the inventory
	of sims not instanced.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	availableSafetyMethods = list()  # type: typing.List[WoohooSafetyMethod]

	for woohooSafetyMethod in _woohooSafetyMethods.values():  # type: WoohooSafetyMethod
		if woohooSafetyMethod.IsAvailable(targetSimInfo):
			availableSafetyMethods.append(woohooSafetyMethod)

	return availableSafetyMethods

def GetUsingWoohooSafetyMethods (targetSimInfo: sim_info.SimInfo) -> typing.List[WoohooSafetyMethod]:
	"""
	Get all woohoo safety methods target sim should use and that are available to them.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	usingSafetyMethods = list()  # type: typing.List[WoohooSafetyMethod]

	for woohooSafetyMethod in GetAvailableWoohooSafetyMethods(targetSimInfo):  # type: WoohooSafetyMethod
		if IsUsingWoohooSafetyMethod(woohooSafetyMethod, targetSimInfo):
			usingSafetyMethods.append(woohooSafetyMethod)

	return usingSafetyMethods

def IsUsingWoohooSafetyMethod (woohooSafetyMethod: WoohooSafetyMethod, targetSimInfo: sim_info.SimInfo) -> bool:
	"""
	Get whether or not the target sim should use the specified woohoo safety method if available.
	"""

	if not isinstance(woohooSafetyMethod, WoohooSafetyMethod):
		raise Exceptions.IncorrectTypeException(woohooSafetyMethod, "woohooSafetyMethod", (WoohooSafetyMethod,))

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	if woohooSafetyMethod.GUID is None:
		Debug.Log("Attempted to get the 'is using' value for a woohoo device with no guid.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
		return woohooSafetyMethod.UsingByDefault

	woohooSafetyMethodUse = SimSettings.WoohooSafetyMethodUse.Get(str(targetSimInfo.id))  # type: typing.Dict[int, bool]
	return woohooSafetyMethodUse.get(woohooSafetyMethod.GUID, woohooSafetyMethod.UsingByDefault)

def SetIsUsingWoohooSafetyMethod (woohooSafetyMethod: WoohooSafetyMethod, targetSimInfo: sim_info.SimInfo, isUsing: bool) -> None:
	"""
	Set whether or not the target sim should use the specified woohoo safety method if available.
	"""

	if not isinstance(woohooSafetyMethod, WoohooSafetyMethod):
		raise Exceptions.IncorrectTypeException(woohooSafetyMethod, "woohooSafetyMethod", (WoohooSafetyMethod,))

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	if not isinstance(isUsing, bool):
		raise Exceptions.IncorrectTypeException(isUsing, "isUsing", (bool,))

	if woohooSafetyMethod.GUID is None:
		Debug.Log("Attempted to set 'is using' value for a woohoo device with no guid.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
		return

	woohooSafetyMethodUse = SimSettings.WoohooSafetyMethodUse.Get(str(targetSimInfo.id))  # type: typing.Dict[int, bool]
	woohooSafetyMethodUse[woohooSafetyMethod.GUID] = isUsing
	SimSettings.WoohooSafetyMethodUse.Set(str(targetSimInfo.id), woohooSafetyMethodUse)

def _Setup () -> None:
	snippets.define_snippet(_woohooSafetyMethodSnippetName, WoohooSafetyMethod.TunableFactory())
	MainSnippets.SetupSnippetScanning(_woohooSafetyMethodSnippetName, _WoohooSafetyMethodsScanningCallback)

	snippets.define_snippet(_limitedUseWoohooSafetyMethodSnippetName, LimitedUseWoohooSafetyMethod.TunableFactory())
	MainSnippets.SetupSnippetScanning(_limitedUseWoohooSafetyMethodSnippetName, _WoohooSafetyMethodsScanningCallback)

def _WoohooSafetyMethodsScanningCallback (woohooSafetyMethodSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
	global _woohooSafetyMethods

	for woohooSafetyMethodSnippet in woohooSafetyMethodSnippets:  # type: snippets.SnippetInstanceMetaclass
		woohooSafetyMethod = woohooSafetyMethodSnippet.value  # type: WoohooSafetyMethod
		woohooSafetyMethod.GUID = woohooSafetyMethodSnippet.guid64

		_woohooSafetyMethods[woohooSafetyMethod.GUID] = woohooSafetyMethod

_Setup()
