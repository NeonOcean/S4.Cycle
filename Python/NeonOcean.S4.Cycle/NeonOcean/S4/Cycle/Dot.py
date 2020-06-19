import enum_lib
import typing

import game_services
import services
import time_service
from NeonOcean.S4.Cycle import Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Cycle.Females.Cycle import Shared as CycleShared
from NeonOcean.S4.Cycle.Tools import SimPointer
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Saving import SectionBranched
from NeonOcean.S4.Main.Tools import Exceptions, Parse, Savable, Version
from sims import sim_info

if typing.TYPE_CHECKING:
	pass

DotSavingKey = "Dot"

_allDotInformation = dict()  # type: typing.Dict[int, DotInformation]

class TrackingMode(enum_lib.IntEnum):
	Cycle = 0  # type: TrackingMode
	Pregnancy = 1  # type: TrackingMode

class DotCycle:
	class _Phase:
		def __init__ (self,
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
		"""
		A simple object to temporarily hold information about where the dot app thinks a sim is on their menstrual cycle.
		"""

		self.Age = 0

		# noinspection PyProtectedMember
		self._phases = {
			CycleShared.MenstrualCyclePhases.Follicular: self._Phase(
				lambda: self.InFollicularPhase, lambda: self.FollicularLength, lambda: self.FollicularStartMinute, lambda: self.FollicularEndMinute
			),
			CycleShared.MenstrualCyclePhases.Ovulation: self._Phase(
				lambda: self.Ovulating, lambda: self.OvulationLength, lambda: self.OvulationStartMinute, lambda: self.OvulationEndMinute
			),
			CycleShared.MenstrualCyclePhases.Luteal: self._Phase(
				lambda: self.InLutealPhase, lambda: self.LutealLength, lambda: self.LutealStartMinute, lambda: self.LutealEndMinute
			),
			CycleShared.MenstrualCyclePhases.Menstruation: self._Phase(
				lambda: self.Menstruating, lambda: self.MenstruationLength, lambda: self.MenstruationStartMinute, lambda: self.MenstruationEndMinute
			),
		}  # type: typing.Dict[enum_lib.Enum, DotCycle._Phase]

	@property
	def Age (self) -> typing.Union[float, int]:
		"""
		The amount of time in game minutes that the cycle has been active.
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
			raise Exceptions.IncorrectTypeException(value, "Age", (float, int))

		if value < 0:
			raise ValueError("Progress values must be greater than or equal to 0.")

		self._age = self.Lifetime * value

	@property
	def Lifetime (self) -> float:
		"""
		The exact life time of this cycle in game minutes.
		"""

		return self.LutealEndMinute

	@property
	def FollicularLength (self) -> float:
		"""
		The amount of time in game minutes of the cycle's follicular phase.
		"""

		reproductiveTimeMultiplier = self._GetCycleReproductiveTimeMultiplier()  # type: float
		menstrualCycleGuide = self._GetMenstrualCycleGuide()  # type: CycleGuides.CycleMenstrualGuide
		return ReproductionShared.ReproductiveMinutesToGameMinutes(menstrualCycleGuide.FollicularLength.Mean, reproductiveTimeMultiplier)

	@property
	def FollicularStartMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that the follicular phase will start.
		"""

		return 0

	@property
	def FollicularEndMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that the follicular phase will end.
		"""

		return self.FollicularLength

	@property
	def InFollicularPhase (self) -> bool:
		"""
		Whether or not the cycle is in the follicular phase.
		"""

		return self.FollicularStartMinute <= self.Age < self.FollicularEndMinute

	@property
	def OvulationLength (self) -> float:
		"""
		The amount of time in game minutes in which ovulation will occur. The sim will start ovulating half of this many minutes before the follicular
		phase ends, and will stop ovulating half of this many minutes after the luteal phase starts.
		"""

		reproductiveTimeMultiplier = self._GetCycleReproductiveTimeMultiplier()  # type: float
		menstrualCycleGuide = self._GetMenstrualCycleGuide()  # type: CycleGuides.CycleMenstrualGuide
		return ReproductionShared.ReproductiveMinutesToGameMinutes(menstrualCycleGuide.OvulationLength.Mean, reproductiveTimeMultiplier)

	@property
	def OvulationStartMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that ovulation will start.
		"""

		return self.FollicularLength - self.OvulationLength / 2

	@property
	def OvulationEndMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that ovulation will end.
		"""

		return self.FollicularLength + self.OvulationLength / 2

	@property
	def Ovulating (self) -> bool:
		"""
		Whether or not ovulation is occurring.
		"""

		return self.OvulationStartMinute <= self.Age < self.OvulationEndMinute

	@property
	def LutealLength (self) -> float:
		"""
		The length of the cycle's luteal phase in game minutes.
		"""

		reproductiveTimeMultiplier = self._GetCycleReproductiveTimeMultiplier()  # type: float
		menstrualCycleGuide = self._GetMenstrualCycleGuide()  # type: CycleGuides.CycleMenstrualGuide
		return ReproductionShared.ReproductiveMinutesToGameMinutes(menstrualCycleGuide.LutealLength.Mean, reproductiveTimeMultiplier)

	@property
	def LutealStartMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that the luteal phase will start.
		"""

		return self.FollicularLength

	@property
	def LutealEndMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that the luteal phase will end.
		"""

		return self.FollicularLength + self.LutealLength

	@property
	def InLutealPhase (self) -> bool:
		"""
		Whether or not this cycle is in the luteal phase.
		"""

		return self.LutealStartMinute <= self.Age < self.LutealEndMinute

	@property
	def MenstruationLength (self) -> float:
		"""
		The length of the cycle's menstruation phase in game minutes.
		"""

		reproductiveTimeMultiplier = self._GetCycleReproductiveTimeMultiplier()  # type: float
		menstrualCycleGuide = self._GetMenstrualCycleGuide()  # type: CycleGuides.CycleMenstrualGuide
		return ReproductionShared.ReproductiveMinutesToGameMinutes(menstrualCycleGuide.MenstruationLength.Mean, reproductiveTimeMultiplier)

	@property
	def MenstruationStartMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that menstruation will start.
		"""

		return self.LutealEndMinute - self.MenstruationLength

	@property
	def MenstruationEndMinute (self) -> float:
		"""
		The amount of time in game minutes into the cycle that menstruation will end.
		"""

		return self.LutealEndMinute

	@property
	def Menstruating (self) -> bool:
		"""
		Whether or not menstruation is occurring.
		"""

		return self.MenstruationStartMinute < self.Age <= self.MenstruationEndMinute

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
		Get the amount of time in game minutes a phase lasts for.
		"""

		return self._phases[phase].Length

	def GetPhaseStartTime (self, phase: enum_lib.Enum) -> float:
		"""
		Get the start time in game minutes of the input phase.
		"""

		return self._phases[phase].StartTime

	def GetPhaseEndTime (self, phase: enum_lib.Enum) -> float:
		"""
		Get the end time in game minutes of the input phase.
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
		Get the length in game minutes of each phase.
		"""

		phaseLengths = dict()  # type: typing.Dict[enum_lib.Enum, float]

		for phaseType, phase in self._phases.items():
			phaseLengths[phaseType] = phase.Length

		return phaseLengths

	def GetAllPhaseStartTimes (self) -> typing.Dict[enum_lib.Enum, float]:
		"""
		Get the start time in game minutes of each phase.
		"""

		phaseStartTimes = dict()  # type: typing.Dict[enum_lib.Enum, float]

		for phaseType, phase in self._phases.items():
			phaseStartTimes[phaseType] = phase.StartTime

		return phaseStartTimes

	def GetAllPhaseEndTimes (self) -> typing.Dict[enum_lib.Enum, float]:
		"""
		Get the end time in game minutes of each phase.
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
		Get the time in game minutes until the input phase starts. This will return a negative number if the phase has already started.
		"""

		return self.GetPhaseStartTime(phase) - self.Age

	def GetTimeUntilPhaseEnds (self, phase: enum_lib.Enum) -> float:
		"""
		Get the time in game minutes until the input phase ends. This will return a negative number if the phase has already ended.
		"""

		return self.GetPhaseEndTime(phase) - self.Age

	def GetTimeUntilNextPhase (self) -> typing.Optional[float]:
		"""
		Get the amount of time in game minutes until the next phase starts. This may return none if no more phases will start before the cycle ends.
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

	def _GetCycleReproductiveTimeMultiplier (self) -> float:
		return FemalesShared.GetCycleTrackerReproductiveTimeMultiplier()

	def _GetMenstrualCycleGuide (self) -> CycleGuides.CycleMenstrualGuide:
		return CycleGuides.HumanCycleMenstrualGuide.Guide

class DotInformation(Savable.SavableExtension):
	def __init__ (self, targetSimInfoOrID: typing.Union[sim_info.SimInfo, int, None]):
		"""
		An object to save information for and handle interactions with the dot menstrual cycle tracker app.
		"""

		if not isinstance(targetSimInfoOrID, (sim_info.SimInfo, int)) and targetSimInfoOrID is not None:
			raise Exceptions.IncorrectTypeException(targetSimInfoOrID, "targetSimInfoOrID", (sim_info.SimInfo, int, None))

		super().__init__()

		self._targetSimPointer = SimPointer.SimPointer()
		self._targetSimPointer.ChangePointer(targetSimInfoOrID)

		self.Enabled = False
		self.TrackingMode = TrackingMode.Cycle

		self.TimeSinceCycleStart = None
		self.LastSimulatedTick = services.time_service().sim_now.absolute_ticks()

		encodeEnum = lambda value: value.name if value is not None else None
		decodeTrackingMode = lambda valueString: Parse.ParsePythonEnum(valueString, TrackingMode)

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Enabled", "Enabled", self.Enabled))  # TODO add type verifiers to values without built in verifiers else where.
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("TrackingMode", "TrackingMode", self.TrackingMode, encoder = encodeEnum, decoder = decodeTrackingMode))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("TimeSinceCycleStart", "TimeSinceCycleStart", self.TimeSinceCycleStart))

	@property
	def TargetSimInfo (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that this dot object is handling.
		"""

		return self._targetSimPointer.GetSim()

	@property
	def TargetSimID (self) -> typing.Optional[int]:
		"""
		The id of the sim that this dot object is handling.
		"""

		return self._targetSimPointer.SimID

	@property
	def Enabled (self) -> bool:
		"""
		Whether or not the dot app is installed on the target sim's phone.
		"""

		return self._enabled

	@Enabled.setter
	def Enabled (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Enabled", (bool,))

		self._enabled = value

	@property
	def TrackingMode (self) -> TrackingMode:
		"""
		Whether the app is currently tracking the target sim's menstrual cycle or pregnancy.
		"""

		return self._trackingMode

	@TrackingMode.setter
	def TrackingMode (self, value: TrackingMode) -> None:
		if not isinstance(value, TrackingMode):
			raise Exceptions.IncorrectTypeException(value, "TrackingMode", (TrackingMode,))

		self._trackingMode = value

	@property
	def TimeSinceCycleStart (self) -> typing.Optional[float]:
		"""
		The time in reproductive minutes since the target sim's last known cycle start.
		"""

		return self._timeSinceCycleStart

	@TimeSinceCycleStart.setter
	def TimeSinceCycleStart (self, value: typing.Optional[float]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "TimeSinceCycleStart", (float, int, None))

		self._timeSinceCycleStart = value

	@property
	def LastSimulatedTick (self) -> int:
		"""
		The tick this dot information was last simulated to. This value isn't saved, when the dot information is first creating it is assumed the it was
		simulated up to now. All dot information objects should be updated before being saved to prevent missed time.
		"""

		return self._lastSimulatedTick

	@LastSimulatedTick.setter
	def LastSimulatedTick (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "LastSimulatedTick", (int,))

		self._lastSimulatedTick = value

	@property
	def TicksBehind (self) -> int:
		"""
		The number of game ticks the information object is behind the current game tick.
		"""

		timeService = services.time_service()  # type: time_service.TimeService
		return max(timeService.sim_now.absolute_ticks() - self.LastSimulatedTick, 0)

	@property
	def Outdated (self) -> bool:
		"""
		Whether or not this dot information has been updated all the way to the latest tick. If the game's time service is not available this will return False.
		"""

		if game_services.service_manager is None:
			return False

		timeService = services.time_service()  # type: time_service.TimeService

		return self.LastSimulatedTick < timeService.sim_now.absolute_ticks()

	@property
	def ReproductiveTimeMultiplier (self) -> typing.Union[float, int]:
		"""
		Get the value that is divided with the game time to get the reproductive time and multiplied with the reproductive time to get the game time.
		"""

		return FemalesShared.GetCycleTrackerReproductiveTimeMultiplier()

	def Update (self) -> None:
		"""
		Update this dot app information to the most recent tick.
		"""

		if game_services.service_manager is None:
			return

		if not self.Outdated:
			return

		ticksBehind = self.TicksBehind

		if ticksBehind <= 0:
			return

		self.Simulate(ticksBehind)

	def Simulate (self, ticks: int) -> None:
		"""
		Simulate this many ticks for this dot app information. This method could allow you to simulate time that hasn't actually passed. The dot app information
		should be simulated every time the target sim's reproductive system simulates.
		:param ticks: The number of ticks to simulate.
		:type ticks: int
		"""

		if not isinstance(ticks, int):
			raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

		self._SimulateInternal(ticks)

		timeService = services.time_service()  # type: time_service.TimeService
		currentTick = timeService.sim_now.absolute_ticks()  # type: int

		self.LastSimulatedTick = min(self.LastSimulatedTick + ticks, currentTick)

	def GetCurrentCycle (self) -> typing.Optional[DotCycle]:
		"""
		Get information about the current cycle, according to the dot app. This will be none if the app is not tracking the cycle, the target sim does not exists,
		the target sim cannot menstruate, or we don't know when the last menstrual cycle occurred.
		"""

		if self.TrackingMode != TrackingMode.Cycle:
			return None

		if self.TimeSinceCycleStart is None:
			return None

		gameTimeSinceCycleStart = ReproductionShared.ReproductiveMinutesToGameMinutes(self.TimeSinceCycleStart, self.ReproductiveTimeMultiplier)  # type: float

		cycleInformation = DotCycle()
		cycleInformation.Age = gameTimeSinceCycleStart % cycleInformation.Lifetime
		return cycleInformation

	def SetCycleStart (self, minutesSince: float) -> None:
		"""
		Set the suspected start of the target's cycle.
		:param minutesSince: The number of reproductive minutes since the cycle started.
		:type minutesSince: float
		"""

		if not isinstance(minutesSince, (float, int)):
			raise Exceptions.IncorrectTypeException(minutesSince, "minutesSince", (float, int))

		self.TimeSinceCycleStart = minutesSince

	def _SimulateInternal (self, ticks: int) -> None:
		if ticks <= 0:
			return

		if self.TimeSinceCycleStart is not None:
			simulatingMinutes = ReproductionShared.TicksToReproductiveMinutes(ticks, self.ReproductiveTimeMultiplier)  # type: float
			self.TimeSinceCycleStart += simulatingMinutes

def CreateDotInformation (targetSimInfo: sim_info.SimInfo) -> DotInformation:
	"""
	Create a new set of dot information for the target sim. If such information already exists it will be replaced with the new one.
	"""

	targetDotInformation = DotInformation(targetSimInfo)  # type: DotInformation
	_RegisterDotInformation(targetSimInfo.id, targetDotInformation)

	return targetDotInformation

def GetDotInformation (targetSimInfo: sim_info.SimInfo, automaticallyUpdate: bool = True) -> typing.Optional[DotInformation]:
	"""
	Get the dot app information for the target sim. This can return none if no dot app information has been created for this sim yet.
	:param targetSimInfo: The info of the sim to get the dot information of.
	:type targetSimInfo: sim_info.SimInfo
	:param automaticallyUpdate: Whether or not we should automatically update the dot information before returning it. An information object should be updated
	before  using it or it may be incorrect.
	:type automaticallyUpdate: bool
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	if not isinstance(automaticallyUpdate, bool):
		raise Exceptions.IncorrectTypeException(automaticallyUpdate, "automaticallyUpdate", (bool,))

	targetDotInformation = _allDotInformation.get(targetSimInfo.id, None)  # type: DotInformation

	if automaticallyUpdate and targetDotInformation is not None:
		targetDotInformation.Update()

	return targetDotInformation

def HasDotInformation (targetSimInfo: sim_info.SimInfo) -> bool:
	"""
	Get whether or not the target sim has had a dot information object created for them.
	"""

	return targetSimInfo.id in _allDotInformation

def GetAllDotInformation (automaticallyUpdate: bool = True) -> typing.Dict[int, DotInformation]:
	"""
	Get all dot app information objects. This will return a dict of sim ids as the keys and dot information objects as the key's values.
	:param automaticallyUpdate: Whether or not we should automatically update the dot information before returning it. An information object should be updated
	before using it or it may be incorrect.
	:type automaticallyUpdate: bool
	"""

	if automaticallyUpdate:
		for dotInformation in _allDotInformation.values():  # type: sim_info.SimInfo, DotInformation
			dotInformation.Update()

	return dict(_allDotInformation)

def ClearDotInformation (targetSimInfo: sim_info.SimInfo) -> None:
	"""
	Clear out the saved dot information for the target sim.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	_allDotInformation.pop(targetSimInfo.id, None)

def ClearAllDotInformation () -> None:
	"""
	Clear out every dot information object for every sim.
	"""

	global _allDotInformation
	_allDotInformation = dict()

def LoadAllDotInformation (simsSection: typing.Optional[SectionBranched.SectionBranched] = None) -> bool:
	operationSuccessful = True  # type: bool

	try:
		if simsSection.SavingObject.DataHostVersion is not None:
			try:
				lastVersion = Version.Version(simsSection.SavingObject.DataHostVersion)  # type: typing.Optional[Version.Version]
			except:
				Debug.Log("Failed to parse the data host version value '%s' as a version number" % simsSection.SavingObject.DataHostVersion, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__) #TODO fix
				lastVersion = None
		else:
			lastVersion = None  # type: typing.Optional[Version.Version]

		for dotInformation in _allDotInformation.values():  # type: DotInformation
			targetSimID = dotInformation.TargetSimID  # type: int

			savedDotInformationData = simsSection.GetValue(str(targetSimID), DotSavingKey)  # type: dict

			if not isinstance(savedDotInformationData, dict):
				Debug.Log("The value for the sim saving section branch '%s' is not a dictionary.\nSaving Key: %s" % (str(targetSimID), DotSavingKey), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
				operationSuccessful = False
				continue

			dotInformation.LoadFromDictionary(savedDotInformationData, lastVersion = lastVersion)
	except:
		Debug.Log("At least partially failed to load all dot information.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
		operationSuccessful = False

	return operationSuccessful

def SaveAllDotInformation (simsSection: typing.Optional[SectionBranched.SectionBranched] = None) -> bool:
	operationSuccessful = True  # type: bool

	try:
		for targetSimID, targetDotInformation in _allDotInformation.items():  # type: int, DotInformation
			targetSimIDString = str(targetSimID)  # type: str

			try:
				saveSuccessful, targetDotInformationData = targetDotInformation.SaveToDictionary()  # type: dict

				if not saveSuccessful:
					operationSuccessful = False

				simsSection.Set(str(targetSimID), DotSavingKey, targetDotInformationData)
			except:
				Debug.Log("Failed to save dot information to the sim saving section branch '%s'.\nSaving Key: %s" % (targetSimIDString, DotSavingKey), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
				operationSuccessful = False
				continue
	except:
		Debug.Log("At least partially failed to save all dot information.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
		operationSuccessful = False

	return operationSuccessful

# noinspection PyUnusedLocal
def ResetAllDotInformation (simsSection: typing.Optional[SectionBranched.SectionBranched] = None) -> bool:
	operationSuccessful = True  # type: bool

	try:
		ClearAllDotInformation()
	except:
		operationSuccessful = False

	return operationSuccessful

def _RegisterDotInformation (targetSimID: int, targetDotInformation: DotInformation) -> None:
	_allDotInformation[targetSimID] = targetDotInformation
