from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Guides import Base as GuidesBase
from NeonOcean.S4.Cycle.Tools import Curve
from NeonOcean.S4.Main.Tools import Exceptions
from sims4.tuning import tunable

# noinspection PyTypeChecker
DefaultEmergencyContraceptivePillEffectGuide = None  # type: EmergencyContraceptivePillEffectGuide
EmergencyContraceptivePillEffectGuideIdentifier = "EmergencyContraceptivePillEffect"  # type: str

class EmergencyContraceptivePillEffectGuide(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit, GuidesBase.GuideBase):
	FACTORY_TUNABLES = {
		"StrengthPerReproductiveMinute": tunable.Tunable(description = "The amount the strength of the emergency contraceptive changes per reproductive minute.", tunable_type = float, default = 0),
		"DelayTimeMean": Curve.TunableCurve(description = "The average time in reproductive minutes that an ovum will be delayed by, based on how strong the medication's effect's currently are. The value taken from this curve will be combined with the standard deviation curve's value in a normal distribution, which will be used to randomly generate a delay time. This will not be used if quick mode is enabled."),
		"DelayTimeStandardDeviation": Curve.TunableCurve(description = "The standard deviation time in reproductive minutes that an ovum will be delayed by, based on how strong the medication's effect's currently are. The value taken from this curve will be combined with the mean curve's value in a normal distribution, which will be used to randomly generate a delay time. This will not be used if quick mode is enabled."),
		"DelayTimeMaximum": tunable.Tunable(description = "The maximum amount of time in reproductive minutes emergency contraceptives can delay an ovum by. If the ovum has already been delayed by this amount of time or more, it will not be further delayed.", tunable_type = float, default = 10080),
		"QuickModeSpermBlockChance": Curve.TunableCurve(description = "The chance that a sperm object will be prevented from fertilizing an ovum, based on how strong the medication's effect's currently are. This is only used when quick mode is enabled."),
	}

	StrengthPerReproductiveMinute: float
	DelayTimeMean: Curve.Curve
	DelayTimeStandardDeviation: Curve.Curve
	DelayTimeMaximum: float
	QuickModeSpermBlockChance: Curve.Curve

	@classmethod
	def GetIdentifier (cls):
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		return EmergencyContraceptivePillEffectGuideIdentifier

	@classmethod
	def GetDefaultGuide (cls):
		"""
		Get a default instance of this guide.
		"""

		return DefaultEmergencyContraceptivePillEffectGuide

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

class HumanEmergencyContraceptivePillEffectGuide(GuidesBase.GuideTuningHandler):
	_snippetName = This.Mod.Namespace.replace(".", "_") + "_Human_Emergency_Contraceptive_Pill_Effect_Guide"

	Guide = None  # type: EmergencyContraceptivePillEffectGuide

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		return EmergencyContraceptivePillEffectGuide.TunableFactory()

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		from NeonOcean.S4.Cycle import GuideGroups

		global DefaultEmergencyContraceptivePillEffectGuide

		super()._SnippetTuningCallback(guideSnippets)
		GuideGroups.HumanGuideGroup.Guides.append(HumanEmergencyContraceptivePillEffectGuide.Guide)

		DefaultEmergencyContraceptivePillEffectGuide = cls.Guide

def _Setup () -> None:
	global DefaultEmergencyContraceptivePillEffectGuide

	DefaultEmergencyContraceptivePillEffectGuide = EmergencyContraceptivePillEffectGuide.TunableFactory().default

_Setup()
