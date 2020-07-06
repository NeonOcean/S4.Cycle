from __future__ import annotations

import typing

from sims import sim_info
from NeonOcean.S4.Cycle import Reproduction, ReproductionShared
from NeonOcean.S4.Cycle.Safety import WoohooSafety
from NeonOcean.S4.Cycle import Guides as CycleGuides
from NeonOcean.S4.Cycle.Males import Sperm, Shared as MalesShared
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Main.Tools import Exceptions

def AutoInseminate (
		inseminatedSimInfo: sim_info.SimInfo,
		sourceSimInfo: sim_info.SimInfo,
		tryingForBaby: bool = True,
		generateGenericSperm: bool = False,
		woohooSafetyMethods: typing.Optional[typing.List[WoohooSafety.WoohooSafetyMethod]] = None,
		arrivingSpermPercentage: typing.Optional[float] = None) -> None:

	"""
	A simple function to add sperm to a sim.
	:param inseminatedSimInfo: The sim who is being inseminated.
	:type inseminatedSimInfo: sim_info.SimInfo
	:param sourceSimInfo: The sim who is providing the sperm.
	:type sourceSimInfo: sim_info.SimInfo
	:param tryingForBaby: Whether or not the sims are trying for a baby. Sims trying to a baby will not use any devices to prevent pregnancy, such as condoms.
	:type tryingForBaby: bool
	:param generateGenericSperm: Whether or not we should generate a generic sperm object if the source sim does not have a sperm production tracker.
	:type generateGenericSperm: bool
	:param woohooSafetyMethods: Allows for the woohoo safety methods that would normally be used by the two sims to be overridden.
	:type woohooSafetyMethods: typing.Optional[typing.List[Safety.WoohooSafetyMethod]]
	:param arrivingSpermPercentage: Allows for the sperm arrival percentage to be overridden. Other than the arriving sperm percentage, which will be
	overridden, we will act as though the appropriate woohoo safety methods have been used. This must be between 0 and 1.
	:type arrivingSpermPercentage: typing.Optional[float]
	"""

	if not isinstance(inseminatedSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(inseminatedSimInfo, "inseminatedSimInfo", (sim_info.SimInfo, ))

	if not isinstance(sourceSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(sourceSimInfo, "sourceSimInfo", (sim_info.SimInfo, ))

	if not isinstance(tryingForBaby, bool):
		raise Exceptions.IncorrectTypeException(tryingForBaby, "tryingForBaby", (bool, ))

	if not isinstance(generateGenericSperm, bool):
		raise Exceptions.IncorrectTypeException(generateGenericSperm, "generateGenericSperm", (bool, ))

	if not isinstance(woohooSafetyMethods, list) and woohooSafetyMethods is not None:
		raise Exceptions.IncorrectTypeException(woohooSafetyMethods, "woohooSafetyMethods", (list, None))

	if woohooSafetyMethods is not None:
		for woohooSafetyMethodIndex in range(len(woohooSafetyMethods)):  # type: int
			woohooSafetyMethod = woohooSafetyMethods[woohooSafetyMethodIndex]  # type: WoohooSafety.WoohooSafetyMethod

			if not isinstance(woohooSafetyMethod, WoohooSafety.WoohooSafetyMethod):
				raise Exceptions.IncorrectTypeException(woohooSafetyMethod, "woohooSafetyMethod[%s]" % woohooSafetyMethodIndex, (WoohooSafety.WoohooSafetyMethod, ))

	if not isinstance(arrivingSpermPercentage, float) and arrivingSpermPercentage is not None:
		raise Exceptions.IncorrectTypeException(arrivingSpermPercentage, "arrivingSpermPercentage", (float, None))

	if arrivingSpermPercentage is not None:
		if not (0 < arrivingSpermPercentage < 1):
			raise ValueError("The parameter 'arrivingSpermPercentage' must be greater than or equal to 0 and less than or equal to 1.")

	inseminatedSystem = Reproduction.GetSimSystem(inseminatedSimInfo)  # type: typing.Union[ReproductionShared.ReproductiveSystem, None]

	if inseminatedSystem is None or not inseminatedSystem.HasTracker(FemalesShared.SpermTrackerIdentifier):
		return

	sourceSystem = Reproduction.GetSimSystem(sourceSimInfo)  # type: typing.Union[ReproductionShared.ReproductiveSystem, None]

	if sourceSystem is None or not sourceSystem.HasTracker(MalesShared.SpermProductionTrackerIdentifier):
		if not generateGenericSperm:
			return

		inseminatedSpermGuide = CycleGuides.SpermGuide.GetGuide(inseminatedSystem.GuideGroup)  # type: CycleGuides.SpermGuide
		inseminatedSpermTracker = inseminatedSystem.GetTracker(FemalesShared.SpermTrackerIdentifier)

		releasingSperm = Sperm.GenerateGenericSperm(source = sourceSimInfo, spermGuide = inseminatedSpermGuide)  # type: Sperm.Sperm
	else:
		inseminatedSpermTracker = inseminatedSystem.GetTracker(FemalesShared.SpermTrackerIdentifier)
		sourceSpermProductionTracker = sourceSystem.GetTracker(MalesShared.SpermProductionTrackerIdentifier)

		releasingSperm = sourceSpermProductionTracker.GenerateSperm()  # type: Sperm.Sperm

	if not tryingForBaby:
		if woohooSafetyMethods is None:
			woohooSafetyMethods = set()  # type: typing.Set[WoohooSafety.WoohooSafetyMethod]

			woohooSafetyMethods.update(WoohooSafety.GetUsingWoohooSafetyMethods(inseminatedSimInfo))
			woohooSafetyMethods.update(WoohooSafety.GetUsingWoohooSafetyMethods(sourceSimInfo))

			woohooSafetyMethods = list(woohooSafetyMethods)  # type: typing.List[WoohooSafety.WoohooSafetyMethod]

		methodPerformanceSelections = WoohooSafety.MethodPerformanceSelectionSet(woohooSafetyMethods)

		if arrivingSpermPercentage is None:
			arrivingSpermPercentage = methodPerformanceSelections.GenerateSpermArrivingPercentage()

		arrivingSpermCount = int(releasingSperm.SpermCount * arrivingSpermPercentage)  # type: int

		if arrivingSpermCount != 0:
			releasingSperm.SpermCount = arrivingSpermCount
			inseminatedSpermTracker.ReleaseSperm(releasingSperm)

		methodPerformanceSelections.HandlePostUse(inseminatedSimInfo, sourceSimInfo)
	else:
		inseminatedSpermTracker.ReleaseSperm(releasingSperm)
