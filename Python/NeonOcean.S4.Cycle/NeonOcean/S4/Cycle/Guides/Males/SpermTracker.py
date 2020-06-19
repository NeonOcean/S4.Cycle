from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultSpermTrackerGuide = None  # type: SpermTrackerGuide
SpermTrackerGuideIdentifier = "SpermTracker"  # type: str

class SpermTrackerGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"FertilizationEqualChanceCount": tunable.Tunable(int, 75000000, description = "The total sperm count at which there is a 50-50 chance that a sperm cell will fertilize the ovum.")
	}

	FertilizationEqualChanceCount: int

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return SpermTrackerGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultSpermTrackerGuide

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

class HumanSpermTrackerGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Sperm_Tracker_Guide"

	Guide = None  # type: SpermTrackerGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return SpermTrackerGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultSpermTrackerGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanSpermTrackerGuide.Guide)

		DefaultSpermTrackerGuide = cls.Guide

def _Setup () -> None:
	global DefaultSpermTrackerGuide

	DefaultSpermTrackerGuide = SpermTrackerGuide.TunableFactory().default

_Setup()
