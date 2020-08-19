from __future__ import annotations

import random
import typing
import uuid

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, This
from NeonOcean.S4.Cycle.Tools import Distribution, SimPointer
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Events, Exceptions, Python, Sims as ToolsSims, Savable, Version
from sims import sim_info

class Sperm(Savable.SavableExtension):
	# TODO Track the location of sperm / the sperm would decay quicker or slower based on location.

	LifeSpanDeviationLimit = 3  # type: int  # All sperm cells will be instantly killed if they live this many standard deviations above the average lifespan.

	_uniqueIdentifierSavingKey = "UniqueIdentifier"  # type: str
	_uniqueSeedSavingKey = "UniqueSeed"  # type: str

	def __init__ (self):
		"""
		An object for keeping track of sperm that has entered the cervix.
		"""

		super().__init__()

		self._uniqueIdentifier = None  # type: typing.Optional[uuid.UUID]
		self._uniqueSeed = None  # type: typing.Optional[int]

		self.DecayedCallback = None

		self.SourcePointer = SimPointer.SimPointer()

		self.Age = 0

		self.MotilePercentage = 0.8
		self.ViablePercentage = 0.8

		self.LifetimeDistribution = Distribution.NormalDistribution(4320, 960)

		self.SpermCount = 0

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

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler(self._uniqueIdentifierSavingKey, "_uniqueIdentifier", None, encoder = encodeUUID, decoder = decodeUUID, typeVerifier = uniqueIdentifierVerifier))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler(self._uniqueSeedSavingKey, "_uniqueSeed", None, updater = uniqueSeedUpdater, typeVerifier = uniqueSeedVerifier))

		self.RegisterSavableAttribute(Savable.StaticSavableAttributeHandler("SourcePointer", "SourcePointer"))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("SpermCount", "SpermCount", self.SpermCount, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Age", "Age", self.Age, requiredAttribute = True))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("MotilePercentage", "MotilePercentage", self.MotilePercentage))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("ViablePercentage", "ViablePercentage", self.ViablePercentage))

		self.RegisterSavableAttribute(Savable.StaticSavableAttributeHandler("LifetimeDistribution", "LifetimeDistribution"))

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
	def DecayedCallback (self) -> typing.Optional[typing.Callable]:
		"""
		Callback that will be triggered once when all sperm cells have decayed. This should be set by the sperm tracker when this sperm becomes active.
		The callback should take one argument, this sperm object.
		"""

		return self._decayedCallback

	@DecayedCallback.setter
	def DecayedCallback (self, value: typing.Optional[typing.Callable]) -> None:
		if not isinstance(value, typing.Callable) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "DecayedCallback", ("Callable", None))

		self._decayedCallback = value

	@property
	def Source (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that this sperm object came from. This can be None if the sim can't be found.
		"""

		return self.SourcePointer.GetSim()

	@property
	def SourceID (self) -> typing.Optional[int]:
		"""
		The id of the sim that this sperm object came from. This can be None if the sim can't be found.
		"""

		return self.SourcePointer.SimID

	@property
	def SourcePointer (self) -> SimPointer.SimPointer:
		"""
		An object that points out the sim that this sperm object came from.
		"""

		return self._sourcePointer

	@SourcePointer.setter
	def SourcePointer (self, value: SimPointer.SimPointer) -> None:
		if not isinstance(value, SimPointer.SimPointer):
			raise Exceptions.IncorrectTypeException(value, "SourcePointer", (SimPointer.SimPointer,))

		self._sourcePointer = value

	@property
	def SpermCount (self) -> int:
		"""
		The amount of sperm cells alive in this sperm object.
		"""

		return self._spermCount

	@SpermCount.setter
	def SpermCount (self, value: int) -> None:
		if not isinstance(value, (int,)):
			raise Exceptions.IncorrectTypeException(value, "SpermCount", (int,))

		self._spermCount = value

	@property
	def MaximumLifetime (self) -> typing.Union[float, int]:
		"""
		The maximum amount of time in reproductive minutes any sperm cell can be alive for. Any sperm cells left alive after this long will be
		instantly killed.
		"""

		return self.LifeSpanDeviationLimit * self.LifetimeDistribution.StandardDeviation + self.LifetimeDistribution.Mean

	@property
	def Lifetime (self) -> typing.Union[float, int]:
		"""
		The exact life time of this sperm object in reproductive minutes.
		"""

		return self.MaximumLifetime

	@property
	def Age (self) -> typing.Union[float, int]:
		"""
		The amount of time in reproductive minutes this sperm object has been active.
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
	def TimeRemaining (self) -> typing.Union[float, int]:
		"""
		The amount of time remaining in reproductive minutes until all sperm tracked by this object decays.
		"""

		return max(0, self.Lifetime - self.Age)

	@property
	def Decayed (self) -> bool:
		"""
		Whether this sperm object's age is at or has surpassed its lifetime.
		"""

		return self.Age >= self.Lifetime

	@property
	def MotilePercentage (self) -> float:
		"""
		The percentage of sperm that can reach or impregnate an ovum.
		"""

		return self._motilePercentage

	@MotilePercentage.setter
	def MotilePercentage (self, value: typing.Union[float, int]) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "MotilePercentage", (float, int))

		if value < 0 or value > 1:
			raise ValueError("MotilePercentage values must be between 0 and 1.")

		self._motilePercentage = value

	@property
	def MotileSpermCount (self) -> int:
		"""
		The number of sperm cells that can reach or impregnate an ovum.
		"""

		return int(self.SpermCount * self.MotilePercentage)

	@property
	def ViablePercentage (self) -> typing.Union[float, int]:
		"""
		The percentage of sperm cells that have DNA of high enough quality to produce a viable fetus.
		"""

		return self._viablePercentage

	@ViablePercentage.setter
	def ViablePercentage (self, value: typing.Union[float, int]) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "QualityPercentage", (float, int))

		if value < 0 or value > 1:
			raise ValueError("ViablePercentage values must be between 0 and 1.")

		self._viablePercentage = value

	@property
	def ViableSpermCount (self) -> int:
		"""
		The amount of sperm cells that have DNA of high enough quality to produce a viable fetus.
		"""

		return int(self.SpermCount * self.ViablePercentage)

	@property
	def LifetimeDistribution (self) -> Distribution.NormalDistribution:
		"""
		The normal distribution for the life span of a sperm cell. The distribution's values are measured in reproductive minutes.
		"""

		return self._lifetimeDistribution

	@LifetimeDistribution.setter
	def LifetimeDistribution (self, value: Distribution.NormalDistribution) -> None:
		if not isinstance(value, Distribution.NormalDistribution):
			raise Exceptions.IncorrectTypeException(value, "LifetimeDistribution", (Distribution.NormalDistribution,))

		self._lifetimeDistribution = value

	@classmethod
	def GetSpermGuide (cls, target: ReproductionShared.ReproductiveSystem) -> CycleGuides.SpermGuide:
		"""
		Get the ovum guide applicable to this sperm type.
		"""

		return CycleGuides.SpermGuide.GetGuide(target.GuideGroup)

	def SetSource (self, source: typing.Optional[sim_info.SimInfo]) -> None:
		"""
		Set the source of the sperm object.
		:param source: The sim being set as the source of the sperm object. This can be none if there is no specific source.
		:type source: typing.Optional[sim_info.SimInfo]
		"""

		if not isinstance(source, sim_info.SimInfo) and source is not None:
			raise Exceptions.IncorrectTypeException(source, "source", (sim_info.SimInfo, None))

		self.SourcePointer.ChangePointer(source)

	def Decaying (self, reproductiveMinutes: typing.Union[float, int]) -> int:
		"""
		Get the amount of sperm cells that will decay within this many reproductive minutes. This may return a slightly incorrect value if the
		age or the input are between two game tick.
		"""

		if not isinstance(reproductiveMinutes, (float, int)):
			raise Exceptions.IncorrectTypeException(reproductiveMinutes, "reproductiveMinutes", (float, int))

		if reproductiveMinutes < 0:
			raise ValueError("The parameter 'reproductiveMinutes' cannot be less than 0.")

		if self.SpermCount == 0:
			return 0

		if reproductiveMinutes == 0:
			return 0

		currentAge = self.Age  # type: float
		nextAge = self.Age + reproductiveMinutes  # type: float

		if nextAge >= self.Lifetime:
			return self.SpermCount

		currentPercentageRemaining = 1.0 - self.LifetimeDistribution.CumulativeDistribution(currentAge)  # type: typing.Union[float, int]
		nextPercentageRemaining = 1.0 - self.LifetimeDistribution.CumulativeDistribution(nextAge)  # type: typing.Union[float, int]
		percentageRemainingChange = nextPercentageRemaining - currentPercentageRemaining  # type: typing.Union[float, int]

		originalSpermCount = int(self.SpermCount / currentPercentageRemaining)  # type: int
		decayingSpermCount = int(originalSpermCount * percentageRemainingChange)  # type: int

		if decayingSpermCount < 0:
			Debug.Log("Calculated a decaying sperm count of less than zero (%s)." % decayingSpermCount, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

		return int(originalSpermCount * percentageRemainingChange)

	def DecayingTicks (self, ticks: int, reproductiveTimeMultiplier: typing.Union[float, int]) -> int:
		"""
		Get the amount of sperm cells that will decay within this many ticks.
		"""

		if not isinstance(ticks, (int,)):
			raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

		if not isinstance(reproductiveTimeMultiplier, (float, int)):
			raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

		if ticks < 0:
			raise ValueError("The parameter 'ticks' cannot be less than 0.")

		if reproductiveTimeMultiplier <= 0:
			raise ValueError("The parameter 'reproductiveTimeMultiplier' cannot be less than or equal to 0.")

		if self.SpermCount == 0:
			return 0

		if ticks == 0:
			return 0

		currentAgeTicks = ReproductionShared.ReproductiveMinutesToTicks(self.Age, reproductiveTimeMultiplier)  # type: int
		currentAge = ReproductionShared.TicksToReproductiveMinutes(currentAgeTicks, reproductiveTimeMultiplier)  # type: typing.Union[float, int]  # This is slightly faster than getting using the GetClosestPreciseReproductiveMinute function.
		nextAgeTicks = currentAgeTicks + ticks  # type: typing.Union[float, int]
		nextAge = ReproductionShared.TicksToReproductiveMinutes(nextAgeTicks, reproductiveTimeMultiplier)  # type: typing.Union[float, int]

		lifeTimeTick = ReproductionShared.ReproductiveMinutesToTicks(self.Lifetime, reproductiveTimeMultiplier)

		if nextAgeTicks >= lifeTimeTick:
			return self.SpermCount

		currentPercentageRemaining = 1.0 - self.LifetimeDistribution.CumulativeDistribution(currentAge)  # type: typing.Union[float, int]
		nextPercentageRemaining = 1.0 - self.LifetimeDistribution.CumulativeDistribution(nextAge)  # type: typing.Union[float, int]
		percentageRemainingChange = currentPercentageRemaining - nextPercentageRemaining  # type: typing.Union[float, int]

		originalSpermCount = int(self.SpermCount / currentPercentageRemaining)  # type: int
		decayingSpermCount = int(originalSpermCount * percentageRemainingChange)  # type: int

		if decayingSpermCount < 0:
			Debug.Log("Calculated a decaying sperm count of less than zero (%s)." % decayingSpermCount, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))

		return int(originalSpermCount * percentageRemainingChange)

	def GetDebugNotificationString (self) -> str:
		sourceName = ToolsSims.GetFullName(self.Source) if self.Source is not None else "Unknown"  # type: str
		spermCount = str(self.SpermCount / 1000000)  # type: str
		activeTime = str(round(self.Age, 4))  # type: str

		return "Source: %s, Count: %s million, Age: %s minutes" % (sourceName, spermCount, activeTime)

	def Generate (self, generationArguments: CycleEvents.SpermGeneratingArguments) -> None:
		"""
		Fill the sperm object's attributes with instruction from the input.
		:param generationArguments: Event arguments to instruct how to set the sperm's attributes.
		:type generationArguments: EventsSperm.SpermGeneratingArguments
		"""

		if not isinstance(generationArguments, CycleEvents.SpermGeneratingArguments):
			raise Exceptions.IncorrectTypeException(generationArguments, "generationArguments", (CycleEvents.SpermGeneratingArguments,))

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
		:param reproductiveTimeMultiplier: Divided by the amount of game time that the ticks count for to get the amount of time to simulate. All reproductive
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

	def _GenerateInternal (self, generationArguments: CycleEvents.SpermGeneratingArguments) -> None:
		self._uniqueIdentifier = generationArguments.GetUniqueIdentifier()
		self._uniqueSeed = generationArguments.GetUniqueSeed()

		self.SetSource(generationArguments.Source)

		self.SpermCount = generationArguments.GetSpermCount()

		self.LifetimeDistribution = generationArguments.GetLifetimeDistribution()

		self.MotilePercentage = generationArguments.GetMotilePercentage()
		self.ViablePercentage = generationArguments.GetViablePercentage()

	# noinspection PyUnusedLocal
	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: typing.Union[float, int]) -> None:
		ageTicks = ReproductionShared.ReproductiveMinutesToTicks(self.Age, reproductiveTimeMultiplier)  # type: typing.Union[float, int]
		decayTick = ReproductionShared.ReproductiveMinutesToTicks(self.Lifetime, reproductiveTimeMultiplier)  # type: typing.Union[float, int]

		decaying = False  # type: bool
		decayed = False  # type: bool

		if ageTicks < decayTick <= (ageTicks + ticks):
			decaying = True

		if decayTick <= (ageTicks + ticks):
			decayed = True

		if not decayed:
			decayingAmount = self.DecayingTicks(ticks, reproductiveTimeMultiplier)  # type: int
		else:
			decayingAmount = self.SpermCount  # type: int

		self.Age = ReproductionShared.TicksToReproductiveMinutes(ageTicks + ticks, reproductiveTimeMultiplier)
		self.SpermCount -= decayingAmount

		if decaying:
			if self.DecayedCallback is None:
				Debug.Log("Missing callback to be triggered on sperm decay.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			else:
				self.DecayedCallback(self)

	def _PlanSimulationInternal (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: typing.Union[float, int]) -> None:
		decayTick = ReproductionShared.ReproductiveMinutesToTicks(self.TimeRemaining, reproductiveTimeMultiplier)  # type: int

		if decayTick <= 0:
			decayTick = 1

		if simulation.RemainingTicks >= decayTick:
			simulation.Schedule.AddPoint(decayTick)

def GenerateGenericSperm (source: typing.Optional[sim_info.SimInfo] = None, spermGuide: typing.Optional[CycleGuides.SpermGuide] = None) -> Sperm:
	"""
	Generate a generic sperm object. This is best used to generate sperm for sims who can't normally produce sperm.
	:param source: The sim that this sperm is supposed to be from. Let this be none to have no specific sim be the source.
	:type source: typing.Optional[sim_info.SimInfo]
	:param spermGuide: The sperm guide used to generate the sperm object. We will use the default sperm guide if this is left as None.
	:type spermGuide: typing.Optional[GuidesSperm.SpermGuide]
	"""

	if not isinstance(source, sim_info.SimInfo) and source is not None:
		raise Exceptions.IncorrectTypeException(source, "source", (sim_info.SimInfo, None))

	if not isinstance(spermGuide, CycleGuides.SpermGuide) and spermGuide is not None:
		raise Exceptions.IncorrectTypeException(spermGuide, "spermGuide", (CycleGuides.SpermGuide, None))

	if spermGuide is None:
		spermGuide = CycleGuides.SpermGuide.GetDefaultGuide()

	generatingSperm = Sperm()  # type: Sperm
	generationSeed = random.randint(-1000000000, 1000000000)

	generationArguments = CycleEvents.SpermGeneratingArguments(generationSeed, generatingSperm, spermGuide)
	generationArguments.Source = source
	generatingSperm.Generate(generationArguments)

	return generatingSperm