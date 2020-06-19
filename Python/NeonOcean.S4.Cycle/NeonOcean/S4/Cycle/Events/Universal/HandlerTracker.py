from __future__ import annotations

from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Main.Tools import Exceptions

class HandlerAddedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, addedHandler):
		from NeonOcean.S4.Cycle.Handlers import Base as HandlersBase

		if not isinstance(addedHandler, HandlersBase.HandlerBase):
			raise Exceptions.IncorrectTypeException(addedHandler, "addedHandler", (HandlersBase.HandlerBase, ))

		self._addedHandler = addedHandler  # type: HandlersBase.HandlerBase

	@property
	def AddedHandler (self):
		return self._addedHandler

class HandlerRemovedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, removedHandler):
		from NeonOcean.S4.Cycle.Handlers import Base as HandlersBase

		if not isinstance(removedHandler, HandlersBase.HandlerBase):
			raise Exceptions.IncorrectTypeException(removedHandler, "removedHandler", (HandlersBase.HandlerBase,))

		self._removedHandler = removedHandler  # type: HandlersBase.HandlerBase

	@property
	def RemovedHandler (self):
		return self._removedHandler
