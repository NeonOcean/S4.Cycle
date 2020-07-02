from __future__ import annotations

import random
import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Ovum, Shared as FemalesShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Types
from sims import sim_info


class OvumTrackerSimulationMemory:
	def __init__ (self):
		self.OvumFertilizationTesting = dict()  # type: typing.Dict[str, CycleEvents.OvumFertilizationTestingArguments]

class OvumTracker(ReproductionShared.TrackerBase):
	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self.OvumGeneratingEvent = Events.EventHandler()
		self.OvumReleasedEvent = Events.EventHandler()
		self.OvumFertilizationTestingEvent = Events.EventHandler()
		self.OvumFertilizingEvent = Events.EventHandler()
		self.OvumFertilizedEvent = Events.EventHandler()
		self.OvumImplantationTestingEvent = Events.EventHandler()

		self.OvumGeneratingEvent += self._OvumGeneratingCallback
		self.OvumImplantationTestingEvent += self._OvumImplantationTestingCallback

		self._activeOva = list()  # type: typing.List[Ovum]
		self._ovumObjectsGenerated = 0  # type: int

		self.RegisterSavableAttribute(Savable.ListedSavableAttributeHandler(
			"ActiveOva",
			"_activeOva",
			lambda: Ovum.Ovum(),
			lambda: list(),
			requiredSuccess = False
		))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("OvumObjectsGenerated", "_ovumObjectsGenerated", self.OvumObjectsGenerated, requiredSuccess = False))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		return FemalesShared.OvumTrackerIdentifier

	@property
	def SimulationMemoryKey (self) -> str:
		return self.TypeIdentifier

	@property
	def OvumGeneratingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when an ovum object needs to be created.
		The event arguments parameter should be a 'OvumGeneratingArguments' object.
		"""

		return self._ovumGeneratingEvent

	@OvumGeneratingEvent.setter
	def OvumGeneratingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "OvumGeneratingEvent", (Events.EventHandler,))

		self._ovumGeneratingEvent = value

	@property
	def OvumReleasedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered every time an egg cell has been released from the ovaries.
		The event arguments parameter should be a 'OvumReleasedArguments' object.
		"""

		return self._ovumReleasedEvent

	@OvumReleasedEvent.setter
	def OvumReleasedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "OvumReleasedEvent", (Events.EventHandler,))

		self._ovumReleasedEvent = value

	@property
	def OvumFertilizationTestingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered to determine if an ovum should be fertilized in a specified time span.
		The event arguments parameter should be a 'OvumFertilizationTestingArguments' object.
		"""

		return self._ovumFertilizationTestingEvent

	@OvumFertilizationTestingEvent.setter
	def OvumFertilizationTestingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "OvumFertilizationTestingEvent", (Events.EventHandler,))

		self._ovumFertilizationTestingEvent = value

	@property
	def OvumFertilizingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered to determine fertilization values, such as the source and viability.
		The event arguments parameter should be a 'OvumFertilizingArguments' object.
		"""

		return self._ovumFertilizingEvent

	@OvumFertilizingEvent.setter
	def OvumFertilizingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "OvumFertilizingEvent", (Events.EventHandler,))

		self._ovumFertilizingEvent = value

	@property
	def OvumFertilizedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered to handle special post ovum fertilization work.
		The event arguments parameter should be a 'OvumFertilizedArguments' object.
		"""

		return self._ovumFertilizedEvent

	@OvumFertilizedEvent.setter
	def OvumFertilizedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "OvumFertilizedEvent", (Events.EventHandler,))

		self._ovumFertilizedEvent = value

	@property
	def OvumImplantationTestingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered to determine if an ovum should implant in the uterus in a specified time span.
		The event arguments parameter should be a 'ImplantationTestingArguments' object.
		"""

		return self._ovumImplantationTestingEvent

	@OvumImplantationTestingEvent.setter
	def OvumImplantationTestingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "OvumImplantationTestingEvent", (Events.EventHandler,))

		self._ovumImplantationTestingEvent = value

	@property
	def ActiveOva (self) -> typing.List[Ovum.Ovum]:
		"""
		All active ova. Egg cells cannot be added or removed by modifying this list, used the release and remove ovum methods instead.
		"""

		return list(self._activeOva)

	@property
	def OvumObjectsGenerated (self) -> int:
		"""
		The total number of ovum objects that have been generated by this ovum tracker.
		"""

		return self._ovumObjectsGenerated

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return FemalesShared.ShouldHaveFemaleTrackers(targetSimInfo)

	def DoOvumFertilizationTesting (self, ovum: Ovum.Ovum) -> CycleEvents.OvumFertilizationTestingArguments:
		"""
		Test if an ovum should be fertilized.
		:param ovum: The ovum object that this test is being run for.
		:type ovum: Ovum.Ovum
		:return: Testing event arguments that carry information on whether or not an ovum should be fertilized.
		:rtype: EventsOva.OvumFertilizationTestingArguments
		"""

		if not isinstance(ovum, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(ovum, "ovum", (Ovum.Ovum,))

		eventsSeed = ovum.FertilizationSeed + 71299844
		eventArguments = CycleEvents.OvumFertilizationTestingArguments(eventsSeed, ovum)  # type: CycleEvents.OvumFertilizationTestingArguments

		for ovumFertilizationTestingCallback in self.OvumFertilizationTestingEvent:
			try:
				ovumFertilizationTestingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call ovum fertilization testing callback '" + Types.GetFullName(ovumFertilizationTestingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = ovumFertilizationTestingCallback)

		return eventArguments

	def DoOvumImplantationTesting (self, ovum: Ovum.Ovum) -> CycleEvents.OvumImplantationTestingArguments:
		"""
		Test if an ovum can implant and begin a pregnancy.
		:param ovum: The ovum object that this test is being run for.
		:type ovum: Ovum.Ovum
		:return: Testing event arguments that carry information on whether or not an ovum should implant.
		:rtype:  EventsOva.OvumImplantationTestingArguments
		"""

		if not isinstance(ovum, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(ovum, "ovum", (Ovum.Ovum,))

		eventsSeed = ovum.FertilizationSeed + -865356260
		eventArguments = CycleEvents.OvumImplantationTestingArguments(eventsSeed, ovum)  # type: CycleEvents.OvumImplantationTestingArguments

		for ovumImplantationTestingCallback in self.OvumImplantationTestingEvent:
			try:
				ovumImplantationTestingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call ovum implantation testing callback '" + Types.GetFullName(ovumImplantationTestingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = ovumImplantationTestingCallback)

		return eventArguments

	def ReleaseOvum (self, releasingOvum: Ovum.Ovum) -> None:
		"""
		Release an egg cell into this reproductive system. If the ovum has already been released nothing will happen.
		:param releasingOvum: The ovum to be released.
		:type releasingOvum: Ovum.Ovum
		"""

		if not isinstance(releasingOvum, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(releasingOvum, "releasingOvum", (Ovum.Ovum,))

		if not releasingOvum in self._activeOva:
			self._SetOvumCallbacks(releasingOvum)
			self._activeOva.append(releasingOvum)

			if self.TrackingSystem.Simulating:
				self.TrackingSystem.Simulation.NeedToPlan = True

	def GenerateOvum (self) -> Ovum.Ovum:
		"""
		Create an ovum object based off and made for this reproductive system.
		"""

		generationSeed = self.TrackingSystem.CurrentSeed  # type: int

		random.seed(self.OvumObjectsGenerated)
		generationSeed += random.randint(-1000000000, 1000000000)

		ovum = Ovum.Ovum()
		ovumGuide = ovum.GetOvumGuide(self.TrackingSystem)  # type: CycleGuides.OvumGuide
		ovumGeneratingArguments = CycleEvents.OvumGeneratingArguments(generationSeed, ovum, ovumGuide)
		self.OvumGeneratingEvent.Invoke(self, ovumGeneratingArguments)
		ovum.Generate(ovumGeneratingArguments)

		self._ovumObjectsGenerated += 1

		return ovum

	def GenerateAndReleaseOvum (self) -> Ovum.Ovum:
		"""
		Generate and then release an ovum in this reproductive system.
		"""

		releasingOvum = self.GenerateOvum()
		self.ReleaseOvum(releasingOvum)
		return releasingOvum

	def RemoveOvum (self, removingOvum: Ovum.Ovum) -> None:
		"""
		Remove an already released egg cell from this reproductive system. If the ovum was never released nothing will happen.
		:param removingOvum: The ovum to be removed.
		:type removingOvum: Ovum.Ovum
		"""

		if not isinstance(removingOvum, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(removingOvum, "removingOvum", (Ovum.Ovum,))

		activeOvumIndex = 0
		while activeOvumIndex < len(self._activeOva):
			activeOvum = self._activeOva[activeOvumIndex]  # type: Ovum.Ovum

			if activeOvum == removingOvum:
				self._UnsetOvumCallbacks(activeOvum)
				self._activeOva.pop(activeOvumIndex)

				if self.TrackingSystem.Simulating:
					self.TrackingSystem.Simulation.NeedToPlan = True

			activeOvumIndex += 1

	def ClearAllOva (self, clearFertilized: bool = True) -> None:
		"""
		Clear all egg cells tracked by this ovum tracker.
		"""

		if not isinstance(clearFertilized, bool):
			raise Exceptions.IncorrectTypeException(clearFertilized, "clearFertilized", (bool,))

		clearedActiveOva = list()  # type: typing.List[Ovum.Ovum]

		for activeOvum in self._activeOva:  # type: Ovum.Ovum
			if not clearFertilized and activeOvum.Fertilized:
				clearedActiveOva.append(activeOvum)
				continue

			self._UnsetOvumCallbacks(activeOvum)

		self._activeOva = list()

		if self.TrackingSystem.Simulating:
			self.TrackingSystem.Simulation.NeedToPlan = True

	def FertilizeOvum (self, fertilizingOvum: Ovum.Ovum) -> None:
		"""
		Run the fertilization events and use them to fertilize this ovum.
		"""

		if not isinstance(fertilizingOvum, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(fertilizingOvum, "fertilizingOvum", (Ovum.Ovum,))

		fertilizingEventSeed = fertilizingOvum.FertilizationSeed + 136275445
		fertilizingEventArguments = CycleEvents.OvumFertilizingArguments(fertilizingEventSeed, fertilizingOvum)  # type: CycleEvents.OvumFertilizingArguments

		for ovumFertilizingCallback in self.OvumFertilizingEvent:
			try:
				ovumFertilizingCallback(self, fertilizingEventArguments)
			except:
				Debug.Log("Failed to call ovum fertilizing callback '" + Types.GetFullName(ovumFertilizingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = ovumFertilizingCallback)

		fertilizingOvum.FertilizeWithEvent(fertilizingEventArguments)

		if self.TrackingSystem.Simulating:
			self.TrackingSystem.Simulation.NeedToPlan = True

		fertilizedEventArguments = CycleEvents.OvumFertilizedArguments(fertilizingEventArguments)  # type: CycleEvents.OvumFertilizedArguments

		for ovumFertilizedCallback in self.OvumFertilizedEvent:
			try:
				ovumFertilizedCallback(self, fertilizedEventArguments)
			except:
				Debug.Log("Failed to call ovum fertilized callback '" + Types.GetFullName(ovumFertilizedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = ovumFertilizedCallback)

	def ImplantIfPossible (self, implantingOvum: Ovum.Ovum, forceImplant: bool = False) -> bool:
		"""
		Attempt to implant an ovum in the uterus. This will run the implantation testing event and do nothing if it indicates implantation should not happen.
		:param implantingOvum: The ovum trying to implant.
		:type implantingOvum: Ovum.Ovum
		:param forceImplant: Whether or not we should skip implantation testing.
		:type forceImplant: bool
		:return: True if implantation was successful, false if not.
		:rtype: bool
		"""

		if not isinstance(implantingOvum, Ovum.Ovum):
			raise Exceptions.IncorrectTypeException(implantingOvum, "implantingOvum", (Ovum.Ovum,))

		if not isinstance(forceImplant, bool):
			raise Exceptions.IncorrectTypeException(forceImplant, "forceImplant", (bool,))

		canImplant = True  # type: bool

		if not forceImplant:
			implantationTesting = self.DoOvumImplantationTesting(implantingOvum)  # type: CycleEvents.OvumImplantationTestingArguments
			canImplant = implantationTesting.CanImplant()

		if canImplant:
			pregnancyTracker = self.TrackingSystem.GetTracker(FemalesShared.PregnancyTrackerIdentifier)
			pregnancyTracker.StartPregnancy(implantingOvum.Source, implantingOvum.Fertilizer)

		return True

	def GetDebugNotificationString (self) -> str:
		if len(self._activeOva) == 0:
			return ""

		debugString = "Active ova:"

		for activeOvumIndex in range(len(self._activeOva)):  # type: int
			activeOvum = self._activeOva[activeOvumIndex]  # type: Ovum.Ovum

			debugString += ("\n  [%s] " % activeOvumIndex) + activeOvum.GetDebugNotificationString().replace("\n", "\n  ")

		return debugString

	def Verify (self) -> None:
		replanSimulation = False  # type: bool

		for activeOvum in self.ActiveOva:  # type: Ovum.Ovum
			if activeOvum.Decayed:
				self.RemoveOvum(activeOvum)
				replanSimulation = True

		if replanSimulation and self.TrackingSystem.Simulating:
			self.TrackingSystem.Simulation.NeedToPlan = True

	def _SetOvumCallbacks (self, ovum: Ovum.Ovum) -> None:
		self._UnsetOvumCallbacks(ovum)

		ovum.DecayedCallback = self._OvumDecayedCallback
		ovum.AttemptImplantationCallback = self._OvumAttemptImplantationCallback

	def _UnsetOvumCallbacks (self, ovum: Ovum.Ovum) -> None:
		ovum.DecayedCallback = None
		ovum.AttemptImplantationCallback = None

	# noinspection PyUnusedLocal
	def _OvumSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]
		simulatingMinutes = ReproductionShared.TicksToReproductiveMinutes(ticks, reproductiveTimeMultiplier)  # type: float

		simulationMemoryKey = self.SimulationMemoryKey
		simulationMemoryExists = simulationMemoryKey in simulation.Memory  # type: bool
		simulationMemory = simulation.Memory.get(simulationMemoryKey, OvumTrackerSimulationMemory())  # type: OvumTrackerSimulationMemory

		for activeOvum in self.ActiveOva:  # type: Ovum.Ovum
			if not activeOvum.Fertilized:
				ovumFertilizationTesting = simulationMemory.OvumFertilizationTesting.get(str(activeOvum.UniqueIdentifier), None)  # type: typing.Optional[CycleEvents.OvumFertilizationTestingArguments]

				if ovumFertilizationTesting is None:
					Debug.Log("Expected the ovum fertilization testing' for an ovum with the identifier '" + str(activeOvum.UniqueIdentifier) + "' to be in the simulation memory, but it wasn't there.\n" + self.DebugInformation,
							  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self.TrackingSystem)

					# TODO An minor bug occurred around here and could not be reproduced. Set the cycle progress for Cassandra to 0.46, had her and Shawn try for a baby twice, upon ovum release(?) an error occurred because there was no fertilization testing for the ovum in the memory. Fertilization got through in the next simulation, the ovum became non viable. Reproductive speed was 0.15.
					# TODO Update - This just keeps happening randomly. Occasionally, I load up the cassandra save and Holly Alto and Jade Rosa may randomly cause the above error message to appear. It doesn't even happen every time..
					ovumFertilizationTesting = self.DoOvumFertilizationTesting(activeOvum)  # type: CycleEvents.OvumFertilizationTestingArguments
					simulationMemory.OvumFertilizationTesting[str(activeOvum.UniqueIdentifier)] = ovumFertilizationTesting

				if ovumFertilizationTesting.ShouldFertilize():
					self.FertilizeOvum(activeOvum)

				ovumFertilizationTesting.IncreaseTimeSinceTest(simulatingMinutes)

			activeOvum.Simulate(simulation, ticks, reproductiveTimeMultiplier)

	def _PlanSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PlanSimulation(simulation)

		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		trackerSimulationMemory = OvumTrackerSimulationMemory()  # type: OvumTrackerSimulationMemory

		for activeOvum in self.ActiveOva:  # type: Ovum.Ovum
			activeOvum.PlanSimulation(simulation, reproductiveTimeMultiplier)

			if not activeOvum.Fertilized:
				ovumFertilizationTesting = self.DoOvumFertilizationTesting(activeOvum)
				trackerSimulationMemory.OvumFertilizationTesting[str(activeOvum.UniqueIdentifier)] = ovumFertilizationTesting

		simulation.Memory[self.SimulationMemoryKey] = trackerSimulationMemory

	def _PrepareForSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PrepareForSimulation(simulation)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(20, self._OvumSimulationPhase)
		)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return FemalesShared.GetOvumTrackerReproductiveTimeMultiplier()

	def _OnLoaded (self) -> None:
		for activeOva in self._activeOva:
			self._SetOvumCallbacks(activeOva)

	def _OnLoading (self) -> None:
		for activeOva in self._activeOva:
			self._UnsetOvumCallbacks(activeOva)

	def _OnResetted (self) -> None:
		for activeOva in self._activeOva:
			self._UnsetOvumCallbacks(activeOva)

	def _OvumDecayedCallback (self, ovum: Ovum.Ovum) -> None:
		self.RemoveOvum(ovum)

	def _OvumAttemptImplantationCallback (self, ovum: Ovum.Ovum) -> None:
		self.RemoveOvum(ovum)
		self.ImplantIfPossible(ovum)

	# noinspection PyUnusedLocal
	def _OvumGeneratingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.OvumGeneratingArguments) -> None:
		eventArguments.Source = self.TrackingSystem.SimInfo
		eventArguments.FertilizationSeed = eventArguments.Seed + 996152026

	# noinspection PyUnusedLocal
	def _OvumImplantationTestingCallback (self, owner: ReproductionShared.TrackerBase, eventArguments: CycleEvents.OvumImplantationTestingArguments) -> None:
		if not eventArguments.TargetedObject.Viable:
			eventArguments.ImplantationPossible.Value = False
