from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Exceptions, Types
from sims import sim_info

_guideGroups = list()  # type: typing.List[GuideGroup]

class GuideGroup:
	def __init__ (self, matcher: typing.Callable[[sim_info.SimInfo], bool]):
		"""
		A group of guides for a specific type of sim.
		:param matcher: A callable that will be used to test if this guide group is appropriate for a sim. It should take the sim's info and return True or False.
		:type matcher: typing.Callable[[sim_info.SimInfo], bool]
		"""

		self.Matcher = matcher  # type: typing.Callable[[sim_info.SimInfo], bool]

		self.Guides = list()

	@property
	def Guides (self) -> list:
		"""
		The guides attached to this group.
		"""

		return self._guides

	@Guides.setter
	def Guides (self, value: list):
		if not isinstance(value, list):
			raise Exceptions.IncorrectTypeException(value, "value", (list,))

		self._guides = value

	def Matches (self, simInfo: sim_info.SimInfo) -> bool:
		"""
		Get whether or not this guide group is appropriate for the specified sim. This only calls the matcher with the sim as the parameter, it can fail
		if the matcher does.
		"""

		return self.Matcher(simInfo)

	def GetGuide (self, identifier: str):
		"""
		Get the first guide found with this identifier. If no such guide exists nothing will happen.
		"""

		for guide in self._guides:
			if guide.GetIdentifier() == identifier:
				return guide

		return None

	def HasGuide (self, identifier: str) -> bool:
		"""
		Get whether or not a guide with this identifier exists.
		"""

		for guide in self._guides:
			if guide.GetIdentifier() == identifier:
				return True

		return False

	def RemoveGuide (self, identifier: str) -> None:
		"""
		Remove the guide with this identifier from the group. If such a guide doesn't exist nothing will happen.
		"""

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		guideIndex = 0
		while guideIndex < len(self.Guides):
			if self.Guides[guideIndex].GetIdentifier() == identifier:
				self.Guides.pop(guideIndex)
				return

			guideIndex += 1

def RegisterGuideGroup (guideGroup: GuideGroup) -> None:
	"""
	Register a guide group to allow it to be checked by reproductive systems. If the guide group is already registered nothing will happen.
	"""

	if not isinstance(guideGroup, GuideGroup):
		raise Exceptions.IncorrectTypeException(guideGroup, "guideGroup", (GuideGroup,))

	if guideGroup in _guideGroups:
		return

	_guideGroups.append(guideGroup)

def FindGuideGroup (simInfo: sim_info.SimInfo) -> typing.Optional[GuideGroup]:
	"""
	Return the first guide group found that is appropriate for the specified sim. This will return None if no appropriate one is found.
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	for guideGroup in _guideGroups:  # type: GuideGroup
		try:
			if guideGroup.Matches(simInfo):
				return guideGroup
		except Exception as e:
			Debug.Log("Encountered an unhandled exception when checking if a guide group matches a sim. Matcher: " + Types.GetFullName(guideGroup.Matcher), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	return None

def GetAllGuideGroups () -> typing.List[GuideGroup]:
	"""
	Get a list of all registered guides groups.
	"""

	return list(_guideGroups)
