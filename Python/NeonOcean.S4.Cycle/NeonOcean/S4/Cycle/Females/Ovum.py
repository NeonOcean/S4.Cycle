from __future__ import annotations

import random
import typing
import uuid

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared, Settings, This
from NeonOcean.S4.Cycle.Tools import SimPointer
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Events, Exceptions, Python, Sims as ToolsSims, Savable
from sims import sim_info

class Ovum(Savable.SavableExtension):
	def __init__ (self):
		super().__init__()

		self._uniqueIdentifier = None  # type: typing.Optional[uuid.UUID]
		self._uniqueSeed = None  # type: typing.Optional[int]

		self.DecayedCallback = None
		self.AttemptImplantationCallback = None

		self.SourcePointer = SimPointer.SimPointer()

		self.NormalLifetime = 1080
		self.ImplantationTime = 11520
		self.Age = 0

		self.Viable = True

		self.FertilizationSeed = random.randint(-1000000000, 1000000000)
		self.Fertilized = False
		self.FertilizerPointer = SimPointer.SimPointer()

		encodeUUID = lambda value: str(value) if value is not None else None
		decodeUUID = lambda valueString: uuid.UUID(valueString) if valueString is not None else None

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Identifier", "_identifier", None, requiredAttribute = True, encoder = encodeUUID, decoder = decodeUUID))
		self.RegisterSavableAttribute(Savable.StaticSavableAttributeHandler("SourcePointer", "SourcePointer", requiredSuccess = False))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("NormalLifetime", "NormalLifetime", self.NormalLifetime))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("ImplantationTime", "ImplantationTime", self.ImplantationTime))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Age", "Age", self.Age))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Viable", "Viable", self.Viable))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FertilizationSeed", "FertilizationSeed", self.FertilizationSeed))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Fertilized", "Fertilized", self.Fertilized))
		self.RegisterSavableAttribute(Savable.StaticSavableAttributeHandler("FertilizerPointer", "FertilizerPointer", requiredSuccess = False))

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
		A callback that will be triggered once this ovum has decayed. This should be set by the ovum tracker when this ovum becomes active.
		The callback should take one argument, this ovum object.
		"""

		return self._decayedCallback

	@DecayedCallback.setter
	def DecayedCallback (self, value: typing.Optional[typing.Callable]) -> None:
		if not isinstance(value, typing.Callable) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "DecayedCallback", ("Callable", None))

		self._decayedCallback = value

	@property
	def AttemptImplantationCallback (self) -> typing.Optional[typing.Callable]:
		"""
		A callback that will be triggered when this ovum tries to implant. This should be set by the ovum tracker when this ovum becomes active.
		The callback should take one argument, this ovum object. The ovum should be removed from the system when this is called.
		"""

		return self._attemptImplantationCallback

	@AttemptImplantationCallback.setter
	def AttemptImplantationCallback (self, value: typing.Optional[typing.Callable]) -> None:
		if not isinstance(value, typing.Callable) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "AttemptImplantationCallback", ("Callable", None))

		self._attemptImplantationCallback = value

	@property
	def Source (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that this ovum object came from. This can be None if the sim can't be found.
		"""

		return self.SourcePointer.GetSim()

	@property
	def SourceID (self) -> typing.Optional[int]:
		"""
		The id of the sim that this ovum object came from. This can be None.
		"""

		return self.SourcePointer.SimID

	@property
	def SourcePointer (self) -> SimPointer.SimPointer:
		"""
		An object that points out the sim that this ovum object came from.
		"""

		return self._sourcePointer

	@SourcePointer.setter
	def SourcePointer (self, value: SimPointer.SimPointer) -> None:
		if not isinstance(value, SimPointer.SimPointer):
			raise Exceptions.IncorrectTypeException(value, "SourcePointer", (SimPointer.SimPointer,))

		self._sourcePointer = value

	@property
	def Decayed (self) -> bool:
		"""
		Whether or not this ovum is still alive, If this is false this object can be removed.
		"""

		return self.Age > self.Lifetime

	@property
	def Lifetime (self) -> float:
		"""
		The life time of this ovum in reproductive minutes. This may change if the ovum becomes fertilized.
		"""

		if not self.Fertilized:
			return self.NormalLifetime
		else:
			return self.ImplantationTime

	@property
	def NormalLifetime (self) -> float:
		"""
		The life time of this ovum, as long as its not fertilized, in reproductive minutes.
		"""

		return self._normalLifetime

	@NormalLifetime.setter
	def NormalLifetime (self, value: float) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Lifetime", (float, int))

		if value < 0:
			raise ValueError("Lifetime values must be greater than or equal to 0.")

		self._normalLifetime = value

	@property
	def ImplantationTime (self) -> float:
		"""
		The time in reproductive minutes from the object's creation that the ovum will implant, if it can.
		"""

		return self._implantationTime

	@ImplantationTime.setter
	def ImplantationTime (self, value: float) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "ImplantationTime", (float, int))

		if value < 0:
			raise ValueError("ImplantationTime values must be greater than or equal to 0.")

		self._implantationTime = value

	@property
	def Age (self) -> float:
		"""
		The amount of time in reproductive minutes that this ovum has been active.
		"""

		return self._age

	@Age.setter
	def Age (self, value: float) -> None:
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
	def TimeRemaining (self) -> float:
		"""
		The amount of time remaining for this ovum in reproductive minutes.
		"""

		return max(0.0, self.Lifetime - self.Age)

	@property
	def TimeUntilImplantation (self) -> float:
		"""
		The amount of time remaining until this ovum attempts to implant.
		"""

		return max(0.0, self.ImplantationTime - self.Age)

	@property
	def Viable (self) -> bool:
		"""
		Whether or not this ovum can ever produce a viable fetus. A pregnancy should not start from this ovum if this is false.
		"""

		return self._viable

	@Viable.setter
	def Viable (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Viable", (bool,))

		self._viable = value

	@property
	def FertilizationSeed (self) -> int:
		"""
		A seed to be used in the generation of random numbers to determine when and which sperm should fertilize this ovum.
		"""

		return self._fertilizationSeed

	@FertilizationSeed.setter
	def FertilizationSeed (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "FertilizationSeed", (int,))

		self._fertilizationSeed = value

	@property
	def Fertilized (self) -> bool:
		"""
		Whether or not this ovum has been fertilized.
		"""

		return self._fertilized

	@Fertilized.setter
	def Fertilized (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Fertilized", (bool,))

		self._fertilized = value

	@property
	def Fertilizer (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		The sim that this ovum object came from. This can be None if the sim can't be found.
		"""

		return self.FertilizerPointer.GetSim()

	@property
	def FertilizerID (self) -> typing.Optional[int]:
		"""
		The id of the sim that this ovum has been fertilized by. This can be None.
		"""

		return self.FertilizerPointer.SimID

	@property
	def FertilizerPointer (self) -> SimPointer.SimPointer:
		"""
		An object that points out the sim that this ovum has been fertilized by.
		"""

		return self._fertilizerPointer

	@FertilizerPointer.setter
	def FertilizerPointer (self, value: SimPointer.SimPointer) -> None:
		if not isinstance(value, SimPointer.SimPointer):
			raise Exceptions.IncorrectTypeException(value, "FertilizerPointer", (SimPointer.SimPointer,))

		self._fertilizerPointer = value

	@classmethod
	def GetOvumGuide (cls, target: ReproductionShared.ReproductiveSystem) -> CycleGuides.OvumGuide:
		"""
		Get the ovum guide applicable to this ovum type.
		"""

		return CycleGuides.OvumGuide.GetGuide(target.GuideGroup)

	def SetSource (self, source: typing.Optional[sim_info.SimInfo]) -> None:
		"""
		Set the source of the ovum object.
		:param source: The sim being set as the source of the ovum object. This can be none if there is no specific source.
		:type source: sim_info.SimInfo
		"""

		if not isinstance(source, sim_info.SimInfo) and source is not None:
			raise Exceptions.IncorrectTypeException(source, "source", (sim_info.SimInfo, None))

		self.SourcePointer.ChangePointer(source)

	def Fertilize (self, fertilizer: typing.Optional[sim_info.SimInfo], fertilizationViability: bool = True) -> None:
		"""
		Fertilize this ovum.
		:param fertilizer: The sim that has fertilized this ovum, the ovum can be fertilized by no specific sim by letting this be None.
		:type fertilizer: sim_info.SimInfo | None
		:param fertilizationViability: Whether or not the ovum will become un-viable as a result of this fertilization. This shouldn't allow the ovum
		to become viable if it isn't already.
		:type fertilizationViability: bool
		"""

		if not isinstance(fertilizer, sim_info.SimInfo) and fertilizer is not None:
			raise Exceptions.IncorrectTypeException(fertilizer, "fertilizer", (sim_info.SimInfo, None))

		if not isinstance(fertilizationViability, bool):
			raise Exceptions.IncorrectTypeException(fertilizationViability, "fertilizationViability", (bool,))

		self.Fertilized = True
		self.FertilizerPointer.ChangePointer(fertilizer)

		if not fertilizationViability:
			self.Viable = False

	def FertilizeWithEvent (self, fertilizingArguments: CycleEvents.OvumFertilizingArguments) -> None:
		"""
		Fertilize this ovum with fertilizing event arguments.
		:param fertilizingArguments: The event arguments to the event that was run to determine fertilization values, such as the source and viability.
		:type fertilizingArguments: EventsOva.OvumFertilizingArguments
		"""

		if not isinstance(fertilizingArguments, CycleEvents.OvumFertilizingArguments):
			raise Exceptions.IncorrectTypeException(fertilizingArguments, "fertilizingArguments", (CycleEvents.OvumFertilizingArguments,))

		self.Fertilize(fertilizingArguments.GetFertilizer(), fertilizationViability = fertilizingArguments.GetFertilizationViability())

	def GetDebugNotificationString (self) -> str:
		source = self.Source  # type: typing.Optional[sim_info.SimInfo]
		sourceName = ToolsSims.GetFullName(source) if source is not None else "Unknown"  # type: str
		activeTime = str(round(self.Age, 4))  # type: str
		fertilized = self.Fertilized  # type: bool
		fertilizer = self.Fertilizer  # type: typing.Optional[sim_info.SimInfo]
		fertilizerName = ToolsSims.GetFullName(fertilizer) if fertilizer is not None else "Unknown"  # type: str
		viable = str(self.Viable)  # type: str

		debugString = "Source: %s, Age: %s minutes, Viable: %s" % (sourceName, activeTime, viable)

		if fertilized:
			debugString += ", Fertilizer: %s" % fertilizerName

		return debugString

	def Generate (self, generationArguments: CycleEvents.OvumGeneratingArguments) -> None:
		"""
		Fill the ovum object's attributes with instruction from the input.
		:param generationArguments: Event arguments to instruct how to set the ovum's attributes.
		:type generationArguments: EventsOva.OvumGeneratingArguments
		"""

		if not isinstance(generationArguments, CycleEvents.OvumGeneratingArguments):
			raise Exceptions.IncorrectTypeException(generationArguments, "generationArguments", (CycleEvents.OvumGeneratingArguments,))

		generationArguments.PreGenerationEvent.Invoke(generationArguments, Events.EventArguments())
		self._GenerateInternal(generationArguments)
		generationArguments.PostGenerationEvent.Invoke(generationArguments, Events.EventArguments())

	def Simulate (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		"""
		Simulate this many ticks in this object, invoking any events that occurred and adding to the progress value.
		:param simulation: The simulation object that is guiding this simulation.
		:type simulation: ReproductionShared.Simulation
		:param ticks: The number of ticks to simulate.
		:type ticks: int
		:param reproductiveTimeMultiplier: Divided by the amount of game time that the ticks count for to get the amount of time to simulate.  All reproductive
		simulations work in real-life time.
		:type reproductiveTimeMultiplier: float
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

	def PlanSimulation (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: float) -> None:
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

	def _GenerateInternal (self, generationArguments: CycleEvents.OvumGeneratingArguments) -> None:
		self._uniqueIdentifier = generationArguments.GetUniqueIdentifier()
		self._uniqueSeed = generationArguments.GetUniqueSeed()

		self.SetSource(generationArguments.GetSource())
		self.FertilizationSeed = generationArguments.GetFertilizationSeed()

		self.NormalLifetime = generationArguments.GetNormalLifetime()
		self.ImplantationTime = generationArguments.GetImplantationTime()

		self.Viable = generationArguments.GetViability()

	# noinspection PyUnusedLocal
	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		simulatingMinutes = ReproductionShared.TicksToReproductiveMinutes(ticks, reproductiveTimeMultiplier)  # type: float
		quickMode = Settings.QuickMode.Get()  # type: bool

		if not self.Fertilized:
			decaying = False  # type: bool

			if self.Age < self.TimeRemaining <= (self.Age + simulatingMinutes):
				decaying = True

			if decaying: #TODO set age first?
				if self.DecayedCallback is None:
					Debug.Log("Missing callback to be triggered on ovum decay.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
				else:
					self.DecayedCallback(self)
		else:
			if quickMode:
				implanting = True  # type: bool
				self.Age = self.ImplantationTime
			else:
				implanting = False  # type: bool

				if self.Age < self.TimeUntilImplantation <= (self.Age + simulatingMinutes):
					implanting = True

			if implanting:
				if self.AttemptImplantationCallback is None:
					Debug.Log("Missing callback to be triggered on ovum implantation attempt.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
				else:
					self.AttemptImplantationCallback(self)

		self.Age += simulatingMinutes

	def _PlanSimulationInternal (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: float) -> None:
		quickMode = Settings.QuickMode.Get()  # type: bool

		if not self.Fertilized:
			decayTick = ReproductionShared.ReproductiveMinutesToTicks(self.TimeRemaining, reproductiveTimeMultiplier)  # type: int

			if simulation.RemainingTicks >= decayTick:
				simulation.Schedule.AddPoint(decayTick)
		else:
			if quickMode:
				if simulation.RemainingTicks >= 1:
					simulation.Schedule.AddPoint(1)
			else:
				implantationTick = ReproductionShared.ReproductiveMinutesToTicks(self.TimeUntilImplantation, reproductiveTimeMultiplier)  # type: int

				if simulation.RemainingTicks >= implantationTick:
					simulation.Schedule.AddPoint(implantationTick)

def GenerateGenericOvum (source: typing.Optional[sim_info.SimInfo] = None, ovumGuide: typing.Optional[CycleGuides.OvumGuide] = None) -> Ovum:
	"""
	Generate a generic ovum object. This is best used to generate an ovum for sims who can't normally produce an ovum.
	:param source: The sim that this ovum is supposed to be from. Let this be none to have no specific sim be the source.
	:type source: typing.Optional[sim_info.SimInfo]
	:param ovumGuide: The ovum guide used to generate the ovum object. We will use the default ovum guide if this is left as None.
	:type ovumGuide: typing.Optional[GuidesOva.OvumGuide]
	"""

	if not isinstance(source, sim_info.SimInfo) and source is not None:
		raise Exceptions.IncorrectTypeException(source, "source", (sim_info.SimInfo, None))

	if not isinstance(ovumGuide, CycleGuides.OvumGuide) and ovumGuide is not None:
		raise Exceptions.IncorrectTypeException(ovumGuide, "ovumGuide", (CycleGuides.OvumGuide, None))

	if ovumGuide is None:
		ovumGuide = CycleGuides.OvumGuide.GetDefaultGuide()

	generatingOvum = Ovum()  # type: Ovum
	generationSeed = random.randint(-1000000000, 1000000000)

	generationArguments = CycleEvents.OvumGeneratingArguments(generationSeed, generatingOvum, ovumGuide)
	generationArguments.Source = source
	generatingOvum.Generate(generationArguments)

	return generatingOvum
