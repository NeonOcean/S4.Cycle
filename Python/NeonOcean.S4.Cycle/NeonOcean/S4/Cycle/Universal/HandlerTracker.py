from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, ReproductionShared, This
from NeonOcean.S4.Cycle.Handlers import Base as HandlersBase, Types as HandlersTypes
from NeonOcean.S4.Cycle.Universal import Shared as UniversalShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Savable, Types, Version
from sims import sim_info

class HandlerTracker(ReproductionShared.TrackerBase):
	_handlersSavingKey = "ActiveHandlers"

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
			ReproductionShared.SimulationPhase(-15, self._HandlerSimulationPhase)
		)

	def _LoadFromDictionaryInternal (self, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		superOperationSuccessful = super()._LoadFromDictionaryInternal(data, lastVersion)  # type: bool

		self._AddMissingHandlers()

		operationSuccessful = True  # type: bool
		operationInformation = self.SavableOperationInformation  # type: str

		handlersSavingKey = self._handlersSavingKey  # type: str
		handlersDataSavingKey = "Data"  # type: str
		handlersTypeSavingKey = "Type"  # type: str

		try:
			handlersListData = data[handlersSavingKey]  # type: typing.Optional[list]
		except KeyError:
			return True

		if not isinstance(handlersListData, list):
			raise Exceptions.IncorrectTypeException(handlersListData, "data[%s]" % self._handlersSavingKey, (list,))

		for activeHandler in self._activeHandlers:  # type: HandlersBase.HandlerBase
			if not isinstance(activeHandler, HandlersBase.HandlerBase):
				Debug.Log("Found an object in the handlers list that was not a handler.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":HandlerSavingOperationNotHandlerType")
				continue

			try:
				for handlerDataIndex in range(len(handlersListData)):  # type: int
					handlerContainerData = handlersListData[handlerDataIndex]  # type: dict

					handlerTypeIdentifier = handlerContainerData.get(handlersTypeSavingKey, None)  # type: typing.Optional[str]

					if handlerTypeIdentifier is None or handlerTypeIdentifier != activeHandler.TypeIdentifier:
						continue

					if not isinstance(handlerContainerData, dict):
						raise Exceptions.IncorrectTypeException(handlerContainerData, "data[%s][%s]" % (handlersSavingKey, handlerDataIndex), (dict,))

					handlerData = handlerContainerData[handlersDataSavingKey]  # type: typing.Optional[dict]

					if not isinstance(handlerData, dict):
						raise Exceptions.IncorrectTypeException(handlerData, "data[%s][%s][%s]" % (handlersSavingKey, handlerDataIndex, handlersDataSavingKey), (dict,))

					if not activeHandler.LoadFromDictionary(handlerData, lastVersion = lastVersion):
						operationSuccessful = False

					break
			except:
				Debug.Log("Load operation in a savable object failed to load the handler data of a handler with the identifier '%s'.\n%s" % (activeHandler.TypeIdentifier, operationInformation), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				operationSuccessful = False

		if not operationSuccessful:
			return False

		return superOperationSuccessful

	def _SaveToDictionaryInternal (self) -> typing.Tuple[bool, dict]:
		superOperationSuccessful, data = super()._SaveToDictionaryInternal()  # type: bool, dict

		operationSuccessful = True  # type: bool
		operationInformation = self.SavableOperationInformation  # type: str

		handlersSavingKey = self._handlersSavingKey  # type: str
		handlersDataSavingKey = "Data"  # type: str
		handlersTypeSavingKey = "Type"  # type: str

		handlersListData = list()  # type: typing.List[typing.Optional[dict]]

		for activeHandler in self._activeHandlers:  # type: HandlersBase.HandlerBase
			if not isinstance(activeHandler, HandlersBase.HandlerBase):
				Debug.Log("Found an object in the handlers list that was not a handler.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":HandlerSavingOperationNotHandlerType")
				continue

			try:
				handlerContainerData = dict()  # type: dict
				entryOperationSuccessful, handlerData = activeHandler.SaveToDictionary()  # type: bool, dict

				if not entryOperationSuccessful:
					operationSuccessful = False

				handlerTypeIdentifier = activeHandler.TypeIdentifier  # type: str

				if not isinstance(handlerTypeIdentifier, str):
					raise Exceptions.IncorrectReturnTypeException(handlerTypeIdentifier, "typeFetcher", (str,))

				handlerContainerData[handlersTypeSavingKey] = handlerTypeIdentifier
				handlerContainerData[handlersDataSavingKey] = handlerData

				handlersListData.append(handlerContainerData)
			except:
				Debug.Log("Save operation in a savable object failed to save the handler data of a handler with the identifier '%s'.\n%s" % (activeHandler.TypeIdentifier, operationInformation), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				operationSuccessful = False

			data[handlersSavingKey] = handlersListData

		if not operationSuccessful:
			return False, data

		return superOperationSuccessful, data

	def _ResetInternal (self) -> bool:
		superOperationSuccessful = super()._ResetInternal()  # type: bool

		operationInformation = self.SavableOperationInformation  # type: str

		for activeHandler in self._activeHandlers:  # type: HandlersBase.HandlerBase
			if not isinstance(activeHandler, HandlersBase.HandlerBase):
				Debug.Log("Found an object in the handlers list that was not a handler.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":TrackerSavingOperationNotTrackerType")
				continue

			activeHandler.Reset()

		return superOperationSuccessful
