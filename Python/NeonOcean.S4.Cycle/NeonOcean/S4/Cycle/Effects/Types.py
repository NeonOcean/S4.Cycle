from __future__ import annotations

import typing

from NeonOcean.S4.Cycle.Effects import Base as EffectsBase
from NeonOcean.S4.Main.Tools import Exceptions

_effectTypes = dict()  # type: typing.Dict[str, typing.Type[EffectsBase.EffectBase]]

def RegisterEffectType (identifier: str, effectType: typing.Type[EffectsBase.EffectBase]) -> None:
	"""
	Register a reproductive effect type. Registration is required to allow for the effect to be loaded. If a effect type with this identifier is already
	registered it will be replaced.
	:param identifier: The identifier of the effect type.
	:type identifier: str
	:param effectType: The effect type's class.
	:type effectType: typing.Type[EffectsBase.BaseEffect]
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not isinstance(effectType, type):
		raise Exceptions.IncorrectTypeException(effectType, "effectType", (type,))

	if not issubclass(effectType, EffectsBase.EffectBase):
		raise Exceptions.DoesNotInheritException("effectType", (EffectsBase.EffectBase,))

	_effectTypes[identifier] = effectType

def GetEffectType (identifier: str) -> typing.Type[EffectsBase.EffectBase]:
	"""
	Get a registered effect type.
	:param identifier: The identifier of the effect type.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not identifier in _effectTypes:
		raise ValueError("No effect type with the identifier '" + identifier + "' has been registered.")

	return _effectTypes.get(identifier)

def GetAllEffectTypes () -> typing.List[typing.Type[EffectsBase.EffectBase]]:
	"""
	Get a list of all registered effect types.
	"""

	return list(_effectTypes.values())

def GetAllEffectTypeIdentifiers () -> typing.Set[str]:
	"""
	Get a list of every registered effect type's identifier.
	"""

	return set(_effectTypes.keys())

def EffectTypeExists (identifier: str) -> bool:
	"""
	Get whether or not a effect of this type exists.
	:param identifier: The identifier of the effect.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	return identifier in _effectTypes