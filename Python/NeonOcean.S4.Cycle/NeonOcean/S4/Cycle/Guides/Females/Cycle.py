from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Cycle.Tools import Distribution, Probability
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultCycleMenstrualGuide = None  # type: CycleMenstrualGuide
CycleMenstrualGuideIdentifier = "CycleMenstrual"  # type: str

class CycleGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"OvumReleaseAmount": Probability.TunableProbability(description = "The probabilities for the amount of egg cells to be released during the cycle."),
	}

	OvumReleaseAmount: Probability.Probability

	@classmethod
	def GetIdentifier (cls) -> str:
		raise NotImplementedError()

class CycleMenstrualGuide(CycleGuide):
	FACTORY_TUNABLES = {
		"FollicularLength": Distribution.TunableNormalDistribution(description = "A distribution for the length of a cycle's follicular phase. These values should be in reproductive minutes.", meanDefault = 20160, standardDeviationDefault = 1440),
		"OvulationLength": Distribution.TunableNormalDistribution(description = "A distribution for the length of a cycle's ovulation. These values should be in reproductive minutes.", meanDefault = 1800, standardDeviationDefault = 480),
		"LutealLength": Distribution.TunableNormalDistribution(description = "A distribution for the length of a cycle's luteal phase. These values should be in reproductive minutes.", meanDefault = 20160, standardDeviationDefault = 1440),
		"MenstruationLength": Distribution.TunableNormalDistribution(description = "A distribution for the length of a cycle's menstruation. These values should be in reproductive minutes.", meanDefault = 5760, standardDeviationDefault = 720)
	}

	FollicularLength: Distribution.NormalDistribution
	OvulationLength: Distribution.NormalDistribution
	LutealLength: Distribution.NormalDistribution
	MenstruationLength: Distribution.NormalDistribution

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return CycleMenstrualGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultCycleMenstrualGuide

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

class HumanCycleMenstrualGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Cycle_Menstrual_Guide"

	Guide = None  # type: CycleMenstrualGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return CycleMenstrualGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultCycleMenstrualGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanCycleMenstrualGuide.Guide)

		DefaultCycleMenstrualGuide = cls.Guide

def _Setup () -> None:
	global DefaultCycleMenstrualGuide

	DefaultCycleMenstrualGuide = CycleMenstrualGuide.TunableFactory().default

_Setup()
