from __future__ import annotations

import random
import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Ovum, Shared as FemalesShared
from NeonOcean.S4.Cycle.Females.Cycle import Base as CycleBase, Shared as CycleShared, Types as CycleTypes, OvumRelease as CycleOvumRelease
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Parse, Python, Savable, Types
from sims import sim_info_types, sim_info

class CycleTrackerSimulationMemory:
	def __init__ (self):
		self.CycleStartTesting = None  # type: typing.Optional[CycleEvents.CycleStartTestingArguments]

class CycleTracker(ReproductionShared.TrackerBase):
	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self.CycleStartTestingEvent = Events.EventHandler()
		self.CycleAbortTestingEvent = Events.EventHandler()
		self.CycleGeneratingEvent = Events.EventHandler()
		self.CycleChangedEvent = Events.EventHandler()
		self.CycleCompletedEvent = Events.EventHandler()
		self.CycleReleaseOvumTestingEvent = Events.EventHandler()

		self.CycleStartTestingEvent += self._CycleStartTestingCallback
		self.CycleAbortTestingEvent += self._CycleAbortTestingCallback

		self.CompletedInitialCycle = False
		self.CompletedFirstCycle = False

		self.CycleStartTestingSeed = None

		self.TimeSinceLastCycle = None
		self.LastCycleCompletionReason = None

		self.CurrentCycle = None

		self._cycleObjectsGenerated = 0  # type: int

		encodeLastCycleCompletionReason = lambda value: value.name if value is not None else None
		decodeLastCycleCompletionReason = lambda valueString: Parse.ParsePythonEnum(valueString, CycleShared.CompletionReasons) if valueString is not None else None

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("CompletedInitialCycle", "CompletedInitialCycle", self.CompletedInitialCycle, requiredSuccess = False))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("CompletedFirstCycle", "CompletedFirstCycle", self.CompletedFirstCycle, requiredSuccess = False))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("CycleStartTestingSeed", "CycleStartTestingSeed", self.CycleStartTestingSeed, requiredSuccess = False))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("TimeSinceLastCycle", "TimeSinceLastCycle", self.TimeSinceLastCycle, requiredSuccess = False))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler(
			"LastCycleCompletionReason",
			"LastCycleCompletionReason",
			self.LastCycleCompletionReason,
			requiredSuccess = False,
			encoder = encodeLastCycleCompletionReason,
			decoder = decodeLastCycleCompletionReason
		))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("CycleObjectsGenerated", "_cycleObjectsGenerated", self.CycleObjectsGenerated, requiredSuccess = False))

		self.RegisterSavableAttribute(Savable.DynamicSavableAttributeHandler(
			"CurrentCycle",
			"CurrentCycle",
			lambda typeIdentifier: CycleTypes.GetCycleType(typeIdentifier)(),
			lambda: None,
			requiredSuccess = False,
			nullable = True,
			multiType = True,
			typeFetcher = lambda attributeValue: attributeValue.TypeIdentifier,
			typeSavingKey = "CurrentCycleType"
		))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		return FemalesShared.CycleTrackerIdentifier

	@property
	def SimulationMemoryKey (self) -> str:
		return self.TypeIdentifier

	@property
	def CycleStartTestingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered to determine if the next cycle started during a simulation's tick step. And if so, what type of cycle it should be.
		The event arguments parameter should be a 'CycleStartTestingArguments' object.
		"""

		return self._cycleStartTestingEvent

	@CycleStartTestingEvent.setter
	def CycleStartTestingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "CycleStartTestingEvent", (Events.EventHandler,))

		self._cycleStartTestingEvent = value

	@property
	def CycleAbortTestingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered to determine if the active cycle needs to stop early.
		The event arguments parameter should be a 'CycleAbortTestingArguments' object.
		"""

		return self._cycleAbortTestingEvent

	@CycleAbortTestingEvent.setter
	def CycleAbortTestingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "CycleAbortTestingEvent", (Events.EventHandler,))

		self._cycleAbortTestingEvent = value

	@property
	def CycleGeneratingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a cycle object needs to be created.
		The event arguments parameter should be a 'CycleGeneratingArguments' object.
		"""

		return self._cycleGeneratingEvent

	@CycleGeneratingEvent.setter
	def CycleGeneratingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "CycleGeneratingEvent", (Events.EventHandler,))

		self._cycleGeneratingEvent = value

	@property
	def CycleChangedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when the current cycle is switched out for another one. Trying to set the current cycle within a callback for this event
		may cause an infinite loop.
		The event arguments parameter should be a 'CycleChangedArguments' object.
		"""

		return self._cycleChangedEvent

	@CycleChangedEvent.setter
	def CycleChangedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "CycleChangedEvent", (Events.EventHandler,))

		self._cycleChangedEvent = value

	@property
	def CycleCompletedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when the current cycle has completed.
		The event arguments parameter should be a 'CycleCompletedArguments' object.
		"""

		return self._cycleCompletedEvent

	@CycleCompletedEvent.setter
	def CycleCompletedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "CycleCompletedEvent", (Events.EventHandler,))

		self._cycleCompletedEvent = value

	@property
	def CycleReleaseOvumTestingEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a cycle is about to release an ovum to determine if we actually should.
		The event arguments parameter should be a 'CycleReleaseOvumTestingArguments' object.
		"""

		return self._cycleReleaseOvumTestingEvent

	@CycleReleaseOvumTestingEvent.setter
	def CycleReleaseOvumTestingEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "CycleReleaseOvumTestingEvent", (Events.EventHandler,))

		self._cycleReleaseOvumTestingEvent = value

	@property
	def CompletedInitialCycle (self) -> bool:
		"""
		Whether or not this sim has gone through the simulation of at least one cycle.
		"""

		return self._completedInitialCycle

	@CompletedInitialCycle.setter
	def CompletedInitialCycle (self, value) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "CompletedInitialCycle", (bool,))

		self._completedInitialCycle = value

	@property
	def RunningInitialCycle (self) -> bool:
		"""
		Whether or not this sim is currently on their first simulated cycle.
		"""

		return not self.CompletedInitialCycle and self.CurrentCycle is not None

	@property
	def CompletedFirstCycle (self) -> bool:
		"""
		Whether or not this sim has had their first menstruation.
		"""

		return self._completedFirstCycle

	@CompletedFirstCycle.setter
	def CompletedFirstCycle (self, value) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "CompletedFirstCycle", (bool,))

		self._completedFirstCycle = value

	@property
	def RunningFirstCycle (self) -> bool:
		"""
		Whether or not this sim is currently on their first cycle.
		"""

		return not self.CompletedFirstCycle and self.CurrentCycle is not None

	@property
	def CycleStartTestingSeed (self) -> typing.Optional[int]:
		return self._cycleStartTestingSeed

	@CycleStartTestingSeed.setter
	def CycleStartTestingSeed (self, value: typing.Optional[int]) -> None:
		if not isinstance(value, int) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "CycleStartTestingSeed", (int, None))

		self._cycleStartTestingSeed = value

	@property
	def TimeSinceLastCycle (self) -> typing.Union[float, int, None]:
		"""
		The amount of time in reproductive minutes since the last cycle ended. This will be None if the sim has not had a cycle yet.
		"""

		return self._timeSinceLastCycle

	@TimeSinceLastCycle.setter
	def TimeSinceLastCycle (self, value: typing.Union[float, int, None]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "TimeSinceLastCycle", (float, int, None))

		self._timeSinceLastCycle = value

	@property
	def TicksSinceLastCycle (self) -> typing.Union[float, int, None]:
		"""
		The amount of game ticks since the last cycle ended. This will be None if the sim has not had a cycle yet.
		"""

		return ReproductionShared.ReproductiveMinutesToTicks(self.TimeSinceLastCycle, self.ReproductiveTimeMultiplier)

	@property
	def LastCycleCompletionReason (self) -> typing.Optional[CycleShared.CompletionReasons]:
		"""
		The reason why the last cycle completed. This will be None if the sim has not had a cycle yet.
		"""

		return self._lastCycleCompletionReason

	@LastCycleCompletionReason.setter
	def LastCycleCompletionReason (self, value: typing.Optional[CycleShared.CompletionReasons]) -> None:
		if not isinstance(value, CycleShared.CompletionReasons) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "LastCycleCompletionReason", (CycleShared.CompletionReasons,))

		self._lastCycleCompletionReason = value

	@property
	def CurrentCycle (self) -> typing.Optional[CycleBase.CycleBase]:
		return self._currentCycle

	@CurrentCycle.setter
	def CurrentCycle (self, value: typing.Optional[CycleBase.CycleBase]) -> None:
		if not isinstance(value, CycleBase.CycleBase) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "CurrentCycle", (CycleBase.CycleBase, None))

		if hasattr(self, "_currentCycle"):
			previousValue = self._currentCycle

			if previousValue is value:
				return

			if previousValue is not None:
				self._UnsetCycleCallbacks(previousValue)
		else:
			previousValue = None  # type: typing.Optional[CycleBase.CycleBase]

		self._currentCycle = value

		if value is not None:
			self._SetCycleCallbacks(value)

		if self.TrackingSystem.Simulating:
			if value is None and previousValue is None:
				return

			self.TrackingSystem.Simulation.NeedToPlan = True

		cycleChangedEventArguments = CycleEvents.CycleAbortTestingArguments()  # type: CycleEvents.CycleAbortTestingArguments

		for cycleChangedCallback in self.CycleChangedEvent:
			try:
				cycleChangedCallback(self, cycleChangedEventArguments)
			except:
				Debug.Log("Failed to call cycle changed callback '" + Types.GetFullName(cycleChangedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = cycleChangedCallback)

	@property
	def CycleObjectsGenerated (self) -> int:
		"""
		The total number of cycle objects that have been generated by this cycle tracker.
		"""

		return self._cycleObjectsGenerated

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return FemalesShared.ShouldHaveFemaleTrackers(targetSimInfo)

	def DoCycleStartTesting (self) -> CycleEvents.CycleStartTestingArguments:
		"""
		Test for when the next cycle is to start and of what type it will be.
		:return: Testing event arguments that carry information on whether or not a cycle should start.
		:rtype: EventsCycles.CycleStartTestingArguments
		"""

		if self.CycleStartTestingSeed is None:
			self.CycleStartTestingSeed = self.TrackingSystem.CurrentSeed

		eventArguments = CycleEvents.CycleStartTestingArguments(self.CycleStartTestingSeed, self.TimeSinceLastCycle)  # type: CycleEvents.CycleStartTestingArguments
		self.CycleStartTestingEvent.Invoke(self, eventArguments)

		for cycleStartTestingCallback in self.CycleStartTestingEvent:
			try:
				cycleStartTestingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call cycle start testing callback '" + Types.GetFullName(cycleStartTestingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = cycleStartTestingCallback)

		return eventArguments

	def DoCycleAbortTesting (self) -> CycleEvents.CycleAbortTestingArguments:
		"""
		Test if the currently active cycle should abort.
		:return: Testing event arguments that carry information on whether or not the current cycle should abort.
		:rtype: EventsCycles.CycleAbortTestingArguments
		"""

		eventArguments = CycleEvents.CycleAbortTestingArguments()  # type: CycleEvents.CycleAbortTestingArguments

		for cycleAbortTestingCallback in self.CycleAbortTestingEvent:
			try:
				cycleAbortTestingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call cycle abort testing callback '" + Types.GetFullName(cycleAbortTestingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = cycleAbortTestingCallback)

		return eventArguments

	def DoCycleReleaseOvumTesting (self, ovumRelease: CycleOvumRelease.OvumRelease) -> CycleEvents.CycleReleaseOvumTestingArguments:
		"""
		Test if the a cycle should release an ovum.
		:param ovumRelease: The object that has indicated to the cycle that an ovum should release.
		:type ovumRelease: CycleOvumRelease.OvumRelease
		:return: Testing event arguments that carry information on whether or not a cycle should release an ovum.
		:rtype: EventsCycles.CycleReleaseOvumTestingArguments
		"""

		eventArguments = CycleEvents.CycleReleaseOvumTestingArguments(ovumRelease)  # type: CycleEvents.CycleReleaseOvumTestingArguments

		for cycleReleaseOvumTestingCallback in self.CycleReleaseOvumTestingEvent:
			try:
				cycleReleaseOvumTestingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call cycle release ovum testing callback '" + Types.GetFullName(cycleReleaseOvumTestingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = cycleReleaseOvumTestingCallback)

		return eventArguments

	def IsTooYoung (self) -> bool:
		"""
		Whether or not this system's sim is too young to have a cycle.
		"""

		return self.TrackingSystem.SimInfo.age <= sim_info_types.Age.CHILD

	def IsTooOld (self) -> bool:
		"""
		Whether or not this system's sim is too old to have a cycle.
		"""

		return self.TrackingSystem.SimInfo.age >= sim_info_types.Age.ELDER

	def GenerateCycle (self, cycleTypeIdentifier: str) -> CycleBase.CycleBase:
		"""
		Create a cycle object based off and made for this reproductive system.
		:param cycleTypeIdentifier: The identifier of the type of cycle to be generated, this must be registered in with cycles types module.
		:type cycleTypeIdentifier: str
		"""

		generationSeed = self.TrackingSystem.CurrentSeed  # type: int

		random.seed(self.CycleObjectsGenerated)
		generationSeed += random.randint(-1000000000, 1000000000)

		cycleType = CycleTypes.GetCycleType(cycleTypeIdentifier)

		cycle = cycleType()
		cycleGuide = cycle.GetCycleGuide(self.TrackingSystem)  # type: CycleGuides.CycleGuide
		eventArgumentsType = cycle.GetGenerationArgumentsType(self.TrackingSystem)  # type: typing.Type[CycleEvents.CycleGeneratingArguments]
		eventArguments = eventArgumentsType(generationSeed, cycle, cycleGuide)

		for cycleGeneratingCallback in self.CycleGeneratingEvent:
			try:
				cycleGeneratingCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call cycle generating callback '" + Types.GetFullName(cycleGeneratingCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = cycleGeneratingCallback)

		cycle.Generate(eventArguments)

		return cycle

	def GetDebugNotificationString (self) -> str:
		debugString = ""  # type: str

		if self.CurrentCycle is None:
			timeSinceLastCycle = self.TimeSinceLastCycle  # type: typing.Optional[float]

			if timeSinceLastCycle is not None:
				debugString = "Last Cycle: %s minutes ago" % str(timeSinceLastCycle)
		else:
			debugString = self.CurrentCycle.GetDebugNotificationString()

		return debugString

	def Verify (self) -> None:
		replanSimulation = False  # type: bool

		if not self.CompletedInitialCycle and not self.RunningInitialCycle:
			self._SetInitialCycle()
			replanSimulation = True
		elif self.CurrentCycle is not None:
			if self.CurrentCycle.Completed:
				self.CurrentCycle = None
				replanSimulation = True
			elif self.DoCycleAbortTesting().AbortCycle.Value:
				self.CurrentCycle.End(CycleShared.CompletionReasons.Unknown)

				if self.CurrentCycle is not None:
					self.CurrentCycle = None

				replanSimulation = True

		if replanSimulation and self.TrackingSystem.Simulating:
			self.TrackingSystem.Simulation.NeedToPlan = True

	def _SetInitialCycle (self) -> None:
		if self.CompletedInitialCycle:
			Debug.Log("Doing initial setup despite such work having already been completed.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		cycleStartTesting = self.DoCycleStartTesting()
		timeUntilCycleStart = cycleStartTesting.GetTimeUntilStart()  # type: typing.Optional[float]

		if cycleStartTesting.GetCanStart() and (timeUntilCycleStart is None or timeUntilCycleStart <= 0):  # We don't need to setup an initial cycle if this sim isn't suppose to start a cycle yet.
			cycleAgeSeed = self.TrackingSystem.StaticSeed + -224951188
			initialCycle = self.GenerateCycle(cycleStartTesting.GetCycleTypeIdentifier())  # type: CycleBase.CycleBase

			random.seed(cycleAgeSeed)
			cycleCompletionPercentage = random.random()  # type: float
			cycleCompletionPercentage = max(min(cycleCompletionPercentage, 0.995), 0)

			cycleAge = initialCycle.Lifetime * cycleCompletionPercentage  # type: typing.Union[float, int]
			initialCycle.Age = cycleAge

			ovumTracker = self.TrackingSystem.GetTracker(FemalesShared.OvumTrackerIdentifier)
			if ovumTracker is not None:
				for ovumRelease in initialCycle.OvumReleases:  # type: CycleOvumRelease.OvumRelease
					ovumReleaseTime = ovumRelease.ReleaseMinute  # type: float

					if ovumReleaseTime > cycleAge:
						continue

					ovumAge = max(cycleAge - ovumReleaseTime, 0)  # type: float
					releasedOvum = ovumTracker.GenerateOvum()  # type: Ovum.Ovum

					if ovumAge >= releasedOvum.Lifetime:
						continue

					releasedOvum.Age = ovumAge

					ovumTracker.ReleaseOvum(releasedOvum)

			self.CurrentCycle = initialCycle

	def _SetCycleCallbacks (self, cycle: CycleBase.CycleBase) -> None:
		self._UnsetCycleCallbacks(cycle)

		cycle.CompletedCallback = self._CurrentCycleCompletedCallback
		cycle.ReleasedOvumCallback = self._CurrentCycleReleasedOvumCallback

	def _UnsetCycleCallbacks (self, cycle: CycleBase.CycleBase) -> None:
		cycle.CompletedCallback = None
		cycle.ReleasedOvumCallback = None

	def _Setup (self) -> None:
		super()._Setup()

	# noinspection PyUnusedLocal
	def _CycleSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]
		simulatingMinutes = ReproductionShared.TicksToReproductiveMinutes(ticks, reproductiveTimeMultiplier)  # type: typing.Union[float, int]

		simulationMemoryKey = self.SimulationMemoryKey
		simulationMemoryExists = simulationMemoryKey in simulation.Memory  # type: bool
		simulationMemory = simulation.Memory.get(simulationMemoryKey, CycleTrackerSimulationMemory())  # type: CycleTrackerSimulationMemory

		if self.TimeSinceLastCycle is not None:
			self.TimeSinceLastCycle += simulatingMinutes

		if self.CurrentCycle is not None:
			cycleTicksRemaining = ReproductionShared.ReproductiveMinutesToTicks(self.CurrentCycle.TimeRemaining, reproductiveTimeMultiplier)  # type: typing.Union[float, int]

			if cycleTicksRemaining < ticks:
				Debug.Log("Simulation stepped over the end of a cycle by %s ticks, this may cause lost time for the tracking sim.\n%s" % (str(ticks - cycleTicksRemaining), self.DebugInformation),
						  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self.TrackingSystem)

			self.CurrentCycle.Simulate(simulation, ticks, reproductiveTimeMultiplier)
		else:
			if simulationMemory.CycleStartTesting is None:
				Debug.Log("Expected the 'CycleStartTesting' to be in the simulation memory, but all we found was None.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self.TrackingSystem)

				simulationMemory.CycleStartTesting = self.DoCycleStartTesting()
			elif not simulationMemoryExists:
				simulationMemory.CycleStartTesting = self.DoCycleStartTesting()

			if simulationMemory.CycleStartTesting.GetCanStart():
				timeUntilCycleStart = simulationMemory.CycleStartTesting.GetTimeUntilStart()  # type: typing.Optional[float]
				cycleStartPlanned = timeUntilCycleStart is not None  # type: bool

				if cycleStartPlanned:
					ticksUntilCycleStart = ReproductionShared.ReproductiveMinutesToTicks(timeUntilCycleStart, reproductiveTimeMultiplier)  # type: int
				else:
					ticksUntilCycleStart = 1  # type: int

				if ticksUntilCycleStart <= ticks:
					if cycleStartPlanned and ticksUntilCycleStart < ticks:
						Debug.Log("Simulation stepped over the start of a cycle by %s ticks, this may cause lost time for the tracking sim.\n%s" % (str(ticks - ticksUntilCycleStart), self.DebugInformation),
								  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self.TrackingSystem)

					cycleTypeIdentifier = simulationMemory.CycleStartTesting.GetCycleTypeIdentifier()  # type: str

					cycle = self.GenerateCycle(cycleTypeIdentifier)

					self.CycleStartTestingSeed = None
					simulationMemory.CycleStartTesting = None
					self.CurrentCycle = cycle
			else:
				simulationMemory.CycleStartTesting.IncreaseTimeSinceTest(simulatingMinutes)

		if not simulationMemoryExists:
			simulation.Memory[simulationMemoryKey] = simulationMemory

	def _PlanSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PlanSimulation(simulation)

		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		simulationMemory = CycleTrackerSimulationMemory()  # type: CycleTrackerSimulationMemory

		if self.CurrentCycle is None:
			cycleStartTesting = self.DoCycleStartTesting()  # type: CycleEvents.CycleStartTestingArguments

			if cycleStartTesting.GetCanStart():
				timeUntilCycleStart = cycleStartTesting.GetTimeUntilStart()  # type: typing.Optional[float]
				cycleStartPlanned = timeUntilCycleStart is not None  # type: bool

				if cycleStartPlanned:
					ticksUntilCycleStart = ReproductionShared.ReproductiveMinutesToTicks(timeUntilCycleStart, reproductiveTimeMultiplier)  # type: int
				else:
					ticksUntilCycleStart = 1  # type: int

				if simulation.RemainingTicks >= ticksUntilCycleStart:
					simulation.Schedule.AddPoint(ticksUntilCycleStart)

			simulationMemory.CycleStartTesting = cycleStartTesting
		else:
			self.CurrentCycle.PlanSimulation(simulation, reproductiveTimeMultiplier)

		simulation.Memory[self.SimulationMemoryKey] = simulationMemory

	def _PrepareForSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PrepareForSimulation(simulation)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(0, self._CycleSimulationPhase)
		)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return FemalesShared.GetCycleTrackerReproductiveTimeMultiplier()

	def _CurrentCycleCompletedCallback (self, completionReason: CycleShared.CompletionReasons) -> None:
		eventArguments = CycleEvents.CycleCompletedArguments(completionReason)  # type: CycleEvents.CycleCompletedArguments

		for cycleCompletedCallback in self.CycleCompletedEvent:
			try:
				cycleCompletedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call cycle completed callback '" + Types.GetFullName(cycleCompletedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = cycleCompletedCallback)

		self.CurrentCycle = None

		self.CompletedInitialCycle = True
		self.CompletedFirstCycle = True

		self.TimeSinceLastCycle = None
		self.LastCycleCompletionReason = completionReason

		if completionReason == CycleShared.CompletionReasons.Finished:
			self.TimeSinceLastCycle = 0  # TODO this should be set only if the sim experiences any symptoms instead.

	def _CurrentCycleReleasedOvumCallback (self, ovumRelease: CycleOvumRelease.OvumRelease) -> None:
		ovumTracker = self.TrackingSystem.GetTracker(FemalesShared.OvumTrackerIdentifier)

		if ovumTracker is not None:
			releaseOvumTesting = self.DoCycleReleaseOvumTesting(ovumRelease)  # type: CycleEvents.CycleReleaseOvumTestingArguments

			if not releaseOvumTesting.Release:
				return

			ovumTracker.GenerateAndReleaseOvum()  # type: Ovum.Ovum

			ovumRelease.Released = True

	def _CycleStartTestingCallback (self, owner: CycleTracker, eventArguments: CycleEvents.CycleStartTestingArguments) -> None:
		if owner.IsTooYoung() or owner.IsTooOld():
			eventArguments.CanStart.Value = False

	def _CycleAbortTestingCallback (self, owner: CycleTracker, eventArguments: CycleEvents.CycleAbortTestingArguments) -> None:
		if owner.IsTooYoung() or owner.IsTooOld():
			eventArguments.AbortCycle.Value = True


