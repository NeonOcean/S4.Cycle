from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Cycle.Tools import Probability, Curve
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultBirthControlPillsEffectGuide = None  # type: BirthControlPillsEffectGuide
BirthControlPillsEffectGuideIdentifier = "BirthControlPillsEffect"  # type: str

class BirthControlPillsEffectGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"NeedPerGameMinute": tunable.Tunable(description = "The amount the birth control pills effect's need value changes per game minute. The need value goes from 0 to 1, with 1 being the most need.", tunable_type = float, default = 0.00046296296),
		"EntrenchmentPerReproductiveMinute": Curve.TunableCurve(description = "A curve that indicates the amount the birth control pills effect's entrenchment value changes per sim minute, based on the need value. X inputs are the need values, this will be a number from 0 to 1. Y values are the rate at which the entrenchment value should change per reproductive minute."),

		"MenstrualBuffRarityOptionAdjusters": tunable.TunableMapping(
			description = "Probability weight offset adjusters to be applied to the buff rarity probability object when the birth control pills effect is active.\n"
						  "Expression adjusters will receive an additional value.\n"
						  "The 'Need' value is a number indicating how recently the sim has taken the pill. 0 means the sim has just taken the pill, 1 means hasn't taken the pill recently. Around a value of 1, the 'Entrenched' value will slowly decrease."
						  "The 'Entrenchment' value is a number indicating how effective the medication is and slowly increases the long a sim takes the pills. 0 is least effective and 1 is most effective.",
			key_type = tunable.Tunable(description = "An identifier that corresponds with an existing buff rarity option.", tunable_type = str, default = "Abstain"),
			value_type = Probability.TunableOptionAdjuster()
		),

		"OvumReleaseSuppressionCurve": Curve.TunableCurve(description = "A curve that indicates the chance that the release of an ovum will be suppressed, based on the birth control's entrenchment value. X inputs are the entrenchment values. Y values are the chance that an ovum will be suppressed. Both x and y values should be limited to between 0 and 1."),

		"GameMinutesBetweenPills": tunable.TunableRange(description = "The amount of game minutes since the last pill was taken until the sim is supposed to take another. This is only used to determine if a pill was missed or not.", tunable_type = float, default = 1440, minimum = 0),
		"GameMinutesBeforePillMissed": tunable.TunableRange(description = "The amount of game minutes since a pill was suppose to be taken until the sim has officially missed that pill. This is only used to determine if a pill was missed or not.", tunable_type = float, default = 1080, minimum = 0),

		"GameMinutesUntilPillInteractionAllowed": tunable.TunableRange(description = "The amount of game minute from since the last pill, until the take pill interaction should be unlocked for use.", tunable_type = float, default = 960, minimum = 0),
		"MissedPillsBeforeIntentional": tunable.TunableRange(description = "The number of missed pills before we start to consider them intentionally missed", tunable_type = int, default = 4, minimum = 0)
	}

	NeedPerGameMinute: float
	EntrenchmentPerReproductiveMinute: Curve.Curve

	MenstrualBuffRarityOptionAdjusters: typing.Dict[str, Probability.OptionAdjuster]
	OvumReleaseSuppressionCurve: Curve.Curve

	GameMinutesBetweenPills: float
	GameMinutesBeforePillMissed: float

	GameMinutesUntilPillInteractionAllowed: float
	MissedPillsBeforeIntentional: int

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return BirthControlPillsEffectGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultBirthControlPillsEffectGuide

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

class HumanBirthControlPillsEffectGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Birth_Control_Pills_Effect_Guide"

	Guide = None  # type: BirthControlPillsEffectGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return BirthControlPillsEffectGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultBirthControlPillsEffectGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanBirthControlPillsEffectGuide.Guide)

		DefaultBirthControlPillsEffectGuide = cls.Guide

def _Setup () -> None:
	global DefaultBirthControlPillsEffectGuide

	DefaultBirthControlPillsEffectGuide = BirthControlPillsEffectGuide.TunableFactory().default

_Setup()
