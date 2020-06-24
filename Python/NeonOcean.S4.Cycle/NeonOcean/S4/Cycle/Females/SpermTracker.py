from __future__ import annotations

import random
import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Cycle.Males import Sperm
from NeonOcean.S4.Cycle.Tools import Probability
from NeonOcean.S4.Main.Tools import Classes, Exceptions, Savable

from sims import sim_info

class SpermTracker(ReproductionShared.TrackerBase):
	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self._activeSperm = list()  # type: typing.List[Sperm.Sperm]

		self.RegisterSavableAttribute(Savable.ListedSavableAttributeHandler(
			"ActiveSperm",
			"_activeSperm",
			lambda: Sperm.Sperm(),
			lambda: list(),
			requiredSuccess = False
		))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		return FemalesShared.SpermTrackerIdentifier

	@property
	def ActiveSperm (self) -> typing.List[Sperm.Sperm]:
		"""
		All active sperm objects. Sperm objects cannot be added or removed by modifying this list, used the release and remove
		sperm methods instead.
		"""

		return list(self._activeSperm)

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return FemalesShared.ShouldHaveFemaleTrackers(targetSimInfo)

	def ReleaseSperm (self, releasingSperm: Sperm.Sperm) -> None:
		"""
		Release sperm into this reproductive system. If the sperm object has already been released nothing will happen.
		:param releasingSperm: The sperm object to be released.
		:type releasingSperm: Sperm.Sperm
		"""

		if not isinstance(releasingSperm, Sperm.Sperm):
			raise Exceptions.IncorrectTypeException(releasingSperm, "releasingSperm", (Sperm.Sperm,))

		if not releasingSperm in self._activeSperm:
			self._SetSpermCallbacks(releasingSperm)
			self._activeSperm.append(releasingSperm)

			if self.TrackingSystem.Simulating:
				self.TrackingSystem.Simulation.NeedToPlan = True

	def RemoveSperm (self, removingSperm: Sperm.Sperm) -> None:
		"""
		Remove already released sperm from this reproductive system. If the sperm object was never released nothing will happen.
		:param removingSperm: The sperm object to be removed.
		:type removingSperm: Sperm.Sperm
		"""

		if not isinstance(removingSperm, Sperm.Sperm):
			raise Exceptions.IncorrectTypeException(removingSperm, "removingSperm", (Sperm.Sperm,))

		activeSpermIndex = 0
		while activeSpermIndex < len(self._activeSperm):
			activeSperm = self._activeSperm[activeSpermIndex]  # type: Sperm.Sperm

			if activeSperm == removingSperm:
				self._UnsetSpermCallbacks(activeSperm)
				self._activeSperm.pop(activeSpermIndex)

				if self.TrackingSystem.Simulating:
					self.TrackingSystem.Simulation.NeedToPlan = True

			activeSpermIndex += 1

	def ClearAllSperm (self) -> None:
		"""
		Clear all sperm tracked by this sperm tracker.
		"""

		for activeSperm in self._activeSperm:  # type: Sperm.Sperm
			self._UnsetSpermCallbacks(activeSperm)

		self._activeSperm = list()

		if self.TrackingSystem.Simulating:
			self.TrackingSystem.Simulation.NeedToPlan = True

	def GetDebugNotificationString (self) -> str:
		if len(self._activeSperm) == 0:
			return ""

		debugString = "Active sperm:"

		for activeSpermIndex in range(len(self._activeSperm)):  # type: int
			activeSperm = self._activeSperm[activeSpermIndex]  # type: Sperm.Sperm

			debugString += ("\n  [%s] " % activeSpermIndex) + activeSperm.GetDebugNotificationString().replace("\n", "\n  ")

		return debugString

	def Verify (self) -> None:
		replanSimulation = False  # type: bool

		for activeSperm in self.ActiveSperm:  # type: Sperm.Sperm
			if activeSperm.Decayed:
				self.RemoveSperm(activeSperm)
				replanSimulation = True

		if replanSimulation and self.TrackingSystem.Simulating:
			self.TrackingSystem.Simulation.NeedToPlan = True

	def _FertilizationChanceFunction (self, spermCount: int, equalChanceSpermCount: int) -> float:
		return -(equalChanceSpermCount / (equalChanceSpermCount + spermCount)) + 1

	def _SetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.OvumTrackerIdentifier:
			self._SetOvumTrackerCallbacks(tracker)

	def _SetOvumTrackerCallbacks (self, tracker) -> None:
		tracker.OvumFertilizationTestingEvent += self._OvumFertilizationTestingCallback
		tracker.OvumFertilizingEvent += self._OvumFertilizingCallback

	def _UnsetTrackerCallbacks (self, tracker) -> None:
		if tracker.TypeIdentifier == FemalesShared.OvumTrackerIdentifier:
			self._UnsetOvumTrackerCallbacks(tracker)

	def _UnsetOvumTrackerCallbacks  (self, tracker) -> None:
		tracker.OvumFertilizationTestingEvent -= self._OvumFertilizationTestingCallback
		tracker.OvumFertilizingEvent -= self._OvumFertilizingCallback

	def _SetSpermCallbacks (self, sperm: Sperm.Sperm) -> None:
		self._UnsetSpermCallbacks(sperm)

		sperm.DecayedCallback = self._SpermDecayedCallback

	def _UnsetSpermCallbacks (self, sperm: Sperm.Sperm) -> None:
		sperm.DecayedCallback = None

	def _OnAdded(self) -> None:
		self.TrackingSystem.TrackerAddedEvent += self._TrackerAddedCallback
		self.TrackingSystem.TrackerRemovedEvent += self._TrackerRemovedCallback

		for tracker in self.TrackingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._SetTrackerCallbacks(tracker)

	def _OnRemoving(self) -> None:
		self.TrackingSystem.TrackerAddedEvent -= self._TrackerAddedCallback
		self.TrackingSystem.TrackerRemovedEvent -= self._TrackerRemovedCallback

		for tracker in self.TrackingSystem.Trackers:  # type: ReproductionShared.TrackerBase
			self._UnsetTrackerCallbacks(tracker)

	# noinspection PyUnusedLocal
	def _SpermSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		for activeSperm in self.ActiveSperm:  # type: Sperm.Sperm
			activeSperm.Simulate(simulation, ticks, reproductiveTimeMultiplier)

	def _PlanSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PlanSimulation(simulation)

		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		for activeSperm in self.ActiveSperm:
			activeSperm.PlanSimulation(simulation, reproductiveTimeMultiplier)

	def _PrepareForSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PrepareForSimulation(simulation)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(-20, self._SpermSimulationPhase)
		)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return FemalesShared.GetSpermTrackerReproductiveTimeMultiplier()

	def _OnLoaded (self) -> None:
		for activeSperm in self._activeSperm:
			self._SetSpermCallbacks(activeSperm)

	def _OnLoading (self) -> None:
		for activeSperm in self._activeSperm:
			self._UnsetSpermCallbacks(activeSperm)

	def _OnResetted (self) -> None:
		for activeSperm in self._activeSperm:
			self._UnsetSpermCallbacks(activeSperm)

	# noinspection PyUnusedLocal
	def _TrackerAddedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._SetTrackerCallbacks(eventArguments.Tracker)

	# noinspection PyUnusedLocal
	def _TrackerRemovedCallback (self, owner: ReproductionShared.ReproductiveSystem, eventArguments: CycleEvents.TrackerAddedArguments) -> None:
		self._UnsetTrackerCallbacks(eventArguments.Tracker)

	def _SpermDecayedCallback (self, sperm: Sperm.Sperm) -> None:
		self.RemoveSperm(sperm)

	# noinspection PyUnusedLocal
	def _OvumFertilizationTestingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.OvumFertilizationTestingArguments) -> None:
		spermTrackerGuide = CycleGuides.SpermTrackerGuide.GetGuide(self.TrackingSystem.GuideGroup)  # type: CycleGuides.SpermTrackerGuide

		totalMotileSperm = 0  # type: int

		for activeSperm in self._activeSperm:  # type: Sperm.Sperm
			totalMotileSperm += activeSperm.MotileSpermCount

		fertilizationChance = self._FertilizationChanceFunction(totalMotileSperm, spermTrackerGuide.FertilizationEqualChanceCount)  # type: float
		random.seed(eventArguments.Seed + -762057032)
		fertilizationRoll = random.random()  # type: float

		if fertilizationRoll <= fertilizationChance:
			eventArguments.Fertilizing.Value = True

	# noinspection PyUnusedLocal
	def _OvumFertilizingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.OvumFertilizingArguments) -> None:
		if eventArguments.FertilizerChosen:
			return

		spermOptions = list()

		for activeSperm in self._activeSperm:  # type: Sperm.Sperm
			spermOptions.append(
				Probability.Option(str(activeSperm.UniqueIdentifier), activeSperm.SpermCount)
			)

		chosenSpermOption = Probability.Probability(spermOptions).ChooseOption(eventArguments.Seed + -257141210)  # type: Probability.Option
		chosenSperm = None  # type: typing.Optional[Sperm.Sperm]

		for activeSperm in self._activeSperm:  # type: Sperm.Sperm
			if chosenSpermOption.Identifier == str(activeSperm.UniqueIdentifier):
				chosenSperm = activeSperm
				break

		assert chosenSperm is not None

		eventArguments.Fertilizer = chosenSperm.Source
		eventArguments.FertilizingObject = chosenSperm

		random.seed(eventArguments.Seed + -808509545)
		viabilityRoll = random.random()

		eventArguments.FertilizationViability.Value = viabilityRoll <= chosenSperm.ViablePercentage
		eventArguments.FertilizerChosen = True
