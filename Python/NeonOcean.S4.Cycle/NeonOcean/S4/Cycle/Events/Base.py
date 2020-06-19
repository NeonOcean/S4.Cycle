from __future__ import annotations

import typing

from NeonOcean.S4.Main.Tools import Events, Exceptions

class ReproductiveArguments(Events.EventArguments):
	"""
	The base reproductive event arguments.
	"""

	pass

class SeededArguments(ReproductiveArguments):
	def __init__ (self, seed: int, *args, **kwargs):
		"""
		The base reproductive event arguments with a seed value for randomization.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		"""

		if not isinstance(seed, int):
			raise Exceptions.IncorrectTypeException(seed, "seed", (int,))

		super().__init__(*args, **kwargs)

		self._seed = seed  # type: int

	@property
	def Seed (self) -> int:
		"""
		The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		"""

		return self._seed

class TargetedArguments (ReproductiveArguments):
	def __init__ (self, targetedObject: typing.Any, *args, **kwargs):
		"""
		The base reproductive event arguments with an object the event is being triggered for.

		:param targetedObject: The object the event has been triggered for.
		:type targetedObject: typing.Any
		"""

		super().__init__(*args, **kwargs)

		self._targetedObject = targetedObject

	@property
	def TargetedObject (self) -> typing.Any:
		"""
		The object the event has been triggered for.
		"""

		return self._targetedObject

class SeededAndTargetedArguments (SeededArguments, TargetedArguments):
	def __init__ (self, seed: int, targetedObject: typing.Any, *args, **kwargs):
		"""
		The base reproductive event arguments with a seed value for randomization and an object the event is being triggered for.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The object the event has been triggered for.
		:type targetedObject: typing.Any
		"""

		super().__init__(seed = seed, targetedObject = targetedObject, *args, **kwargs)

class GenerationArguments (SeededAndTargetedArguments):
	def __init__ (self, seed: int, targetedObject: typing.Any, *args, **kwargs):
		"""
		Reproductive event arguments for when a new object needs its values randomized.

		:param seed: The seed used in the creation of random values for this event. The seed should be mixed with another number specific to each
		randomization operation, otherwise everything would generate the same numbers.
		:type seed: int
		:param targetedObject: The object the event has been triggered for.
		:type targetedObject: typing.Any
		"""

		super().__init__(seed = seed, targetedObject = targetedObject, *args, **kwargs)

		self.PreGenerationEvent = Events.EventHandler()
		self.PostGenerationEvent = Events.EventHandler()

	@property
	def PreGenerationEvent (self) -> Events.EventHandler:
		"""
		An event that should be triggered just before the generating object derives its values from these event arguments, and just after the
		generation event completes.
		The event arguments parameter should be a 'EventArguments' object, the standard event arguments object for the event system.
		"""

		return self._preGenerationEvent

	@PreGenerationEvent.setter
	def PreGenerationEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "PreGenerationEvent", (Events.EventHandler,))

		self._preGenerationEvent = value

	@property
	def PostGenerationEvent (self) -> Events.EventHandler:
		"""
		An event that should be triggered just after the generating object finishes deriving its values from these event arguments.
		The event arguments parameter should be a 'EventArguments' object, the standard event arguments object for the event system.
		"""

		return self._postGenerationEvent

	@PostGenerationEvent.setter
	def PostGenerationEvent (self, value: Events.EventHandler) -> None:
		if not isinstance(value, Events.EventHandler):
			raise Exceptions.IncorrectTypeException(value, "PostGenerationEvent", (Events.EventHandler,))

		self._postGenerationEvent = value


