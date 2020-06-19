from __future__ import annotations

import typing

from NeonOcean.S4.Cycle.Females.Cycle import Base as CycleBase
from NeonOcean.S4.Main.Tools import Exceptions

_cycleTypes = dict()  # type: typing.Dict[str, typing.Type[CycleBase.CycleBase]]

def RegisterCycleType (identifier: str, cycleType: typing.Type[CycleBase.CycleBase]) -> None:
	"""
	Register a reproductive cycle type. Registration is required to allow for the cycle to be loaded. If a cycle type with this identifier is already
	registered it will be replaced.
	:param identifier: The identifier of the cycle type.
	:type identifier: str
	:param cycleType: The cycle type's class.
	:type cycleType: typing.Type[CyclesBase.CycleBase]
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not isinstance(cycleType, type):
		raise Exceptions.IncorrectTypeException(cycleType, "cycleType", (type,))

	if not issubclass(cycleType, CycleBase.CycleBase):
		raise Exceptions.DoesNotInheritException("cycleType", (CycleBase.CycleBase,))

	_cycleTypes[identifier] = cycleType

def GetCycleType (identifier: str) -> typing.Type[CycleBase.CycleBase]:
	"""
	Get a registered cycle type.
	:param identifier: The identifier of the cycle type.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not identifier in _cycleTypes:
		raise ValueError("No cycle type with the identifier '" + identifier + "' has been registered.")

	return _cycleTypes.get(identifier)

def GetAllCycleTypes () -> typing.List[typing.Type[CycleBase.CycleBase]]:
	"""
	Get a list of all registered cycle types.
	"""

	return list(_cycleTypes.values())

def GetAllCycleTypeIdentifiers () -> typing.Set[str]:
	"""
	Get a list of every registered cycle type's identifier.
	"""

	return set(_cycleTypes.keys())

def CycleTypeExists (identifier: str) -> bool:
	"""
	Get whether or not a cycle of this type exists.
	:param identifier: The identifier of the cycle.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	return identifier in _cycleTypes