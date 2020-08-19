from __future__ import annotations

import typing

import interactions
from NeonOcean.S4.Cycle import Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Main import Debug, This
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from event_testing import results, test_base
from interactions.base import immediate_interaction
from sims import sim_info

TakePillInteractions = list()  # type: typing.List[typing.Type[TakePillInteraction]]
ReadInstructionsInteractions = list()  # type: typing.List[typing.Type[ReadInstructionsInteraction]]

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

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		hasCycleTrackerTest = False  # type: bool

		if cls._additional_tests is not None:
			for additionalTest in reversed(cls._additional_tests):
				if isinstance(additionalTest, cls._HasCycleTrackerTest):
					hasCycleTrackerTest = True

		if not hasCycleTrackerTest:
			cls.add_additional_test(cls._HasCycleTrackerTest())

class TakePillInteraction(_TakePillInteractionBase):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			TakePillInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class ReadInstructionsInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			ReadInstructionsInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e
