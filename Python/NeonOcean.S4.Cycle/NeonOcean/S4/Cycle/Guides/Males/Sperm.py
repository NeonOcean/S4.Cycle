from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Cycle.Tools import Distribution
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultSpermGuide = None  # type: SpermGuide
SpermGuideIdentifier = "Sperm"  # type: str

class SpermGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"LifetimeDistributionMean": Distribution.TunableNormalDistribution(description = "A distribution to select the mean of every sperm cell's lifetime normal distribution. These values should be in reproductive minutes.", meanDefault = 5760, standardDeviationDefault = 720),
		"LifetimeDistributionSD": Distribution.TunableNormalDistribution(description = "A distribution to select the standard deviation of every sperm cell's lifetime normal distribution. These values should be in reproductive minutes.", meanDefault = 960, standardDeviationDefault = 240),
		"SpermCount": Distribution.TunableNormalDistribution(description = "A distribution used to select a random sperm count.", meanDefault = 400000000, standardDeviationDefault = 75000000),
		"MotilePercentage": Distribution.TunableNormalDistribution(description = "A distribution to select the percentage of sperm that can make it to an ovum.", meanDefault = 0.8, standardDeviationDefault = 0.05),
		"ViablePercentage": Distribution.TunableNormalDistribution(description = "A distribution to select the percentage of sperm that can produce a viable fetus.", meanDefault = 0.8, standardDeviationDefault = 0.05),
	}

	LifetimeDistributionMean: Distribution.NormalDistribution
	LifetimeDistributionSD: Distribution.NormalDistribution
	SpermCount: Distribution.NormalDistribution
	MotilePercentage: Distribution.NormalDistribution
	ViablePercentage: Distribution.NormalDistribution

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return SpermGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultSpermGuide

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

class HumanSpermGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Sperm_Guide"

	Guide = None  # type: SpermGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return SpermGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultSpermGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanSpermGuide.Guide)

		DefaultSpermGuide = cls.Guide

def _Setup () -> None:
	global DefaultSpermGuide

	DefaultSpermGuide = SpermGuide.TunableFactory().default

_Setup()
