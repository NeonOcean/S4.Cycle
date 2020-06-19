from __future__ import annotations

import typing

from NeonOcean.S4.Cycle.Handlers import Base as HandlerBase
from NeonOcean.S4.Main.Tools import Exceptions

_handlerTypes = dict()  # type: typing.Dict[str, typing.Type[HandlerBase.HandlerBase]]

def RegisterHandlerType (identifier: str, handlerType: typing.Type[HandlerBase.HandlerBase]) -> None:
	"""
	Register a reproductive handler type. Registration is required to allow for the handler to be loaded. If a handler type with this identifier is already
	registered it will be replaced.
	:param identifier: The identifier of the handler type.
	:type identifier: str
	:param handlerType: The handler type's class.
	:type handlerType: typing.Type[HandlerBase.BaseHandler]
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not isinstance(handlerType, type):
		raise Exceptions.IncorrectTypeException(handlerType, "handlerType", (type,))

	if not issubclass(handlerType, HandlerBase.HandlerBase):
		raise Exceptions.DoesNotInheritException("handlerType", (HandlerBase.HandlerBase,))

	_handlerTypes[identifier] = handlerType

def GetHandlerType (identifier: str) -> typing.Type[HandlerBase.HandlerBase]:
	"""
	Get a registered handler type.
	:param identifier: The identifier of the handler type.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not identifier in _handlerTypes:
		raise ValueError("No handler type with the identifier '" + identifier + "' has been registered.")

	return _handlerTypes.get(identifier)

def GetAllHandlerTypes () -> typing.List[typing.Type[HandlerBase.HandlerBase]]:
	"""
	Get a list of all registered handler types.
	"""

	return list(_handlerTypes.values())

def GetAllHandlerTypeIdentifiers () -> typing.Set[str]:
	"""
	Get a list of every registered handler type's identifier.
	"""

	return set(_handlerTypes.keys())

def HandlerTypeExists (identifier: str) -> bool:
	"""
	Get whether or not a handler of this type exists.
	:param identifier: The identifier of the handler.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	return identifier in _handlerTypes