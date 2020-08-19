from __future__ import annotations

import inspect
import random
import typing

import date_and_time
import game_services
import services
import time_service
from NeonOcean.S4.Cycle import Events as CycleEvents, GuideGroups as CycleGuideGroups, ReproductionTrackers, Settings, This, Saving
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Saving import SectionBranched
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Sims as ToolsSims, Types, Version
from sims import sim_info

class Schedule:
	def __init__ (self):
		self._points = list()  # type: typing.List[int]

		self.BlockAdditions = False

	@property
	def BlockAdditions (self) -> bool:
		"""
		Attempts to add more points will result in exceptions while this is true.
		"""

		return self._blockAdditions

	@BlockAdditions.setter
	def BlockAdditions (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "BlockAdditions", (bool,))

		self._blockAdditions = value

	@property
	def Points (self) -> typing.List[int]:
		"""
		Get all points in this schedule.
		"""

		return list(self._points)

	@property
	def CurrentPoint (self) -> typing.Optional[int]:
		"""
		Get the current point, the point with the index of 0. This will return None if there is no point.
		"""

		if len(self._points) >= 1:
			return self._points[0]

	@property
	def NextPoint (self) -> typing.Optional[int]:
		"""
		Get the next point that the simulation should move to after the current point, the point with the index of 1. This will return None if there is no point.
		"""

		if len(self._points) >= 2:
			return self._points[1]

	@property
	def PointCount (self) -> int:
		"""
		The number of points currently existing to this schedule.
		"""

		return len(self._points)

	def AddPoint (self, addingPoint: int) -> None:
		"""
		Add a point to this schedule. Additions may be blocked at certain times such as while simulating.
		:param addingPoint: The point to be added. Each point is a tick that the simulation will stop at to allow for special work to be done.  If the
		point has already been added nothing will happen. The adding point cannot be less than or equal to 0, otherwise we will schedule a point at the
		earliest possible tick.
		:type addingPoint: int
		"""

		if not isinstance(addingPoint, int):
			raise Exceptions.IncorrectTypeException(addingPoint, "addingPoint", (int,))

		if addingPoint <= 0:
			lastFrame = inspect.currentframe().f_back
			lockIdentifier = lastFrame.f_code.co_filename + ":" + str(lastFrame.f_lineno)  # type: str

			Debug.Log("Tried to add the less than or equal to zero point '%s' to the schedule." % addingPoint,
					  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, logStack = True, lockIdentifier = lockIdentifier)

			addingPoint = 1

		if self.BlockAdditions:
			raise Exception("Cannot add points at this time.")

		if addingPoint in self._points:
			return

		for existingPointIndex in range(len(self._points)):  # type: int
			existingPoint = self._points[existingPointIndex]  # type: int

			if existingPoint > addingPoint:
				self._points.insert(existingPointIndex, addingPoint)
				return

		self._points.append(addingPoint)

	def MoveToNextPoint (self) -> None:
		"""
		Move on to the next point, dumping the current point from the list.
		"""

		if len(self._points) != 0:
			self._points.pop(0)

	def ClearPoints (self) -> None:
		"""
		Clear all points in this schedule.
		"""

		self._points = list()

class SimulationPhase:
	def __init__ (self, priority: typing.Union[float, int], phase: typing.Callable, required: bool = False):
		"""
		A phase of the reproductive simulation.
		:param priority: The priority of the phase. Higher priority phases will run first, phases with the same priority run in the order
		of registration.
		:type priority: float | int
		:param phase: What to be called when it is this phase's turn to be run. This should take two arguments, the simulation object
		and the number of ticks being simulated this step.
		:type phase: typing.Callable[[Simulation, int], None]
		:param required: Whether or not this phase is required to finish without exception. Failures in required phases will cause the
		entire reproductive system simulation to fall through.
		:type required: bool
		"""

		if not isinstance(priority, (float, int)):
			raise Exceptions.IncorrectTypeException(priority, "priority", (float, int))

		if not isinstance(phase, typing.Callable):
			raise Exceptions.IncorrectTypeException(phase, "phase", ("Callable",))

		self._priority = priority
		self._phase = phase
		self._required = required

	@property
	def Priority (self) -> typing.Union[float, int]:
		"""
		The priority of the phase. Higher priority phases will run first, phases with the same priority run in the order of registration.
		"""

		return self._priority

	@property
	def Phase (self) -> typing.Callable:
		"""
		What to be called when it is this phase's turn to be run. This should take two arguments, the simulation object and the number
		of ticks being simulated this step.
		"""

		return self._phase

	@property
	def Required (self) -> bool:
		"""
		Whether or not this phase is required to finish without exception. Failures in required phases will cause the entire reproductive system
		simulation to fall through.
		"""

		return self._required

