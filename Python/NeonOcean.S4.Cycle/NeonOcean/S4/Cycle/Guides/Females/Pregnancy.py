from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultPregnancyGuide = None  # type: PregnancyGuide
PregnancyGuideIdentifier = "Pregnancy"  # type: str

class PregnancyGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"PregnancyTime": tunable.TunableRange(description = "The amount of time in reproductive minutes that a pregnancy should last for.", tunable_type = float, default = 388800, minimum = 1440),
		"LatestDiscoveryTime": tunable.TunableRange(description = "The latest time a pregnancy can be discovered in reproductive minutes.", tunable_type = float, default = 129600, minimum = 10)
	}

	PregnancyTime: float
	LatestDiscoveryTime: float

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return PregnancyGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultPregnancyGuide

	@classmethod
	def GetGuide (cls, guideGroup):
		"""
		Get this guide group's instance of this guide or the default guide, if the group doesn't have a copy.
		"""

		from NeonOcean.S4.Cycle.GuideGroups import Base as GuidesGroupsBase

		if not isinstance(guideGroup, GuidesGroupsBase.GuideGroup):
			raise Exceptions.IncorrectTypeException(guideGroup, "guideGroup", (GuidesGroupsBase.GuideGroup,))

		guideGroupGuide = guideGroup.GetGuide(cls.GetIdentifier())  # type: typing.Optional[GuidesBase.GuideBase]
		return guideGroupGuide if guideGroupGuide is not None else cls.GetDefaultGuide()

class HumanPregnancyGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Pregnancy_Guide"

	Guide = None  # type: PregnancyGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return PregnancyGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultPregnancyGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanPregnancyGuide.Guide)

		DefaultPregnancyGuide = cls.Guide

def _Setup () -> None:
	global DefaultPregnancyGuide

	DefaultPregnancyGuide = PregnancyGuide.TunableFactory().default

_Setup()
