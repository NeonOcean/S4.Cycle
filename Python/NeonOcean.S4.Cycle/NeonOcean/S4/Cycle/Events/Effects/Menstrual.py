from __future__ import annotations

from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Main.Tools import Exceptions
from buffs import buff

class MenstrualEffectBuffAddedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, addedBuff: buff.Buff):
		if not isinstance(addedBuff, buff.Buff):
			raise Exceptions.IncorrectTypeException(addedBuff, "addedBuff", (buff.Buff,))

		self._addedBuff = addedBuff  # type: buff.Buff

	@property
	def AddedBuff (self) -> buff.Buff:
		return self._addedBuff

class MenstrualEffectBuffRemovedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, removedBuff: buff.Buff):
		if not isinstance(removedBuff, buff.Buff):
			raise Exceptions.IncorrectTypeException(removedBuff, "removedBuff", (buff.Buff,))

		self._removedBuff = removedBuff  # type: buff.Buff

	@property
	def RemovedBuff (self) -> buff.Buff:
		return self._removedBuff