class Simulation:
	def __init__ (self, simulatingSystem: object, ticks: int):
		"""
		An object for tracking the simulation of a reproductive object.
		:param simulatingSystem: The reproductive system this simulation object was created for.
		:type simulatingSystem: ReproductiveSystem
		:param ticks: The number of ticks being simulated.
		:type ticks: int
		"""

		if not isinstance(simulatingSystem, ReproductiveSystem):
			raise Exceptions.IncorrectTypeException(simulatingSystem, "simulatingSystem", (ReproductiveSystem,))

		if not isinstance(ticks, int):
			raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

		self.Ticks = ticks
		self.CompletedTicks = 0
		self.NeedToPlan = True

		self._simulatingSystem = simulatingSystem  # type: ReproductiveSystem

		self._phases = list()  # type: typing.List[SimulationPhase]
		self._schedule = Schedule()  # type: Schedule
		self._memory = dict()  # type: typing.Dict[str, typing.Any]

		self._lastTickStep = False  # type: bool

	@property
	def SimulatingSystem (self):
		"""
		The reproductive system this simulation object was created for.
		:rtype: ReproductiveSystem
		"""

		return self._simulatingSystem

	@property
	def Ticks (self) -> int:
		"""
		The number of ticks being simulated.
		"""

		return self._ticks

	@Ticks.setter
	def Ticks (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Ticks", (int,))

		self._ticks = value

	@property
	def NonUpdateTicks (self) -> int:
		"""
		The number of ticks that are non-update ticks, meaning that they are ticks that haven't actually happened in-game.
		"""

		return self.Ticks - self.SimulatingSystem.TicksBehind

	@property
	def CompletedTicks (self) -> int:
		"""
		The number of ticks that have already been simulated.
		"""

		return self._simulatedTicks

	@CompletedTicks.setter
	def CompletedTicks (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "CompletedTicks", (int,))

		self._simulatedTicks = value

	@property
	def CompletedMinutes (self) -> float:
		"""
		The number of game minutes that have already been simulated.
		"""

		return date_and_time.ticks_to_time_unit(self.CompletedTicks, date_and_time.TimeUnit.MINUTES, True)

	@property
	def RemainingTicks (self) -> int:
		"""
		The number of ticks that have not yet been simulated.
		"""

		return max(self.Ticks - self.CompletedTicks, 0)

	@property
	def RemainingMinutes (self) -> float:
		"""
		The number of game minutes that have not yet been simulated.
		"""

		return date_and_time.ticks_to_time_unit(self.RemainingTicks, date_and_time.TimeUnit.MINUTES, True)

	@property
	def Schedule (self) -> Schedule:
		"""
		The schedule of this simulation.
		"""

		return self._schedule

	@property
	def Memory (self) -> dict:
		"""
		The simulation memory should be used to store information between tick steps. This is typically used to store things such as tests that we
		don't need to redo each tick step.
		"""

		return self._memory

	@Memory.setter
	def Memory (self, value: dict) -> None:
		if not isinstance(value, dict):
			raise Exceptions.IncorrectTypeException(value, "Memory", (dict,))

		self._memory = value

	@property
	def NeedToPlan (self) -> bool:
		"""
		Signals that we need to plan out the simulation. Usually we will replan the simulation just before the next tick step starts.
		"""

		return self._needToPlan

	@NeedToPlan.setter
	def NeedToPlan (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "NeedToPlan", (bool,))

		self._needToPlan = value

	@property
	def LastTickStep (self) -> bool:
		"""
		Whether or not the last tick step for this simulation is occurring.
		"""

		return self._lastTickStep

	def GetPhases (self) -> typing.List[SimulationPhase]:
		"""
		Get the phases this simulation will run through. You cannot remove or add a phase my modifying the list returned, please use
		the 'RegisterPhase' method.
		"""

		return list(self._phases)

	def RegisterPhase (self, phase: SimulationPhase) -> None:
		"""
		Register a phase to run during this simulation.
		"""

		if not isinstance(phase, SimulationPhase):
			raise Exceptions.IncorrectTypeException(phase, "phase", (SimulationPhase,))

		registeredPhases = self._phases  # type: typing.List[SimulationPhase]
		phasePriority = phase.Priority  # type: typing.Union[float, int]

		lowPhaseIndex = 0  # type: int
		highPhaseIndex = len(self._phases)  # type: int

		while lowPhaseIndex < highPhaseIndex:
			middlePhaseIndex = (lowPhaseIndex + highPhaseIndex) // 2  # type: int
			if -phasePriority < -registeredPhases[middlePhaseIndex].Priority:
				highPhaseIndex = middlePhaseIndex
			else:
				lowPhaseIndex = middlePhaseIndex + 1

		registeredPhases.insert(lowPhaseIndex, phase)

	def Simulate (self) -> None:
		"""
		Run the simulation.
		"""

		while self.RemainingTicks != 0:
			self.SimulatingSystem.Verify()

			if self.NeedToPlan:
				self._PlanSimulation()
				self.NeedToPlan = False

			while True:
				if self.Schedule.CurrentPoint is not None:
					tickStep = self.Schedule.CurrentPoint - self.CompletedTicks  # type: int

					if tickStep > self.RemainingTicks:
						Debug.Log("Next scheduled tick is beyond the final simulating tick.\n" + self.SimulatingSystem.DebugInformation,
								  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self.SimulatingSystem)

						tickStep = self.RemainingTicks
				else:
					tickStep = self.RemainingTicks  # type: int

				if tickStep > 0:
					break
				else:
					lastPointCount = self.Schedule.PointCount  # type: int
					self.Schedule.MoveToNextPoint()
					currentPointCount = self.Schedule.PointCount  # type: int

					if lastPointCount <= currentPointCount:  # A check to prevent infinity loops.
						Debug.Log("Moving to the next scheduled point did not reduce the number of points.\nLast point count: %s, Current point count: %s\n%s" % (lastPointCount, currentPointCount, self.SimulatingSystem.DebugInformation),
								  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = self.SimulatingSystem)

						tickStep = self.RemainingTicks
						break

					continue

			if tickStep > 0:
				if tickStep == self.RemainingTicks:
					self._lastTickStep = True

				for phaseInformation in self._phases:  # type: SimulationPhase
					if not phaseInformation.Required:
						try:
							phaseInformation.Phase(self, tickStep)
						except:
							Debug.Log("Failed to complete reproductive cycle phase at '%s'.\n%s" % (Types.GetFullName(phaseInformation.Phase), self.SimulatingSystem.DebugInformation),
									  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = phaseInformation.Phase)
					else:
						phaseInformation.Phase(self, tickStep)

				if self._lastTickStep:
					self._lastTickStep = False

					self.SimulatingSystem.TicksSimulated += tickStep
					self.CompletedTicks = self.Ticks
					break
				else:
					self.SimulatingSystem.TicksSimulated += tickStep
					self.CompletedTicks += tickStep

		self.SimulatingSystem.Verify()

	def _PlanSimulation (self) -> None:
		self.Schedule.ClearPoints()
		self.SimulatingSystem.PlanSimulation(self)

class TrackerBase(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, trackingSystem):
		super().__init__()

		if not isinstance(trackingSystem, ReproductiveSystem):
			raise Exceptions.IncorrectTypeException(trackingSystem, "trackingSystem", (ReproductiveSystem,))

		self._trackingSystem = trackingSystem  # type: ReproductiveSystem
		self._currentReproductiveTimeMultiplier = 1  # type: float

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		raise NotImplementedError()

	@property
	def TrackingSystem (self):
		return self._trackingSystem

	@property
	def SavableOperationInformation (self) -> str:
		return self.DebugInformation

	@property
	def DebugInformation (self) -> str:
		return "%s | Section Key: %s | Sim ID: %s | Sim: %s" % \
			   (self.__class__.__name__,
				self.TrackingSystem.SectionKey,
				self.TrackingSystem.SimInfo.id,
				ToolsSims.GetFullName(self.TrackingSystem.SimInfo))

	@property
	def ReproductiveTimeMultiplier (self) -> typing.Union[float, int]:
		"""
		Get the value that is divided with the game time to get the reproductive time and multiplied with the reproductive time to get the game time.
		"""

		return self._currentReproductiveTimeMultiplier

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return False

	def Verify (self) -> None:
		"""
		Verify that this tracking object is in a valid state.
		"""

		pass

	def GetDebugNotificationString (self) -> str:
		return ""

	def _Setup (self) -> None:
		"""
		Called when: The reproductive system has finished initializing and has registered all trackers, The system has loaded new save data, or the
		system has reset its save data.
		"""

		pass

	def _OnAdding (self) -> None:
		"""
		Called when the tracker is about to be officially added to the reproductive system.
		"""

		pass

	def _OnAdded (self) -> None:
		"""
		Called when the tracker has been officially added to the reproductive system.
		"""

		pass

	def _OnRemoving (self) -> None:
		"""
		Called when the tracker is about to be removed from the reproductive system.
		"""

		pass

	def _OnRemoved (self) -> None:
		"""
		Called when the tracker has been removed from the reproductive system.
		"""

		pass

	def _PlanSimulation (self, simulation: Simulation) -> None:
		pass

	def _PrepareForSimulation (self, simulation: Simulation) -> None:
		self._UpdateReproductiveTimeMultiplier()

	def _CleanUpSimulation (self, simulation: Simulation) -> None:
		pass

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return self.TrackingSystem.ReproductiveTimeMultiplier

	def _UpdateReproductiveTimeMultiplier (self) -> None:
		nextReproductiveTimeMultiplier = self._GetNextReproductiveTimeMultiplier()  # type: float

		if nextReproductiveTimeMultiplier != self._currentReproductiveTimeMultiplier:
			self._currentReproductiveTimeMultiplier = nextReproductiveTimeMultiplier
			self._OnUpdatedReproductiveTimeMultiplier()

	def _OnUpdatedReproductiveTimeMultiplier (self) -> None:
		pass

class ReproductiveSystemMetaClass(type):
	def __call__ (cls, *args, **kwargs):
		reproductiveSystem = type.__call__(cls, *args, **kwargs)  # type: ReproductiveSystem

		if isinstance(reproductiveSystem, ReproductiveSystem):
			# noinspection PyProtectedMember
			reproductiveSystem._Setup()

		return reproductiveSystem

class ReproductiveSystem(Savable.SavableExtension, metaclass = ReproductiveSystemMetaClass):  # #TODO Ghost sims probably shouldn't have a reproductive system / test if they do.
	HostNamespace = This.Mod.Namespace  # type: str

	_trackersSavingKey = "Trackers"

	def __init__ (self, simInfo: sim_info.SimInfo, sectionKey: str = "ReproductiveSystem", *args, **kwargs):
		"""
		:param simInfo: The info of the sim this reproductive system is tied to.
		:type simInfo: sim_info.SimInfo
		:param sectionKey: The section key that this object's data will be written to when saving.
		:type sectionKey: str
		"""

		super().__init__(*args, **kwargs)

		if not isinstance(simInfo, sim_info.SimInfo):
			raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

		if not isinstance(sectionKey, str):
			raise Exceptions.IncorrectTypeException(sectionKey, "sectionKey", (str,))

		if game_services.service_manager is None:
			raise Exception("Cannot create a reproductive system while the time service is inactive.")

		self.TrackerAddedEvent = Events.EventHandler()
		self.TrackerRemovedEvent = Events.EventHandler()
		self.PlanUpdateEvent = Events.EventHandler()

		self.LastSimulatedTick = services.time_service().sim_now.absolute_ticks()
		self.TicksSimulated = 0
		self.Simulation = None

		self._isSetup = False  # type: bool

		self._assignedGuides = None  # type: typing.Optional[CycleGuideGroups.GuideGroup]

		self._simInfo = simInfo  # type: sim_info.SimInfo
		self._sectionKey = sectionKey  # type: str

		random.seed(self.SimInfo.id)
		self._savedStaticSeed = random.randint(-1000000000, 1000000000)  # type: int
		self._savedCurrentSeed = None  # type: typing.Optional[int]
		self._savedCurrentSeedTicks = None  # type: typing.Optional[int]
		self._uniqueSeedsGenerated = 0  # type: int

		self._currentReproductiveTimeMultiplier = 1  # type: float

		self._trackers = list()  # type: typing.List[TrackerBase]

		self._SetGuideGroup()

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("TicksSimulated", "TicksSimulated", self.TicksSimulated, requiredSuccess = False))

	@property
	def SavableOperationInformation (self) -> str:
		return self.DebugInformation

	@property
	def DebugInformation (self) -> str:
		return "%s | Section Key: %s | Sim ID: %s | Sim: %s" % \
			   (self.__class__.__name__,
				self.SectionKey,
				self.SimInfo.id,
				ToolsSims.GetFullName(self.SimInfo))

	@property
	def TrackerAddedEvent (self) -> Events.EventHandler:
		"""
		An event to be triggered when a tracker is added to this reproductive system.
		The event arguments parameter should be a 'TrackerAddedArguments' object.
		"""

		return self._trackerAddedEvent

	@TrackerAddedEvent.setter
	def TrackerAddedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "TrackerAddedEvent", (Events.EventHandler,))

		self._trackerAddedEvent = value

	@property
	def TrackerRemovedEvent (self) -> Events.EventHandler:
		"""
		An event to be triggered when a tracker is removed from this reproductive system.
		The event arguments parameter should be a 'TrackerRemovedArguments' object.
		"""

		return self._trackerRemovedEvent

	@TrackerRemovedEvent.setter
	def TrackerRemovedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "TrackerRemovedEvent", (Events.EventHandler,))

		self._trackerRemovedEvent = value

	@property
	def PlanUpdateEvent (self) -> Events.EventHandler:
		"""
		An event to be triggered when we need to plan when the next update call should happen.
		The event arguments parameter should be a 'PlanUpdateArguments' object.
		"""

		return self._planUpdateEvent

	@PlanUpdateEvent.setter
	def PlanUpdateEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "PlanUpdateEvent", (Events.EventHandler,))

		self._planUpdateEvent = value

	@property
	def Trackers (self) -> typing.List[TrackerBase]:
		"""
		All trackers associated with this reproductive system.
		"""

		return list(self._trackers)

	@property
	def SimInfo (self) -> sim_info.SimInfo:
		"""
		The info of the sim this reproductive system is tied to.
		"""

		return self._simInfo

	@property
	def SectionKey (self) -> str:
		"""
		The section key that this object's data will be written to when saving.
		"""

		return self._sectionKey

	@property
	def ShouldExist (self) -> bool:
		"""
		Whether or not this reproductive system object should exist.
		"""

		return True

	@property
	def TicksSimulated (self) -> int:
		"""
		The total number of ticks simulated in this reproductive system.
		"""

		return self._ticksSimulated

	@TicksSimulated.setter
	def TicksSimulated (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "TicksSimulated", (int,))

		self._ticksSimulated = value

	@property
	def LastSimulatedTick (self) -> int:
		"""
		The tick this reproductive system was last simulated to. This value isn't saved, when the reproductive system is first creating it is assumed
		the system was simulated up to now. All reproductive systems should be updated before being saved to prevent missed time.
		"""

		return self._lastSimulatedTick

	@LastSimulatedTick.setter
	def LastSimulatedTick (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "LastSimulatedTick", (int,))

		self._lastSimulatedTick = value

	@property
	def Outdated (self) -> bool:
		"""
		Whether or not this reproductive system has been simulated all the way to the latest tick. If the game's time service is not available this will
		return False.
		"""

		if game_services.service_manager is None:
			return False

		timeService = services.time_service()  # type: time_service.TimeService

		return self.LastSimulatedTick < timeService.sim_now.absolute_ticks()

	@property
	def TicksBehind (self) -> int:
		"""
		The number of game ticks the system is behind the current game tick.
		"""

		timeService = services.time_service()  # type: time_service.TimeService
		return max(timeService.sim_now.absolute_ticks() - self.LastSimulatedTick, 0)

	@property
	def Simulation (self) -> typing.Optional[Simulation]:
		"""
		The simulation object handling this reproductive system's simulation. This will be None if the reproductive system is not simulating.
		"""

		return self._simulation

	@Simulation.setter
	def Simulation (self, value) -> None:
		if not isinstance(value, Simulation) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "Simulation", (Simulation, None))

		self._simulation = value

	@property
	def Simulating (self) -> bool:
		"""
		Whether or not this reproductive system is currently in the process of simulating time.
		"""

		return self.Simulation is not None

	@property
	def ShouldUpdate (self) -> bool:
		"""
		Whether or not this reproductive system should be updated. This value will be True if this object is outdated and is not already simulating.
		"""

		return self.Outdated and not self.Simulating

	@property
	def StaticSeed (self) -> int:
		"""
		Get a seed that will be the same for as long as this sim exists. The seed should be mixed with another number specific to each randomization
		operation, otherwise everything would generate the same numbers.
		"""

		return self._savedStaticSeed

	@property
	def CurrentSeed (self) -> int:
		"""
		Get the current seed for this sim. This should be used for the randomization of the reproductive system. The seed should be mixed with another
		number specific to each randomization operation, otherwise everything would generate the same numbers.
		"""

		def SetCurrentSeed () -> None:
			staticSeed = self.StaticSeed  # type: int

			random.seed(self.TicksSimulated)
			ticksSeed = random.randint(-1000000000, 1000000000)  # type: int

			self._savedCurrentSeed = staticSeed + ticksSeed
			self._savedCurrentSeedTicks = self.TicksSimulated

		if self._savedCurrentSeed is None:
			SetCurrentSeed()

		if self._savedCurrentSeedTicks != self.TicksSimulated:
			SetCurrentSeed()

		return self._savedCurrentSeed

	@property
	def GuideGroup (self) -> CycleGuideGroups.GuideGroup:
		"""
		Get the guide group for this reproductive system.
		"""

		if self._assignedGuides is None:
			return self._GetDefaultGuideGroup()
		else:
			return self._assignedGuides

	@property
	def ReproductiveTimeMultiplier (self) -> typing.Union[float, int]:
		"""
		Get the value that is divided with the game time to get the reproductive time and multiplied with the reproductive time to get the game time.
		"""

		return self._currentReproductiveTimeMultiplier

	def CreateUniqueSeed (self) -> int:
		"""
		Get a unique seed for this sim. This value will be generated from the current seed and the number of unique seeds generated.
		"""

		currentSeed = self.CurrentSeed  # type: int

		random.seed(self._uniqueSeedsGenerated)
		useCountSeed = random.randint(-1000000000, 1000000000)  # type: int

		uniqueSeed = currentSeed + useCountSeed  # type: int

		self._uniqueSeedsGenerated += 1

		return uniqueSeed

	def GetTracker (self, identifier: str) -> typing.Optional[TrackerBase]:
		"""
		Get the tracker with this identifier. If no such tracker is registered this will return instead None.
		"""

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		for tracker in self._trackers:  # type: TrackerBase
			if tracker.TypeIdentifier == identifier:
				return tracker

		return None

	def HasTracker (self, identifier: str) -> bool:
		"""
		Get whether or not a tracker with this identifier has been registered to this system.
		"""

		return self.GetTracker(identifier) is not None

	def Load (self, simsSection: SectionBranched.SectionBranched) -> bool:
		"""
		Load the reproductive system's data from this saving section.
		"""

		if not isinstance(simsSection, SectionBranched.SectionBranched):
			raise Exceptions.IncorrectTypeException(simsSection, "simsSection", (SectionBranched.SectionBranched,))

		operationInformation = self.SavableOperationInformation  # type: str
		operationSuccessful = True  # type: bool

		try:
			simSavingKey = Saving.GetSimSimsSectionBranchKey(self.SimInfo)  # type: str

			reproductiveSystemData = simsSection.GetValue(simSavingKey, self.SectionKey, default = None)  # type: typing.Optional[dict]

			if reproductiveSystemData is None:
				Debug.Log("'%s' has had a reproductive system object created for the first time, or at least, they had no saved data in the loaded save file.\n%s" % (ToolsSims.GetFullName(self.SimInfo), operationInformation), self.HostNamespace, Debug.LogLevels.Info, group = self.HostNamespace, owner = __name__)
				reproductiveSystemData = dict()

			if not isinstance(reproductiveSystemData, dict):
				Debug.Log("Incorrect type in reproductive system data with the section key.\n" + operationInformation + "\n" + Exceptions.GetIncorrectTypeExceptionText(reproductiveSystemData, "ReproductiveSystemData", (dict,)), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				reproductiveSystemData = dict()
				operationSuccessful = False

			if simsSection.SavingObject.DataHostVersion is not None:
				lastVersion = Version.Version(simsSection.SavingObject.DataHostVersion)  # type: typing.Optional[Version.Version]
			else:
				lastVersion = None  # type: typing.Optional[Version.Version]

			loadSuccessful = self.LoadFromDictionary(reproductiveSystemData, lastVersion = lastVersion)
		except:
			Debug.Log("Load operation in a reproductive system aborted.\n" + operationInformation, self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
			self.Reset()
			return False

		if not loadSuccessful:
			return False

		return operationSuccessful

	def Save (self, simsSection: SectionBranched.SectionBranched) -> bool:
		"""
		Save the reproductive system's data to this saving section.
		"""

		if not isinstance(simsSection, SectionBranched.SectionBranched):
			raise Exceptions.IncorrectTypeException(simsSection, "simsSection", (SectionBranched.SectionBranched,))

		if self.ShouldUpdate:
			self.Update()

		operationInformation = self.SavableOperationInformation  # type: str
		operationSuccessful = True  # type: bool

		try:
			simSavingKey = Saving.GetSimSimsSectionBranchKey(self.SimInfo)  # type: str

			saveSuccessful, reproductiveSystemData = self.SaveToDictionary()  # type: bool, dict
			simsSection.Set(simSavingKey, self.SectionKey, reproductiveSystemData)
		except:
			Debug.Log("Save operation in a reproductive system aborted.\n" + operationInformation, self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
			return False

		if not saveSuccessful:
			return False

		return operationSuccessful

	def Update (self) -> None:
		"""
		Update this reproductive system to the most recent tick. This needs to be called before this object is saved or time will be missed.
		Reproductive objects should be updated before changes are made or values are gotten from them.
		"""

		if game_services.service_manager is None:
			return

		if not self.Outdated:
			return

		if self.Simulating:
			return

		ticksBehind = self.TicksBehind

		if ticksBehind <= 0:
			return

		self.Simulate(ticksBehind)

	def Simulate (self, ticks: int) -> None:
		"""
		Simulate this many ticks in this reproductive system. This method could allow you to simulate time that hasn't actually passed.
		:param ticks: The number of ticks to simulate.
		:type ticks: int
		"""

		if not isinstance(ticks, int):
			raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

		if self.Simulating:
			return

		self._SimulateInternal(ticks)

		timeService = services.time_service()  # type: time_service.TimeService
		currentTick = timeService.sim_now.absolute_ticks()  # type: int

		self.LastSimulatedTick = min(self.LastSimulatedTick + ticks, currentTick)

	def PlanSimulation (self, simulation: Simulation) -> None:
		"""
		Plan out a simulation. Any tick that needs to be stopped at within the simulation's remaining ticks will to be added to the schedule. This method may be called
		more than once in a single simulation in order to replan any time remaining.
		:param simulation: The simulation object that needs to be worked on.
		:type simulation: Simulation
		"""

		if not isinstance(simulation, Simulation):
			raise Exceptions.IncorrectTypeException(simulation, "simulation", (Simulation,))

		self._PlanSimulationInternal(simulation)

	def Verify (self) -> None:
		"""
		Verify that this reproductive system is in a valid state.
		"""

		self._VerifyInternal()

	def PlanUpdate (self) -> CycleEvents.PlanUpdateArguments:
		"""
		Determine when the next update should occur.
		"""

		eventArguments = CycleEvents.PlanUpdateArguments()  # type: CycleEvents.PlanUpdateArguments

		for planUpdateCallback in self.PlanUpdateEvent:
			try:
				planUpdateCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call plan update callback '" + Types.GetFullName(planUpdateCallback) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = planUpdateCallback)

		return eventArguments

	def GetDebugNotificationString (self) -> str:
		debugStringTemplate = "{Type}\n" \
							  "Owner: {Owner}"

		debugStringFormatting = {
			"Type": self.__class__.__name__,
			"Owner": ToolsSims.GetFullName(self.SimInfo),
		}

		debugString = debugStringTemplate.format_map(debugStringFormatting)

		for tracker in self._trackers:  # type: TrackerBase
			trackerDebugString = tracker.GetDebugNotificationString()  # type: str

			if trackerDebugString == "":
				continue

			if debugString != "":
				debugString += "\n\n===== " + tracker.TypeIdentifier + " ====="

			debugString += "\n\n" + trackerDebugString

		return debugString

	def _Setup (self) -> None:
		self._SetupInternal()

	def _AddTracker (self, tracker: TrackerBase) -> None:
		if self.HasTracker(tracker.TypeIdentifier):
			raise ValueError("Attempted to add a tracker with the identifier '" + tracker.TypeIdentifier + "' while another tracker with the same identifier exists.")

		# noinspection PyProtectedMember
		tracker._OnAdding()

		self._trackers.append(tracker)

		# noinspection PyProtectedMember
		tracker._OnAdded()

		self._InvokeTrackerAddedEvent(tracker)

	def _RemoveTracker (self, tracker: TrackerBase) -> None:
		if not self.HasTracker(tracker.TypeIdentifier):
			raise ValueError("Attempted to remove a tracker that was never added.")

		# noinspection PyProtectedMember
		tracker._OnRemoving()

		try:
			self._trackers.remove(tracker)
		except ValueError:
			pass

		# noinspection PyProtectedMember
		tracker._OnRemoved()

		self._InvokeTrackerRemovedEvent(tracker)

	def _AddValidTrackers (self) -> None:
		activeTypeIdentifiers = set(tracker.TypeIdentifier for tracker in self._trackers)  # type: typing.Set[str]
		allTypeIdentifiers = ReproductionTrackers.GetAllTrackerTypeIdentifiers()  # type: typing.Set[str]

		for typeIdentifier in allTypeIdentifiers:  # type: str
			if not typeIdentifier in activeTypeIdentifiers:
				trackerType = ReproductionTrackers.GetTrackerType(typeIdentifier)

				if not trackerType.ShouldHave(self.SimInfo, self):
					continue

				try:
					tracker = trackerType(self)  # type: TrackerBase
				except:
					Debug.Log("Failed to create instance of the effect type '" + Types.GetFullName(trackerType) + "'.\n" + self.DebugInformation,
							  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + " | Creating_Effect", lockReference = trackerType)

					continue

				self._AddTracker(tracker)

	def _RemoveInvalidTrackers (self) -> None:
		for tracker in self.Trackers:  # type: TrackerBase
			if tracker.ShouldHave(self.SimInfo, self):
				continue

			self._RemoveTracker(tracker)

	def _RemoveAllTrackers (self) -> None:
		for tracker in self.Trackers:  # type: TrackerBase
			self._RemoveTracker(tracker)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return GetGeneralReproductiveTimeMultiplier()

	def _UpdateReproductiveTimeMultiplier (self) -> None:
		nextReproductiveTimeMultiplier = self._GetNextReproductiveTimeMultiplier()  # type: float

		if nextReproductiveTimeMultiplier != self._currentReproductiveTimeMultiplier:
			self._currentReproductiveTimeMultiplier = nextReproductiveTimeMultiplier
			self._OnUpdatedReproductiveTimeMultiplier()

	def _OnUpdatedReproductiveTimeMultiplier (self) -> None:
		pass

	def _SetGuideGroup (self) -> None:
		self._assignedGuides = CycleGuideGroups.FindGuideGroup(self.SimInfo)

	def _GetDefaultGuideGroup (self) -> CycleGuideGroups.GuideGroup:
		return CycleGuideGroups.HumanGuideGroup

	def _SetupInternal (self) -> None:
		self._RemoveInvalidTrackers()
		self._AddValidTrackers()

		for tracker in self._trackers:  # type: TrackerBase
			try:
				# noinspection PyProtectedMember
				tracker._Setup()
			except:
				Debug.Log("Failed to run _Setup method for a reproduction tracker at '" + Types.GetFullName(tracker) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

	def _SimulateInternal (self, ticks: int) -> None:
		if ticks <= 0:
			return

		try:
			self.Simulation = Simulation(self, ticks)  # type: Simulation
			self._PrepareForSimulation(self.Simulation)
			self.Simulation.Simulate()
			self._CleanUpSimulation(self.Simulation)
		finally:
			self.Simulation = None

	def _PlanSimulationInternal (self, simulation: Simulation) -> None:
		for tracker in self._trackers:  # type: TrackerBase
			try:
				# noinspection PyProtectedMember
				tracker._PlanSimulation(simulation)
			except:
				Debug.Log("Failed to run _PlanSimulation method for a reproduction tracker at '" + Types.GetFullName(tracker) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

	def _PrepareForSimulation (self, simulation: Simulation) -> None:
		self._UpdateReproductiveTimeMultiplier()

		for tracker in self._trackers:  # type: TrackerBase
			try:
				# noinspection PyProtectedMember
				tracker._PrepareForSimulation(simulation)
			except:
				Debug.Log("Failed to run _PrepareForSimulation method for a reproduction tracker at '" + Types.GetFullName(tracker) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

	def _CleanUpSimulation (self, simulation: Simulation) -> None:
		for tracker in self._trackers:  # type: TrackerBase
			try:
				# noinspection PyProtectedMember
				tracker._CleanUpSimulation(simulation)
			except:
				Debug.Log("Failed to run _CleanUpSimulation method for a reproduction tracker at '" + Types.GetFullName(tracker) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

	def _VerifyInternal (self) -> None:
		if self._assignedGuides is None or not self._assignedGuides.Matches(self.SimInfo):
			self._SetGuideGroup()

		self._RemoveInvalidTrackers()
		self._AddValidTrackers()

		for tracker in self._trackers:  # type: TrackerBase
			try:
				# noinspection PyProtectedMember
				tracker.Verify()
			except:
				Debug.Log("Failed to run Verify method for a reproduction tracker at '" + Types.GetFullName(tracker) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

	def _OnLoaded (self) -> None:
		self._Setup()

	def _OnResetted (self) -> None:
		self._Setup()

	def _LoadFromDictionaryInternal (self, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		superOperationSuccessful = super()._LoadFromDictionaryInternal(data, lastVersion)  # type: bool

		self._AddValidTrackers()

		operationSuccessful = True  # type: bool
		operationInformation = self.SavableOperationInformation  # type: str

		trackersSavingKey = self._trackersSavingKey  # type: str
		trackersDataSavingKey = "Data"  # type: str
		trackersTypeSavingKey = "Type"  # type: str

		try:
			trackersListData = data[trackersSavingKey]  # type: typing.Optional[list]
		except KeyError:
			return True

		if not isinstance(trackersListData, list):
			raise Exceptions.IncorrectTypeException(trackersListData, "data[%s]" % trackersSavingKey, (list,))

		for tracker in self._trackers:  # type: TrackerBase
			if not isinstance(tracker, TrackerBase):
				Debug.Log("Found an object in the trackers list that was not a tracker.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":TrackerSavingOperationNotTrackerType")
				continue

			try:
				for trackerDataIndex in range(len(trackersListData)):  # type: int
					trackerContainerData = trackersListData[trackerDataIndex]  # type: dict

					trackerTypeIdentifier = trackerContainerData.get(trackersTypeSavingKey, None)  # type: typing.Optional[str]

					if trackerTypeIdentifier is None or trackerTypeIdentifier != tracker.TypeIdentifier:
						continue

					if not isinstance(trackerContainerData, dict):
						raise Exceptions.IncorrectTypeException(trackerContainerData, "data[%s][%s]" % (trackersSavingKey, trackerDataIndex), (dict,))

					trackerData = trackerContainerData[trackersDataSavingKey]  # type: typing.Optional[dict]

					if not isinstance(trackerData, dict):
						raise Exceptions.IncorrectTypeException(trackerData, "data[%s][%s][%s]" % (trackersSavingKey, trackerDataIndex, trackersDataSavingKey), (dict,))

					if not tracker.LoadFromDictionary(trackerData, lastVersion = lastVersion):
						operationSuccessful = False

					break
			except:
				Debug.Log("Load operation in a savable object failed to load the tracker data of a tracker with the identifier '%s'.\n%s" % (tracker.TypeIdentifier, operationInformation), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				operationSuccessful = False

		if not operationSuccessful:
			return False

		return superOperationSuccessful

	def _SaveToDictionaryInternal (self) -> typing.Tuple[bool, dict]:
		superOperationSuccessful, data = super()._SaveToDictionaryInternal()  # type: bool, dict

		operationSuccessful = True  # type: bool
		operationInformation = self.SavableOperationInformation  # type: str

		trackersSavingKey = self._trackersSavingKey  # type: str
		trackersDataSavingKey = "Data"  # type: str
		trackersTypeSavingKey = "Type"  # type: str

		trackersListData = list()  # type: typing.List[typing.Optional[dict]]

		for tracker in self._trackers:  # type: TrackerBase
			if not isinstance(tracker, TrackerBase):
				Debug.Log("Found an object in the trackers list that was not a tracker.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":TrackerSavingOperationNotTrackerType")
				continue

			try:
				trackerContainerData = dict()  # type: dict
				entryOperationSuccessful, trackerData = tracker.SaveToDictionary()  # type: bool, dict

				if not entryOperationSuccessful:
					operationSuccessful = False

				trackerTypeIdentifier = tracker.TypeIdentifier  # type: str

				if not isinstance(trackerTypeIdentifier, str):
					raise Exceptions.IncorrectReturnTypeException(trackerTypeIdentifier, "typeFetcher", (str,))

				trackerContainerData[trackersTypeSavingKey] = trackerTypeIdentifier
				trackerContainerData[trackersDataSavingKey] = trackerData

				trackersListData.append(trackerContainerData)
			except:
				Debug.Log("Save operation in a savable object failed to save the tracker data of a tracker with the identifier '%s'.\n%s" % (tracker.TypeIdentifier, operationInformation), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				operationSuccessful = False

			data[trackersSavingKey] = trackersListData

		if not operationSuccessful:
			return False, data

		return superOperationSuccessful, data

	def _ResetInternal (self) -> bool:
		superOperationSuccessful = super()._ResetInternal()  # type: bool

		operationInformation = self.SavableOperationInformation  # type: str

		for tracker in self._trackers:  # type: TrackerBase
			if not isinstance(tracker, TrackerBase):
				Debug.Log("Found an object in the trackers list that was not a tracker.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":TrackerSavingOperationNotTrackerType")
				continue

			tracker.Reset()

		return superOperationSuccessful

	def _InvokeTrackerAddedEvent (self, tracker: TrackerBase) -> None:
		eventArguments = CycleEvents.TrackerAddedArguments(tracker)  # type: CycleEvents.TrackerAddedArguments

		for trackerAddedCallback in self.TrackerAddedEvent:
			try:
				trackerAddedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call tracker added callback '" + Types.GetFullName(trackerAddedCallback) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = trackerAddedCallback)

	def _InvokeTrackerRemovedEvent (self, tracker: TrackerBase) -> None:
		eventArguments = CycleEvents.TrackerRemovedArguments(tracker)  # type: CycleEvents.TrackerRemovedArguments

		for trackerRemovedCallback in self.TrackerRemovedEvent:
			try:
				trackerRemovedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call tracker removed callback '" + Types.GetFullName(trackerRemovedCallback) + "'.\n" + self.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = trackerRemovedCallback)

def GetGeneralReproductiveTimeMultiplier () -> float:
	return Settings.ReproductiveSpeed.Get()

def GameMinutesToTicks (gameMinutes: typing.Union[float, int]) -> int:
	"""
	Get the number of ticks the specified game minutes count for. 25 ticks is equal to 1 game second therefore precision between each 1/25th of a second
	will be lost as ticks can only be whole numbers.
	:param gameMinutes: The number of game minutes.
	:type gameMinutes: float | int
	:rtype: int
	"""

	if not isinstance(gameMinutes, (float, int)):
		raise Exceptions.IncorrectTypeException(gameMinutes, "gameMinutes", (float, int))

	if gameMinutes == float("infinity"):
		return gameMinutes

	return round(gameMinutes * date_and_time.SECONDS_PER_MINUTE * date_and_time.REAL_MILLISECONDS_PER_SIM_SECOND)

def GameMinutesToReproductiveMinutes (gameMinutes: typing.Union[float, int], reproductiveTimeMultiplier: typing.Union[float, int]) -> typing.Union[float, int]:
	"""
	Get how many minutes of "reproductive time" will pass within this many game minutes. All reproductive simulations should work with their real-life times,
	game time is simply scaled up to determine how much "reproductive time" has passed.
	:param gameMinutes: The number of minutes in game time.
	:type gameMinutes: float | int
	:param reproductiveTimeMultiplier: Divides the amount of game time that the ticks count for to get the reproductive time.
	:type reproductiveTimeMultiplier: float | int
	:rtype: int
	"""

	if not isinstance(gameMinutes, (float, int)):
		raise Exceptions.IncorrectTypeException(gameMinutes, "gameMinutes", (float, int))

	if not isinstance(reproductiveTimeMultiplier, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

	if reproductiveTimeMultiplier <= 0:
		raise ValueError("Reproductive time multipliers cannot be less than or equal to 0.")

	if gameMinutes == float("infinity"):
		return gameMinutes

	return gameMinutes / reproductiveTimeMultiplier

def TicksToGameMinutes (ticks: int) -> typing.Union[float, int]:
	"""
	Get how many game minutes the specified ticks count for.
	:param ticks: The number of game ticks.
	:type ticks: int
	:rtype: float | int
	"""

	if not isinstance(ticks, int):
		raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

	return date_and_time.ticks_to_time_unit(ticks, date_and_time.TimeUnit.MINUTES, True)  # type: typing.Union[float, int]

def TicksToReproductiveMinutes (ticks: int, reproductiveTimeMultiplier: typing.Union[float, int]) -> typing.Union[float, int]:
	"""
	Get how many minutes of "reproductive time" will pass within this many ticks. All reproductive simulations should work with their real-life times,
	game time is simply scaled up to determine how much "reproductive time" has passed.
	:param ticks: The number of game ticks.
	:type ticks: int
	:param reproductiveTimeMultiplier: Divides the amount of game time that the ticks count for to get the reproductive time.
	:type reproductiveTimeMultiplier: float | int
	:rtype: float | int
	"""

	if not isinstance(ticks, int):
		raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

	if not isinstance(reproductiveTimeMultiplier, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

	if reproductiveTimeMultiplier <= 0:
		raise ValueError("Reproductive time multipliers cannot be less than or equal to 0.")

	gameMinutes = TicksToGameMinutes(ticks)  # type: typing.Union[float, int]
	reproductiveMinutes = GameMinutesToReproductiveMinutes(gameMinutes, reproductiveTimeMultiplier)  # type: typing.Union[float, int]
	return reproductiveMinutes

def ReproductiveMinutesToTicks (reproductiveMinutes: typing.Union[float, int], reproductiveTimeMultiplier: typing.Union[float, int]) -> int:
	"""
	Get how many ticks will pass within this many minutes of "reproductive time". All reproductive simulations should work with their real-life times,
	game time is simply scaled up to determine how much "reproductive time" has passed. Depending on the reproductive time multiplier, some
	precision may be lost as a game tick cannot account for very small intervals of reproductive time.
	:param reproductiveMinutes: The number of minutes in reproductive time.
	:type reproductiveMinutes: float | int
	:param reproductiveTimeMultiplier: Multiplies the amount of reproductive time to get the game time, and from that the number of ticks is derived.
	:type reproductiveTimeMultiplier: float | int
	:rtype: int
	"""

	if not isinstance(reproductiveMinutes, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveMinutes, "reproductiveMinutes", (float, int))

	if not isinstance(reproductiveTimeMultiplier, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

	if reproductiveTimeMultiplier <= 0:
		raise ValueError("Reproductive time multipliers cannot be less than or equal to 0.")

	if reproductiveMinutes == float("infinity"):
		return reproductiveMinutes

	gameMinutes = ReproductiveMinutesToGameMinutes(reproductiveMinutes, reproductiveTimeMultiplier)  # type: typing.Union[float, int]
	return GameMinutesToTicks(gameMinutes)

def ReproductiveMinutesToGameMinutes (reproductiveMinutes: typing.Union[float, int], reproductiveTimeMultiplier: typing.Union[float, int]) -> typing.Union[float, int]:
	"""
	Get how many game minutes will pass within this many minutes of "reproductive time". All reproductive simulations should work with their real-life times,
	game time is simply scaled up to determine how much "reproductive time" has passed.
	:param reproductiveMinutes: The number of minutes in reproductive time.
	:type reproductiveMinutes: float | int
	:param reproductiveTimeMultiplier: Multiplies the amount of reproductive time to get the game time.
	:type reproductiveTimeMultiplier: float | int
	:rtype: int
	"""

	if not isinstance(reproductiveMinutes, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveMinutes, "reproductiveMinutes", (float, int))

	if not isinstance(reproductiveTimeMultiplier, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

	if reproductiveTimeMultiplier <= 0:
		raise ValueError("Reproductive time multipliers cannot be less than or equal to 0.")

	if reproductiveMinutes == float("infinity"):
		return reproductiveMinutes

	return reproductiveMinutes * reproductiveTimeMultiplier

def GetClosestPreciseReproductiveMinute (reproductiveMinutes: typing.Union[float, int], reproductiveTimeMultiplier: typing.Union[float, int]) -> typing.Union[float, int]:
	"""
	Get the closest reproductive minute to the input that does not take place between two ticks.
	:param reproductiveMinutes: The number of minutes in reproductive time.
	:type reproductiveMinutes: float | int
	:param reproductiveTimeMultiplier: Used to convert reproductive time to game time.
	:rtype: float | int
	"""

	if not isinstance(reproductiveMinutes, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveMinutes, "reproductiveMinutes", (float, int))

	if not isinstance(reproductiveTimeMultiplier, (float, int)):
		raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

	if reproductiveTimeMultiplier <= 0:
		raise ValueError("Reproductive time multipliers cannot be less than or equal to 0.")

	if reproductiveMinutes == float("infinity"):
		return reproductiveMinutes

	return TicksToReproductiveMinutes(ReproductiveMinutesToTicks(reproductiveMinutes, reproductiveTimeMultiplier), reproductiveTimeMultiplier)
