from __future__ import annotations

import abc
import typing
import enum_lib
import uuid

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Females.Cycle import Shared as CycleShared, OvumRelease as CycleOvumRelease
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Version

class CycleBase(abc.ABC, Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	_uniqueIdentifierSavingKey = "UniqueIdentifier"  # type: str
	_uniqueSeedSavingKey = "UniqueSeed"  # type: str

	_ovumReleasesOldSavingKey = "OvumReleaseTimes"  # type: str
	_ovumReleasesSavingKey = "OvumReleases"  # type: str

	class _Phase:
		def __init__(self,
					 activeGetter: typing.Callable[[], bool],
					 lengthGetter: typing.Callable[[], float],
					 startTimeGetter: typing.Callable[[], float],
					 endTimeGetter: typing.Callable[[], float]):

			self.ActiveGetter = activeGetter
			self.LengthGetter = lengthGetter
			self.StartTimeGetter = startTimeGetter
			self.EndTimeGetter = endTimeGetter

		@property
		def Active (self) -> bool:
			return self.ActiveGetter()

		@property
		def Length (self) -> float:
			return self.LengthGetter()

		@property
		def StartTime (self) -> float:
			return self.StartTimeGetter()

		@property
		def EndTime (self) -> float:
			return self.EndTimeGetter()

	def __init__ (self):
		super().__init__()

		self._uniqueIdentifier = None  # type: typing.Optional[uuid.UUID]
		self._uniqueSeed = None  # type: typing.Optional[int]

		self.CompletedCallback = None
		self.ReleasedOvumCallback = None

		self.OvumReleases = list()
		self.Age = 0

		self.OvumReleaseDelays = 0

		# noinspection PyProtectedMember
		self._phases = {}  # type: typing.Dict[enum_lib.Enum, CycleBase._Phase]

		encodeUUID = lambda value: str(value) if value is not None else None
		decodeUUID = lambda valueString: uuid.UUID(valueString) if valueString is not None else None

		# noinspection PyUnusedLocal
		def uniqueSeedUpdater (data: dict, lastVersion: typing.Optional[Version.Version]) -> None:
			if isinstance(data.get(self._uniqueSeedSavingKey, None), list):
				data.pop(self._uniqueSeedSavingKey)

		def uniqueIdentifierVerifier (value: typing.Optional[uuid.UUID]) -> None:
			if not isinstance(value, uuid.UUID) and value is not None:
				raise Exceptions.IncorrectTypeException(value, self._uniqueIdentifierSavingKey, (uuid.UUID, None))

		def uniqueSeedVerifier (value: typing.Optional[int]) -> None:
			if not isinstance(value, int) and value is not None:
				raise Exceptions.IncorrectTypeException(value, self._uniqueSeedSavingKey, (int, None))

		# noinspection PyUnusedLocal
		def ovumReleasesUpdater (data: dict, lastVersion: typing.Optional[Version.Version]) -> None:
			if self._ovumReleasesOldSavingKey in data and not self._ovumReleasesSavingKey in data:
				data[self._ovumReleasesSavingKey] = data[self._ovumReleasesOldSavingKey]

			if not self._ovumReleasesSavingKey in data:
				return

			ovumReleasesData = data[self._ovumReleasesSavingKey]  # type: typing.List[typing.Union[float, int, dict]]

			if not isinstance(ovumReleasesData, list):
				return

			for ovumReleaseDataIndex in range(len(ovumReleasesData)):  # type: int
				ovumReleaseData = ovumReleasesData[ovumReleaseDataIndex]  # type: typing.Union[float, int, dict]

				if isinstance(ovumReleaseData, (float, int)):
					ovumRelease = CycleOvumRelease.OvumRelease()
					ovumRelease.BaseReleaseMinute = ovumReleaseData
					ovumReleasesData[ovumReleaseDataIndex] = {
						"Data": ovumRelease.SaveToDictionary()[1]
					}

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler(self._uniqueIdentifierSavingKey, "_uniqueIdentifier", None, encoder = encodeUUID, decoder = decodeUUID, typeVerifier = uniqueIdentifierVerifier))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler(self._uniqueSeedSavingKey, "_uniqueSeed", None, updater = uniqueSeedUpdater, typeVerifier = uniqueSeedVerifier))

		self.RegisterSavableAttribute(Savable.ListedSavableAttributeHandler(
			self._ovumReleasesSavingKey,
			"OvumReleases",
			lambda: CycleOvumRelease.OvumRelease(),
			lambda: list(),
			requiredSuccess = False,
			requiredEntrySuccess = False,
			updater = ovumReleasesUpdater))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Age", "Age", self.Age))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("OvumReleaseDelays", "OvumReleaseDelays", self.OvumReleaseDelays))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	@abc.abstractmethod
	def TypeIdentifier (cls) -> str:
		"""
		This cycle type's identifier, this is used to save and load the cycle. Loading will not be possible unless the cycle type is registered
		through the function in the cycle types module.
		"""

		...

	@property
	def UniqueIdentifier (self) -> uuid.UUID:
		"""
		An identifier for this object.
		"""

		if self._uniqueIdentifier is None:
			self._uniqueIdentifier = uuid.uuid4()

		return self._uniqueIdentifier

	@property
	def UniqueSeed (self) -> int:
		"""
		A unique seed for this object.
		"""

		if self._uniqueSeed is None:
			import random
			self._uniqueSeed = random.randint(-1000000000, 1000000000)

		return self._uniqueSeed

	@property
	def CompletedCallback (self) -> typing.Optional[typing.Callable]:
		"""
		Callback that will be triggered once this cycle has completed. This should be set by the cycle tracker when this cycle becomes active.
		The callback should take one argument, the reason why it ended in the form of a CompletionReasons enum.
		"""

		return self._completedCallback

	@CompletedCallback.setter
	def CompletedCallback (self, value: typing.Optional[typing.Callable]) -> None:
		if not isinstance(value, typing.Callable) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "CompletedCallback", ("Callable", None))

		self._completedCallback = value

	@property
	def ReleasedOvumCallback (self) -> typing.Optional[typing.Callable]:
		"""
		Callback that will be triggered once an egg cell was released by the cycle. This should be set by the cycle tracker when this cycle
		becomes active. The callback should take one argument, the ovum release object that indicates one should be releasing.
		"""

		return self._releasedOvumCallback

	@ReleasedOvumCallback.setter
	def ReleasedOvumCallback (self, value: typing.Optional[typing.Callable]) -> None:
		if not isinstance(value, typing.Callable) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "ReleasedOvumCallback", ("Callable", None))

		self._releasedOvumCallback = value

	@property
	def OvumReleases (self) -> typing.List[CycleOvumRelease.OvumRelease]:
		"""
		A list of ovum release objects that indicate at what time a single egg cell should be released.
		"""

		return self._ovumReleases

	@OvumReleases.setter
	def OvumReleases (self, value: typing.List[CycleOvumRelease.OvumRelease]) -> None:
		if not isinstance(value, list):
			raise Exceptions.IncorrectTypeException(value, "OvumReleases", (list,))

		for valueIndex in range(len(value)):
			if not isinstance(value[valueIndex], CycleOvumRelease.OvumRelease):
				raise Exceptions.IncorrectTypeException(value[valueIndex], "OvumReleases[%s]" % valueIndex, (CycleOvumRelease.OvumRelease, ))

		self._ovumReleases = value

	@property
	def OvumReleaseAmount (self) -> int:
		"""
		The amount of egg cells that will be released this cycle.
		"""

		return len(self.OvumReleases)

	@property
	def Anovulatory (self) -> bool:
		"""
		Whether or not this cycle is anovulatory. If no egg cells are set to be released, this cycle is anovulatory.
		"""

		return self.OvumReleaseAmount <= 0

	@property
	def Lifetime (self) -> typing.Union[float, int]:
		"""
		The exact life time of this cycle in reproductive minutes.
		"""

		return 0

	@property
	def Age (self) -> typing.Union[float, int]:
		"""
		The amount of time in reproductive minutes that this cycle has been active.
		"""

		return self._age

	@Age.setter
	def Age (self, value: typing.Union[float, int]) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Age", (float, int))

		if value < 0:
			raise ValueError("Age values must be greater than or equal to 0.")

		self._age = value

	@property
	def Progress (self) -> float:
		"""
		The percentage of the cycle's life time that has already completed.
		"""

		lifeTime = self.Lifetime  # type: float

		if lifeTime == 0:
			return 0
		else:
			return self.Age / self.Lifetime

	@Progress.setter
	def Progress (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "Progress", (float, int))

		if value < 0:
			raise ValueError("Progress values must be greater than or equal to 0.")

		self._age = self.Lifetime * value

	@property
	def TimeRemaining (self) -> typing.Union[float, int]:
		"""
		The amount of time remaining for this cycle in reproductive minutes.
		"""

		return max(0, self.Lifetime - self.Age)

	@property
	def Completed (self) -> bool:
		"""
		Whether or not this cycle has finished running.
		"""

		return self.TimeRemaining <= 0

	@classmethod
	@abc.abstractmethod
	def GetGenerationArgumentsType (cls, target: ReproductionShared.ReproductiveSystem) -> typing.Type[CycleEvents.CycleGeneratingArguments]:
		"""
		Get the type of generating event arguments to be used in generating a cycle.
		"""

		...

	@classmethod
	@abc.abstractmethod
	def GetCycleGuide (cls, target: ReproductionShared.ReproductiveSystem) -> CycleGuides.CycleGuide:
		"""
		Get the cycle guide applicable to this cycle type.
		"""

		...

	def GetPhaseIsActive (self, phase: enum_lib.Enum) -> bool:
		"""
		Get whether or not a phase is active.
		"""

		return self._phases[phase].Active

	def GetPhaseCompleted (self, phase: enum_lib.Enum) -> bool:
		"""
		Get whether or not a phase has already completed.
		"""

		requestedPhase = self._phases[phase]

		if requestedPhase.Active:
			return False

		return requestedPhase.EndTime < self.Age

	def GetPhaseLength (self, phase: enum_lib.Enum) -> float:
		"""
		Get the amount of time in reproductive minutes a phase lasts for.
		"""

		return self._phases[phase].Length

	def GetPhaseStartTime (self, phase: enum_lib.Enum) -> float:
		"""
		Get the start time in reproductive minutes of the input phase.
		"""

		return self._phases[phase].StartTime

	def GetPhaseEndTime (self, phase: enum_lib.Enum) -> float:
		"""
		Get the end time in reproductive minutes of the input phase.
		"""

		return self._phases[phase].EndTime

	def GetAllActivePhases (self) -> typing.Set[enum_lib.Enum]:
		"""
		Get a set of all active phases.
		"""

		activePhases = set()  # type: typing.Set[enum_lib.Enum]

		for phaseType, phase in self._phases.items():
			if phase.Active:
				activePhases.add(phaseType)

		return activePhases

	def GetUpcomingPhases (self) -> typing.Set[enum_lib.Enum]:
		"""
		Get a set of all cycle phases that have yet to begin.
		"""

		upcomingPhases = set()  # type: typing.Set[enum_lib.Enum]

		for phaseType, phase in self._phases.items():
			if phase.StartTime > self.Age:
				upcomingPhases.add(phaseType)

		return upcomingPhases

	def GetAllPhaseLengths (self) -> typing.Dict[enum_lib.Enum, float]:
		"""
		Get the length in reproductive minutes of each phase.
		"""

		phaseLengths = dict()  # type: typing.Dict[enum_lib.Enum, float]

		for phaseType, phase in self._phases.items():
			phaseLengths[phaseType] = phase.Length

		return phaseLengths

	def GetAllPhaseStartTimes (self) -> typing.Dict[enum_lib.Enum, float]:
		"""
		Get the start time in reproductive minutes of each phase.
		"""

		phaseStartTimes = dict()  # type: typing.Dict[enum_lib.Enum, float]

		for phaseType, phase in self._phases.items():
			phaseStartTimes[phaseType] = phase.StartTime

		return phaseStartTimes

	def GetAllPhaseEndTimes (self) -> typing.Dict[enum_lib.Enum, float]:
		"""
		Get the end time in reproductive minutes of each phase.
		"""

		phaseEndTimes = dict()  # type: typing.Dict[enum_lib.Enum, float]

		for phaseType, phase in self._phases.items():
			phaseEndTimes[phaseType] = phase.EndTime

		return phaseEndTimes

	def GetPhaseCompletionPercentage (self, phase: enum_lib.Enum) -> typing.Optional[float]:
		"""
		Get the percentage of the way this phase is to being completed.
		:return: A number from 0 to 1 or none if the phase is not active.
		:rtype: typing.Optional[float]
		"""

		phaseActive = self.GetPhaseIsActive(phase)  # type: bool

		if not phaseActive:
			return None

		phaseStartTime = self.GetPhaseStartTime(phase)  # type: float
		minutesIntoPhase = self.Age - phaseStartTime  # type: float

		if minutesIntoPhase <= 0:
			return 0

		phaseLength = self.GetPhaseLength(phase)  # type: float
		completionPercentage = minutesIntoPhase / phaseLength

		return max(min(completionPercentage, 1), 0)

	def GetTimeUntilPhaseStarts (self, phase: enum_lib.Enum) -> float:
		"""
		Get the time in reproductive minutes until the input phase starts. This will return a negative number if the phase has already started.
		"""

		return self.GetPhaseStartTime(phase) - self.Age

	def GetTimeUntilPhaseEnds (self, phase: enum_lib.Enum) -> float:
		"""
		Get the time in reproductive minutes until the input phase ends. This will return a negative number if the phase has already ended.
		"""

		return self.GetPhaseEndTime(phase) - self.Age

	def GetTimeUntilNextPhase (self) -> typing.Optional[float]:
		"""
		Get the amount of time in reproductive minutes until the next phase starts. This may return none if no more phases will start before the cycle ends.
		"""

		allPhaseStartTimes = self.GetAllPhaseStartTimes()  # type: typing.Dict[enum_lib.Enum, float]

		timeUntilNextPhase = None  # type: typing.Optional[float]
		for phaseType, phaseStartTime in allPhaseStartTimes:  # type: enum_lib.Enum, float
			timeUntilPhaseStart = phaseStartTime - self.Age  # type: float

			if timeUntilPhaseStart <= 0:
				continue

			if timeUntilPhaseStart > timeUntilNextPhase:
				continue

			timeUntilNextPhase = timeUntilPhaseStart

		return timeUntilNextPhase

	def GetNextPhase (self) -> typing.Optional[enum_lib.Enum]:
		"""
		Get the phase that will start next. This may return none if no more phases will start before the cycle ends.
		"""

		allPhaseStartTimes = self.GetAllPhaseStartTimes()  # type: typing.Dict[enum_lib.Enum, float]

		nextPhase = None  # type: typing.Optional[enum_lib.Enum]
		timeUntilNextPhase = None  # type: typing.Optional[float]
		for phaseType, phaseStartTime in allPhaseStartTimes:  # type: enum_lib.Enum, float
			timeUntilPhaseStart = phaseStartTime - self.Age  # type: float

			if timeUntilPhaseStart <= 0:
				continue

			if timeUntilPhaseStart > timeUntilNextPhase:
				continue

			nextPhase = phaseType
			timeUntilNextPhase = timeUntilPhaseStart

		return nextPhase

	def End (self, completedReason: CycleShared.CompletionReasons = CycleShared.CompletionReasons.Unknown) -> None:
		"""
		End this cycle, sending the signal that this cycle has completed. This can be called even if it hasn't actually ended.
		:param completedReason: The reason why this cycle has completed.
		:type completedReason: CompletionReasons
		"""

		if not isinstance(completedReason, CycleShared.CompletionReasons):
			raise Exceptions.IncorrectTypeException(completedReason, "completedReason", (CycleShared.CompletionReasons,))

		self.Age = self.Lifetime

		if self.CompletedCallback is None:
			Debug.Log("Missing callback to be triggered on cycle completion.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
		else:
			self.CompletedCallback(completedReason)

	def Generate (self, generationArguments: CycleEvents.CycleGeneratingArguments) -> None:
		"""
		Fill the cycle object's attributes with instruction from the input.
		:param generationArguments: Event arguments to instruct how to set the cycle's attributes.
		:type generationArguments: EventsCycle.CycleGeneratingArguments
		"""

		if not isinstance(generationArguments, CycleEvents.CycleGeneratingArguments):
			raise Exceptions.IncorrectTypeException(generationArguments, "generationArguments", (CycleEvents.CycleGeneratingArguments,))

		generationArguments.PreGenerationEvent.Invoke(generationArguments, Events.EventArguments())
		self._GenerateInternal(generationArguments)
		generationArguments.PostGenerationEvent.Invoke(generationArguments, Events.EventArguments())

	def Simulate (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: typing.Union[float, int]) -> None:
		"""
		Simulate this many ticks in this object, invoking any events that occurred and adding to the progress value.
		:param simulation: The simulation object that is guiding this simulation.
		:type simulation: ReproductionShared.Simulation
		:param ticks: The number of ticks to simulate.
		:type ticks: int
		:param reproductiveTimeMultiplier: Divided by the amount of game time that the ticks count for to get the amount of time to simulate.  All reproductive
		simulations work in real-life time.
		:type reproductiveTimeMultiplier: typing.Union[float, int]
		"""

		if not isinstance(simulation, ReproductionShared.Simulation):
			raise Exceptions.IncorrectTypeException(simulation, "simulation", (ReproductionShared.Simulation,))

		if not isinstance(ticks, int):
			raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

		if not isinstance(reproductiveTimeMultiplier, (float, int)):
			raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

		if ticks <= 0:
			return

		if reproductiveTimeMultiplier <= 0:
			raise ValueError("The parameter 'reproductiveTimeMultiplier' cannot be less than or equal to 0.")

		self._SimulateInternal(simulation, ticks, reproductiveTimeMultiplier)

	def PlanSimulation (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: typing.Union[float, int]) -> None:
		"""
		Plan out a simulation. Any tick that needs to be stopped at within the simulation's remaining ticks will to be added to the schedule. This method may be called
		more than once in a single simulation in order to replan any time remaining.
		:param simulation: The simulation object that needs to be worked on.
		:type simulation: Simulation
		:param reproductiveTimeMultiplier: Divided by the amount of game time that the ticks count for to get the amount of time to simulate.  All reproductive
		simulations work in real-life time
		:type reproductiveTimeMultiplier: float | int
		"""

		if not isinstance(simulation, ReproductionShared.Simulation):
			raise Exceptions.IncorrectTypeException(simulation, "simulation", (ReproductionShared.Simulation,))

		if not isinstance(reproductiveTimeMultiplier, (float, int)):
			raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

		self._PlanSimulationInternal(simulation, reproductiveTimeMultiplier)

	def GetDebugNotificationString (self) -> str:
		cycleDebugFormatting = "Cycle:\n" \
							   "  Type: %s\n" \
							   "  Length: %s minutes\n" \
							   "  Age: %s minutes\n" \
							   "  Ova Releasing: %s"

		length = round(self.Lifetime)  # type: typing.Union[float, int]
		age = round(self.Age)  # type: typing.Union[float, int]

		return cycleDebugFormatting % (self.TypeIdentifier, length, age, len(self.OvumReleases))

	def _GenerateInternal (self, generationArguments: CycleEvents.CycleGeneratingArguments) -> None:
		self._uniqueIdentifier = generationArguments.GetUniqueIdentifier()
		self._uniqueSeed = generationArguments.GetUniqueSeed()

		for ovumReleaseTime in generationArguments.GetOvumReleaseTimes():  # type: float
			ovumRelease = CycleOvumRelease.OvumRelease()  # type: CycleOvumRelease.OvumRelease
			ovumRelease.BaseReleaseMinute = ovumReleaseTime

			self._ovumReleases.append(ovumRelease)

	# noinspection PyUnusedLocal
	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: typing.Union[float, int]) -> None:
		lastAgeTick = ReproductionShared.ReproductiveMinutesToTicks(self.Age, reproductiveTimeMultiplier)  # type: int
		nextAgeTick = lastAgeTick + ticks  # type: int

		self.Age = ReproductionShared.TicksToReproductiveMinutes(nextAgeTick, reproductiveTimeMultiplier)

		releasingOva = list()  # type: typing.List[CycleOvumRelease.OvumRelease]
		ended = False  # type: bool

		for ovumRelease in self.OvumReleases:  # type: CycleOvumRelease.OvumRelease
			if ovumRelease.Released:
				continue

			ovumReleaseTime = ovumRelease.ReleaseMinute  # type: float
			ovumReleaseTick = ReproductionShared.ReproductiveMinutesToTicks(ovumReleaseTime, reproductiveTimeMultiplier)  # type: int

			if lastAgeTick < ovumReleaseTick <= nextAgeTick:
				releasingOva.append(ovumRelease)

		endTick = ReproductionShared.ReproductiveMinutesToTicks(self.Lifetime, reproductiveTimeMultiplier)  # type: typing.Union[float, int]
		if lastAgeTick < endTick <= nextAgeTick:
			ended = True

		if len(releasingOva) != 0:
			if self.ReleasedOvumCallback is None:
				Debug.Log("Missing callback to be triggered on ovum release.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			else:
				for ovumRelease in releasingOva:  # type: CycleOvumRelease.OvumRelease
					self.ReleasedOvumCallback(ovumRelease)

		if ended:
			self.End(completedReason = CycleShared.CompletionReasons.Finished)

	def _PlanSimulationInternal (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: typing.Union[float, int]) -> None:
		ticksToCompletion = ReproductionShared.ReproductiveMinutesToTicks(self.TimeRemaining, reproductiveTimeMultiplier)  # type: int

		if simulation.RemainingTicks >= ticksToCompletion:
			simulation.Schedule.AddPoint(ticksToCompletion)

		for ovumRelease in self.OvumReleases:  # type: CycleOvumRelease.OvumRelease
			if ovumRelease.Released:
				continue

			ovumReleaseTime = ovumRelease.ReleaseMinute  # type: float
			minutesToOvumRelease = ovumReleaseTime - self.Age  # type: float

			if minutesToOvumRelease <= 0:
				continue

			ticksToOvumRelease = ReproductionShared.ReproductiveMinutesToTicks(minutesToOvumRelease, reproductiveTimeMultiplier)  # type: int

			if ticksToOvumRelease <= 0:
				continue

			if simulation.RemainingTicks >= ticksToOvumRelease:
				simulation.Schedule.AddPoint(ticksToOvumRelease)
