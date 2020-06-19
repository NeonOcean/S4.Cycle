from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Cycle.Tools import Distribution
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultOvumGuide = None  # type: OvumGuide
OvumGuideIdentifier = "Ovum"  # type: str

class OvumGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"NormalLifetime": Distribution.TunableNormalDistribution(description = "The distribution used to create a random ovum lifetime. These values should be in reproductive minutes.", meanDefault = 1080, standardDeviationDefault = 120),
		"ImplantationTime": Distribution.TunableNormalDistribution(description = "The distribution used to create a random ovum implantation time. The ovum's lifetime should be extended to the generated value if fertilized. These values should be in reproductive minutes.", meanDefault = 11520, standardDeviationDefault = 864),
		"ViabilityChance": tunable.Tunable(description = "The chance that a particular ovum can ever cause a pregnancy.", tunable_type = float, default = 0.8),
	}

	NormalLifetime: Distribution.NormalDistribution
	ImplantationTime: Distribution.NormalDistribution
	ViabilityChance: float

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return OvumGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultOvumGuide

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

class HumanOvumGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Ovum_Guide"

	Guide = None  # type: OvumGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return OvumGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultOvumGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanOvumGuide.Guide)

		DefaultOvumGuide = cls.Guide

def _Setup () -> None:
	global DefaultOvumGuide

	DefaultOvumGuide = OvumGuide.TunableFactory().default

_Setup()
