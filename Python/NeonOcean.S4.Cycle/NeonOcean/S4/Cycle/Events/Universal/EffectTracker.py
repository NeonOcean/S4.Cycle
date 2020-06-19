from __future__ import annotations

from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Main.Tools import Exceptions

class EffectAddedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, addedEffect):
		from NeonOcean.S4.Cycle.Effects import Base as EffectsBase

		if not isinstance(addedEffect, EffectsBase.EffectBase):
			raise Exceptions.IncorrectTypeException(addedEffect, "addedEffect", (EffectsBase.EffectBase, ))

		self._addedEffect = addedEffect  # type: EffectsBase.EffectBase

	@property
	def AddedEffect (self):
		return self._addedEffect

class EffectRemovedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, removedEffect):
		from NeonOcean.S4.Cycle.Effects import Base as EffectsBase

		if not isinstance(removedEffect, EffectsBase.EffectBase):
			raise Exceptions.IncorrectTypeException(removedEffect, "removedEffect", (EffectsBase.EffectBase,))

		self._removedEffect = removedEffect  # type: EffectsBase.EffectBase

	@property
	def RemovedEffect (self):
		return self._removedEffect
