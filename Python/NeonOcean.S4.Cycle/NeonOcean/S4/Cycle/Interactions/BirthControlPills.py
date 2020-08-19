from __future__ import annotations

import typing
import services

import interactions
from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Mods import WickedWhims
from NeonOcean.S4.Cycle.Effects import BirthControlPills as EffectsBirthControlPills, Shared as EffectsShared
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Cycle.Universal import EffectTracker, Shared as UniversalShared
from NeonOcean.S4.Main import Debug, Language
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from event_testing import results, test_base
from interactions.base import immediate_interaction
from sims import sim_info
from sims4 import resources
from objects import definition_manager

TakePillInteractions = list()  # type: typing.List[typing.Type[TakePillInteraction]]
TakePillWickedWhimsInteractions = list()  # type: typing.List[typing.Type[TakePillWickedWhimsInteraction]]

ReadInstructionsInteractions = list()  # type: typing.List[typing.Type[ReadInstructionsInteraction]]

TakePillTooRecentTooltip = Language.String(This.Mod.Namespace + ".Interactions.Birth_Control_Pills.Take_Pill.Too_Recent_Tooltip")  # type: Language.String

class _TakePillInteractionBase(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	class _HasCycleTrackerTest(test_base.BaseTest):
		def __call__ (self, actors: typing.Tuple[sim_info.SimInfo, ...]):
			if len(actors) == 0:
				Debug.Log("Took pill recently test received an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			targetActor = actors[0]  # type: sim_info.SimInfo

			targetSystem = Reproduction.GetSimSystem(targetActor)  # type: ReproductionShared.ReproductiveSystem

			if targetSystem is None:
				return results.TestResult(False)

			targetCycleTracker = targetSystem.GetTracker(FemalesShared.CycleTrackerIdentifier)

			if targetCycleTracker is None:
				return results.TestResult(False)

			return results.TestResult(True)

		def get_expected_args (self) -> dict:
			# noinspection SpellCheckingInspection
			return {
				"actors": interactions.ParticipantType.Actor
			}

	class _TookPillRecentlyTest(test_base.BaseTest):
		def __call__ (self, actors: typing.Tuple[sim_info.SimInfo, ...]):
			if len(actors) == 0:
				Debug.Log("Took pill recently test received an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			targetActor = actors[0]  # type: sim_info.SimInfo

			targetSystem = Reproduction.GetSimSystem(targetActor)  # type: ReproductionShared.ReproductiveSystem

			if targetSystem is None:
				return results.TestResult(False)

			targetEffectTracker = targetSystem.GetTracker(UniversalShared.EffectTrackerIdentifier)  # type: typing.Optional[EffectTracker.EffectTracker]

			if targetEffectTracker is None:
				return results.TestResult(False)

			birthControlPillsEffect = targetEffectTracker.GetEffect(EffectsShared.BirthControlPillsEffectTypeIdentifier)  # type: typing.Optional[EffectsBirthControlPills.BirthControlPillsEffect]

			if birthControlPillsEffect is None:
				return results.TestResult(False)

			if birthControlPillsEffect.TooRecentForTakePillInteraction():
				return results.TestResult(False, tooltip = TakePillTooRecentTooltip.GetCallableLocalizationString())

			return results.TestResult(True)

		def get_expected_args (self) -> dict:
			# noinspection SpellCheckingInspection
			return {
				"actors": interactions.ParticipantType.Actor
			}

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		hasCycleTrackerTest = False  # type: bool
		hasTookPillRecentlyTest = False  # type: bool

		if cls._additional_tests is not None:
			for additionalTest in reversed(cls._additional_tests):
				if isinstance(additionalTest, cls._HasCycleTrackerTest):
					hasCycleTrackerTest = True
				elif isinstance(additionalTest, cls._TookPillRecentlyTest):
					hasTookPillRecentlyTest = True

		if not hasCycleTrackerTest:
			cls.add_additional_test(cls._HasCycleTrackerTest())

		if not hasTookPillRecentlyTest:
			cls.add_additional_test(cls._TookPillRecentlyTest())

class TakePillInteraction(_TakePillInteractionBase):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			TakePillInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class TakePillWickedWhimsInteraction(_TakePillInteractionBase):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			TakePillWickedWhimsInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

	@classmethod
	def RegisterToObjects (cls) -> None:
		"""
		Add this interaction to the appropriate objects.
		"""

		super().RegisterToObjects()

		if WickedWhims.ModInstalled() and WickedWhims.CyclePatchEnabled("AddTakeBirthControlPillInteraction"):
			objectManager = services.get_instance_manager(resources.Types.OBJECT)  # type: definition_manager.DefinitionManager

			wickedWhimsPillsObjectKey = resources.get_resource_key(WickedWhims.WickedWhimsBirthControlPillsObjectID, resources.Types.OBJECT)
			wickedWhimsPillsObject = objectManager.types.get(wickedWhimsPillsObjectKey, None)  # type: typing.Optional[typing.Any]

			if wickedWhimsPillsObject is None:
				Debug.Log("Could not find Wicked Whim's birth control pills object.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				return

			# noinspection PyProtectedMember
			wickedWhimsPillsObject._super_affordances += (cls, )

class ReadInstructionsInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			ReadInstructionsInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

	@classmethod
	def RegisterToObjects (cls) -> None:
		"""
		Add this interaction to the appropriate objects.
		"""

		super().RegisterToObjects()

		if WickedWhims.ModInstalled() and WickedWhims.CyclePatchEnabled("AddReadBirthControlPillInstructionsInteraction"):
			objectManager = services.get_instance_manager(resources.Types.OBJECT)  # type: definition_manager.DefinitionManager

			wickedWhimsPillsObjectKey = resources.get_resource_key(WickedWhims.WickedWhimsBirthControlPillsObjectID, resources.Types.OBJECT)
			wickedWhimsPillsObject = objectManager.types.get(wickedWhimsPillsObjectKey, None)  # type: typing.Optional[typing.Any]

			if wickedWhimsPillsObject is None:
				Debug.Log("Could not find Wicked Whim's birth control pills object.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				return

			# noinspection PyProtectedMember
			wickedWhimsPillsObject._super_affordances += (cls, )