from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Buffs import Shared as BuffsShared
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Cycle.Tools import Distribution, Probability
from NeonOcean.S4.Main.Tools import Exceptions, Tunable as ToolsTunable
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultMenstrualEffectGuide = None  # type: MenstrualEffectGuide
MenstrualEffectGuideIdentifier = "MenstrualEffect"  # type: str

class MenstrualEffectGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"BuffRarity": Probability.TunableProbability(
			description = "A set of weights used to determine the rarity of the next buff. Adding an option with the identifier 'Abstain' will allow for a chance to not add a buff."
		),
		"BuffRarityOffsets": tunable.TunableMapping(
			description = "A set of option weight offsets to be temporarily applied when a buff is added to the sim. This may be used to reduce the probability that multiple very strenuous buffs are added in a row.",
			key_type = ToolsTunable.TunablePythonEnumEntry(description = "How rare the last buff was.", enumType = BuffsShared.BuffRarity, default = BuffsShared.BuffRarity.NotApplicable),
			value_type = tunable.TunableMapping(
				key_type = tunable.Tunable(description = "The identifier of the rarity option that needs to be adjusted.", tunable_type = str, default = "Abstain"),
				value_type = Probability.TunableOptionWeightAdjuster()
			)
		),
		"AbstainedBuffRarityOffset": tunable.TunableMapping(
			key_type = tunable.Tunable(description = "The identifier of the rarity option that needs to be adjusted.", tunable_type = str, default = "Abstain"),
			value_type = Probability.TunableOptionWeightAdjuster()
		),
		"BuffRarityResetRates": tunable.TunableMapping(
			description = "The rates at which, for each sim minute, rarity weight offsets move back to 0.",
			key_type = tunable.Tunable(description = "A rarity option identifier.", tunable_type = str, default = BuffsShared.BuffRarity.NotApplicable.name),
			value_type = tunable.TunableRange(description = "The amount the option weight offset moves toward 0 within a sim minute.", tunable_type = float, default = 0.3, minimum = 0)
		),
		"BuffCoolDown": tunable.TunableMapping(
			description = "A set of cool down distributions to randomly select the time between two buffs being added based on how rare first buff was.",
			key_type = ToolsTunable.TunablePythonEnumEntry(description = "How rare the first buff was.", enumType = BuffsShared.BuffRarity, default = BuffsShared.BuffRarity.NotApplicable),
			value_type = Distribution.TunableNormalDistribution(description = "A distribution to select the minimum amount of time in sim minutes between buffs. More strenuous buffs should impose longer cool downs than less strenuous ones.", meanDefault = 240, standardDeviationDefault = 60)
		),
		"AbstainedBuffCoolDown": Distribution.TunableNormalDistribution("A distribution to select, if we didn't choose a buff when the opportunity arose, the minimum amount of time in sim minutes until we can try to pick a buff again.", meanDefault = 120, standardDeviationDefault = 15),
	}

	BuffRarity: Probability.Probability
	BuffRarityOffsets: typing.Dict[BuffsShared.BuffRarity, typing.Dict[str, Probability.OptionWeightAdjuster]]
	AbstainedBuffRarityOffset: typing.Dict[str, Probability.OptionWeightAdjuster]
	BuffRarityResetRates: typing.Dict[str, float]
	AbstainedBuffCoolDown: Distribution.NormalDistribution
	BuffCoolDown: typing.Dict[BuffsShared.BuffRarity, Distribution.NormalDistribution]

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return MenstrualEffectGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultMenstrualEffectGuide

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

class HumanMenstrualEffectGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Menstrual_Effect_Guide"

	Guide = None  # type: MenstrualEffectGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return MenstrualEffectGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultMenstrualEffectGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanMenstrualEffectGuide.Guide)

		DefaultMenstrualEffectGuide = cls.Guide

def _Setup () -> None:
	global DefaultMenstrualEffectGuide

	DefaultMenstrualEffectGuide = MenstrualEffectGuide.TunableFactory().default

_Setup()
