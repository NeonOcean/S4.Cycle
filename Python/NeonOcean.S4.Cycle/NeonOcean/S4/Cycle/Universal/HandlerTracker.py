from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, ReproductionShared, This
from NeonOcean.S4.Cycle.Handlers import Base as HandlersBase, Types as HandlersTypes
from NeonOcean.S4.Cycle.Universal import Shared as UniversalShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Types
from sims import sim_info

class HandlerTracker(ReproductionShared.TrackerBase):
	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self.HandlerAddedEvent = Events.EventHandler()
		self.HandlerRemovedEvent = Events.EventHandler()

		self._activeHandlers = list()  # type: typing.List[HandlersBase.HandlerBase]

		def handlerSaveSkipTest (testingHandler: HandlersBase.HandlerBase) -> bool:
			if not isinstance(testingHandler, HandlersBase.HandlerBase):
				return True

			return testingHandler.ShouldSave

		self.RegisterSavableAttribute(Savable.ListedSavableAttributeHandler(
			"ActiveHandlers",
			"_activeHandlers",
			lambda typeIdentifier: HandlersTypes.GetHandlerType(typeIdentifier)(self.TrackingSystem),
			lambda: list(),
			requiredSuccess = False,
			skipEntrySaveTest = handlerSaveSkipTest,
			multiType = True,
			typeFetcher = lambda attributeValue: attributeValue.TypeIdentifier,
		))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		return UniversalShared.HandlerTrackerIdentifier

	@property
	def HandlerAddedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a menstruation handler buff was added.
		The event arguments parameter should be a 'HandlerAddedArguments' object.
		"""

		return self._handlerAddedEvent

	@HandlerAddedEvent.setter
	def HandlerAddedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "HandlerAddedEvent", (Events.EventHandler,))

		self._handlerAddedEvent = value

	@property
	def HandlerRemovedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a menstruation handler buff was removed.
		The event arguments parameter should be a 'HandlerRemovedArguments' object.
		"""

		return self._handlerRemovedEvent

	@HandlerRemovedEvent.setter
	def HandlerRemovedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "HandlerRemovedEvent", (Events.EventHandler,))

		self._handlerRemovedEvent = value

	@property
	def ActiveHandlers (self) -> typing.List[HandlersBase.HandlerBase]:
		"""
		All handlers active in this handler tracker.
		"""

		return list(self._activeHandlers)

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return True

	def GetHandler (self, handlerTypeIdentifier: str) -> typing.Optional[HandlersBase.HandlerBase]:
		"""
		Get the active handler with this handler type identifier. Returns none if no handler with this type identifier can be found.
		"""

		if not isinstance(handlerTypeIdentifier, str):
			raise Exceptions.IncorrectTypeException(handlerTypeIdentifier, "handlerTypeIdentifier", (str,))

		for activeHandler in self._activeHandlers:  # type: HandlersBase.HandlerBase
			if activeHandler.TypeIdentifier == handlerTypeIdentifier:
				return activeHandler

		return None

	def HasHandler (self, handlerTypeIdentifier: str) -> bool:
		"""
		Whether or not this tracker has an handler of this type.
		"""

		return self.GetHandler(handlerTypeIdentifier) is not None

	def _Setup (self) -> None:
		super()._Setup()

		self._ClearDuplicateHandlers()
		self._AddMissingHandlers()

	def _AddHandler (self, addingHandler: HandlersBase.HandlerBase) -> None:
		if self.HasHandler(addingHandler.TypeIdentifier):
			return

		# noinspection PyProtectedMember
		addingHandler._OnAdding()

		self._activeHandlers.append(addingHandler)

		# noinspection PyProtectedMember
		addingHandler._OnAdded()

		self._NotifyHandlerAdded(addingHandler)

	def _RemoveHandler (self, removingHandler: HandlersBase.HandlerBase) -> None:
		# noinspection PyProtectedMember
		removingHandler._OnRemoving()

		try:
			self._activeHandlers.remove(removingHandler)
		except ValueError:
			pass

		# noinspection PyProtectedMember
		removingHandler._OnRemoved()

		self._NotifyHandlerRemoved(removingHandler)

	def _NotifyHandlerAdded (self, addedHandler: HandlersBase.HandlerBase) -> None:
		eventArguments = CycleEvents.HandlerAddedArguments(addedHandler)  # type: CycleEvents.HandlerAddedArguments

		for handlerAddedCallback in self.HandlerAddedEvent:
			try:
				handlerAddedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call handler added callback '" + Types.GetFullName(handlerAddedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = handlerAddedCallback)

	def _NotifyHandlerRemoved (self, removedHandler: HandlersBase.HandlerBase) -> None:
		eventArguments = CycleEvents.HandlerRemovedArguments(removedHandler)  # type: CycleEvents.HandlerRemovedArguments

		for handlerRemovedCallback in self.HandlerRemovedEvent:
			try:
				handlerRemovedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call handler removed callback '" + Types.GetFullName(handlerRemovedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = handlerRemovedCallback)

	def _AddMissingHandlers (self) -> None:
		activeTypeIdentifiers = set(handler.TypeIdentifier for handler in self.ActiveHandlers)  # type: typing.Set[str]
		allTypeIdentifiers = HandlersTypes.GetAllHandlerTypeIdentifiers()  # type: typing.Set[str]

		for typeIdentifier in allTypeIdentifiers:  # type: str
			if not typeIdentifier in activeTypeIdentifiers:
				addingHandlerType = HandlersTypes.GetHandlerType(typeIdentifier)

				try:
					addingHandler = addingHandlerType(self.TrackingSystem)  # type: HandlersBase.HandlerBase
				except:
					Debug.Log("Failed to create instance of the handler type '" + Types.GetFullName(addingHandlerType) + "'.\n" + self.TrackingSystem.DebugInformation,
							  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + " | Creating_Handler", lockReference = addingHandlerType)

					continue

				self._AddHandler(addingHandler)

	def _ClearDuplicateHandlers (self) -> None:
		existingHandlerTypes = set()  # type: typing.Set[str]

		activeHandlerIndex = 0
		while activeHandlerIndex < len(self._activeHandlers):
			activeHandler = self._activeHandlers[activeHandlerIndex]

			if activeHandler.TypeIdentifier in existingHandlerTypes:
				self._activeHandlers.pop(activeHandlerIndex)
				continue

			existingHandlerTypes.add(activeHandler.TypeIdentifier)

			activeHandlerIndex += 1

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return UniversalShared.GetHandlerTrackerReproductiveTimeMultiplier()

	# noinspection PyUnusedLocal
	def _HandlerSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		for activeHandler in self.ActiveHandlers:
			activeHandler.Simulate(simulation, ticks, reproductiveTimeMultiplier)

	def _PlanSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PlanSimulation(simulation)

		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		for activeHandler in self.ActiveHandlers:
			activeHandler.PlanSimulation(simulation, reproductiveTimeMultiplier)

	def _PrepareForSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PrepareForSimulation(simulation)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(0, self._HandlerSimulationPhase)
		)
