from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, ReproductionShared, This
from NeonOcean.S4.Cycle.Effects import Base as EffectsBase, Types as EffectsTypes
from NeonOcean.S4.Cycle.Universal import Shared as UniversalShared
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Classes, Events, Exceptions, Python, Types, Version
from sims import sim_info

class EffectTracker(ReproductionShared.TrackerBase):
	_effectsSavingKey = "ActiveEffects"

	def __init__ (self, trackingSystem: ReproductionShared.ReproductiveSystem):
		super().__init__(trackingSystem)

		self.EffectAddedEvent = Events.EventHandler()
		self.EffectRemovedEvent = Events.EventHandler()

		self._activeEffects = list()  # type: typing.List[EffectsBase.EffectBase]

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This tracker type's identifier, this is used to save and load the tracker. Loading will not be possible unless the tracker type is registered
		through the function in the reproductive trackers module.
		"""

		return UniversalShared.EffectTrackerIdentifier

	@property
	def EffectAddedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a menstruation effect buff was added.
		The event arguments parameter should be a 'EffectAddedArguments' object.
		"""

		return self._effectAddedEvent

	@EffectAddedEvent.setter
	def EffectAddedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "EffectAddedEvent", (Events.EventHandler,))

		self._effectAddedEvent = value

	@property
	def EffectRemovedEvent (self) -> Events.EventHandler:
		"""
		An event that will be triggered when a menstruation effect buff was removed.
		The event arguments parameter should be a 'EffectRemovedArguments' object.
		"""

		return self._effectRemovedEvent

	@EffectRemovedEvent.setter
	def EffectRemovedEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "EffectRemovedEvent", (Events.EventHandler,))

		self._effectRemovedEvent = value

	@property
	def ActiveEffects (self) -> typing.List[EffectsBase.EffectBase]:
		"""
		All effects active in this effect tracker.
		"""

		return list(self._activeEffects)

	@classmethod
	def ShouldHave (cls, targetSimInfo: sim_info.SimInfo, targetSystem: ReproductionShared.ReproductiveSystem) -> bool:
		"""
		Get whether or not the target should have this tracker.
		"""

		return True

	def GetEffect (self, effectTypeIdentifier: str) -> typing.Optional[EffectsBase.EffectBase]:
		"""
		Get the active effect with this effect type identifier. Returns none if no effect with this type identifier can be found.
		"""

		if not isinstance(effectTypeIdentifier, str):
			raise Exceptions.IncorrectTypeException(effectTypeIdentifier, "effectTypeIdentifier", (str,))

		for activeEffect in self._activeEffects:  # type: EffectsBase.EffectBase
			if activeEffect.TypeIdentifier == effectTypeIdentifier:
				return activeEffect

		return None

	def HasEffect (self, effectTypeIdentifier: str) -> bool:
		"""
		Whether or not this tracker has an effect of this type.
		"""

		return self.GetEffect(effectTypeIdentifier) is not None

	def _Setup (self) -> None:
		super()._Setup()

		self._ClearDuplicateEffects()
		self._AddMissingEffects()

	def _AddEffect (self, addingEffect: EffectsBase.EffectBase) -> None:
		if self.HasEffect(addingEffect.TypeIdentifier):
			return

		# noinspection PyProtectedMember
		addingEffect._OnAdding()

		self._activeEffects.append(addingEffect)

		# noinspection PyProtectedMember
		addingEffect._OnAdded()

		self._NotifyEffectAdded(addingEffect)

	def _RemoveEffect (self, removingEffect: EffectsBase.EffectBase) -> None:
		# noinspection PyProtectedMember
		removingEffect._OnRemoving()

		try:
			self._activeEffects.remove(removingEffect)
		except ValueError:
			pass

		# noinspection PyProtectedMember
		removingEffect._OnRemoved()

		self._NotifyEffectRemoved(removingEffect)

	def _NotifyEffectAdded (self, addedEffect: EffectsBase.EffectBase) -> None:
		eventArguments = CycleEvents.EffectAddedArguments(addedEffect)  # type: CycleEvents.EffectAddedArguments

		for effectAddedCallback in self.EffectAddedEvent:
			try:
				effectAddedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call effect added callback '" + Types.GetFullName(effectAddedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = effectAddedCallback)

	def _NotifyEffectRemoved (self, removedEffect: EffectsBase.EffectBase) -> None:
		eventArguments = CycleEvents.EffectRemovedArguments(removedEffect)  # type: CycleEvents.EffectRemovedArguments

		for effectRemovedCallback in self.EffectRemovedEvent:
			try:
				effectRemovedCallback(self, eventArguments)
			except:
				Debug.Log("Failed to call effect removed callback '" + Types.GetFullName(effectRemovedCallback) + "'.\n" + self.TrackingSystem.DebugInformation,
						  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = effectRemovedCallback)

	def _AddMissingEffects (self) -> None:
		activeTypeIdentifiers = set(effect.TypeIdentifier for effect in self.ActiveEffects)  # type: typing.Set[str]
		allTypeIdentifiers = EffectsTypes.GetAllEffectTypeIdentifiers()  # type: typing.Set[str]

		for typeIdentifier in allTypeIdentifiers:  # type: str
			if not typeIdentifier in activeTypeIdentifiers:
				addingEffectType = EffectsTypes.GetEffectType(typeIdentifier)

				try:
					addingEffect = addingEffectType(self.TrackingSystem)  # type: EffectsBase.EffectBase
				except:
					Debug.Log("Failed to create instance of the effect type '" + Types.GetFullName(addingEffectType) + "'.\n" + self.TrackingSystem.DebugInformation,
							  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":CreatingEffect", lockReference = addingEffectType)

					continue

				self._AddEffect(addingEffect)

	def _ClearDuplicateEffects (self) -> None:
		existingEffectTypes = set()  # type: typing.Set[str]

		activeEffectIndex = 0
		while activeEffectIndex < len(self._activeEffects):
			activeEffect = self._activeEffects[activeEffectIndex]

			if activeEffect.TypeIdentifier in existingEffectTypes:
				self._activeEffects.pop(activeEffectIndex)
				continue

			existingEffectTypes.add(activeEffect.TypeIdentifier)

			activeEffectIndex += 1

	# noinspection PyUnusedLocal
	def _EffectSimulationPhase (self, simulation: ReproductionShared.Simulation, ticks: int) -> None:
		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		for activeEffect in self.ActiveEffects:
			activeEffect.Simulate(simulation, ticks, reproductiveTimeMultiplier)

	def _PlanSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PlanSimulation(simulation)

		reproductiveTimeMultiplier = self.ReproductiveTimeMultiplier  # type: typing.Union[float, int]

		for activeEffect in self.ActiveEffects:
			activeEffect.PlanSimulation(simulation, reproductiveTimeMultiplier)

	def _PrepareForSimulation (self, simulation: ReproductionShared.Simulation) -> None:
		super()._PrepareForSimulation(simulation)

		simulation.RegisterPhase(
			ReproductionShared.SimulationPhase(-15, self._EffectSimulationPhase)
		)

	def _GetNextReproductiveTimeMultiplier (self) -> float:
		return UniversalShared.GetEffectTrackerReproductiveTimeMultiplier()

	def _LoadFromDictionaryInternal (self, data: dict, lastVersion: typing.Optional[Version.Version]) -> bool:
		superOperationSuccessful = super()._LoadFromDictionaryInternal(data, lastVersion)  # type: bool

		self._AddMissingEffects()

		operationSuccessful = True  # type: bool
		operationInformation = self.SavableOperationInformation  # type: str

		effectsSavingKey = self._effectsSavingKey  # type: str
		effectsDataSavingKey = "Data"  # type: str
		effectsTypeSavingKey = "Type"  # type: str

		try:
			effectsListData = data[effectsSavingKey]  # type: typing.Optional[list]
		except KeyError:
			return True

		if not isinstance(effectsListData, list):
			raise Exceptions.IncorrectTypeException(effectsListData, "data[%s]" % self._effectsSavingKey, (list,))

		for activeEffect in self._activeEffects:  # type: EffectsBase.EffectBase
			if not isinstance(activeEffect, EffectsBase.EffectBase):
				Debug.Log("Found an object in the effects list that was not an effect.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":EffectSavingOperationNotEffectType")
				continue

			try:
				for effectDataIndex in range(len(effectsListData)):  # type: int
					effectContainerData = effectsListData[effectDataIndex]  # type: dict

					effectTypeIdentifier = effectContainerData.get(effectsTypeSavingKey, None)  # type: typing.Optional[str]

					if effectTypeIdentifier is None or effectTypeIdentifier != activeEffect.TypeIdentifier:
						continue

					if not isinstance(effectContainerData, dict):
						raise Exceptions.IncorrectTypeException(effectContainerData, "data[%s][%s]" % (effectsSavingKey, effectDataIndex), (dict,))

					effectData = effectContainerData[effectsDataSavingKey]  # type: typing.Optional[dict]

					if not isinstance(effectData, dict):
						raise Exceptions.IncorrectTypeException(effectData, "data[%s][%s][%s]" % (effectsSavingKey, effectDataIndex, effectsDataSavingKey), (dict,))

					if not activeEffect.LoadFromDictionary(effectData, lastVersion = lastVersion):
						operationSuccessful = False

					break
			except:
				Debug.Log("Load operation in a savable object failed to load the effect data of an effect with the identifier '%s'.\n%s" % (activeEffect.TypeIdentifier, operationInformation), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				operationSuccessful = False

		if not operationSuccessful:
			return False

		return superOperationSuccessful

	def _SaveToDictionaryInternal (self) -> typing.Tuple[bool, dict]:
		superOperationSuccessful, data = super()._SaveToDictionaryInternal()  # type: bool, dict

		operationSuccessful = True  # type: bool
		operationInformation = self.SavableOperationInformation  # type: str

		effectsSavingKey = self._effectsSavingKey  # type: str
		effectsDataSavingKey = "Data"  # type: str
		effectsTypeSavingKey = "Type"  # type: str

		effectsListData = list()  # type: typing.List[typing.Optional[dict]]

		for activeEffect in self._activeEffects:  # type: EffectsBase.EffectBase
			if not isinstance(activeEffect, EffectsBase.EffectBase):
				Debug.Log("Found an object in the effects list that was not an effect.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":EffectSavingOperationNotEffectType")
				continue

			try:
				effectContainerData = dict()  # type: dict
				entryOperationSuccessful, effectData = activeEffect.SaveToDictionary()  # type: bool, dict

				if not entryOperationSuccessful:
					operationSuccessful = False

				effectTypeIdentifier = activeEffect.TypeIdentifier  # type: str

				if not isinstance(effectTypeIdentifier, str):
					raise Exceptions.IncorrectReturnTypeException(effectTypeIdentifier, "typeFetcher", (str,))

				effectContainerData[effectsTypeSavingKey] = effectTypeIdentifier
				effectContainerData[effectsDataSavingKey] = effectData

				effectsListData.append(effectContainerData)
			except:
				Debug.Log("Save operation in a savable object failed to save the effect data of an effect with the identifier '%s'.\n%s" % (activeEffect.TypeIdentifier, operationInformation), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				operationSuccessful = False

			data[effectsSavingKey] = effectsListData

		if not operationSuccessful:
			return False, data

		return superOperationSuccessful, data

	def _ResetInternal (self) -> bool:
		superOperationSuccessful = super()._ResetInternal()  # type: bool

		operationInformation = self.SavableOperationInformation  # type: str

		for activeEffect in self._activeEffects:  # type: EffectsBase.EffectBase
			if not isinstance(activeEffect, EffectsBase.EffectBase):
				Debug.Log("Found an object in the effects list that was not an effect.\n%s" % operationInformation, self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__, lockIdentifier = __name__ + ":TrackerSavingOperationNotTrackerType")
				continue

			activeEffect.Reset()

		return superOperationSuccessful
