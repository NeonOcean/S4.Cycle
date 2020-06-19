from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import ReproductionShared
from NeonOcean.S4.Main.Tools import Exceptions

_trackerTypes = dict()  # type: typing.Dict[str, typing.Type[ReproductionShared.TrackerBase]]

def RegisterTrackerType (identifier: str, trackerType: typing.Type[ReproductionShared.TrackerBase]) -> None:
	"""
	Register a reproductive cycle type. Registration is required to allow for the tracker to be loaded. If a tracker type with this identifier is already
	registered it will be replaced.
	:param identifier: The identifier of the tracker type.
	:type identifier: str
	:param trackerType: The tracker type's class.
	:type trackerType: typing.Type[ReproductionShared.TrackerBase]
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not isinstance(trackerType, type):
		raise Exceptions.IncorrectTypeException(trackerType, "trackerType", (type,))

	if not issubclass(trackerType, ReproductionShared.TrackerBase):
		raise Exceptions.DoesNotInheritException("trackerType", (ReproductionShared.TrackerBase,))

	_trackerTypes[identifier] = trackerType

def GetTrackerType (identifier: str) -> typing.Type[ReproductionShared.TrackerBase]:
	"""
	Get a registered tracker type.
	:param identifier: The identifier of the tracker type.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	if not identifier in _trackerTypes:
		raise ValueError("No tracker type with the identifier '" + identifier + "' has been registered.")

	return _trackerTypes.get(identifier)

def GetAllTrackerTypes () -> typing.List[typing.Type[ReproductionShared.TrackerBase]]:
	"""
	Get a list of all registered tracker types.
	"""

	return list(_trackerTypes.values())

def GetAllTrackerTypeIdentifiers () -> typing.Set[str]:
	"""
	Get a list of every registered tracker type's identifier.
	"""

	return set(_trackerTypes.keys())

def TrackerTypeExists (identifier: str) -> bool:
	"""
	Get whether or not a tracker of this type exists.
	:param identifier: The identifier of the tracker.
	:type identifier: str
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	return identifier in _trackerTypes