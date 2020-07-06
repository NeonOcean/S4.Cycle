from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Debug, This
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from interactions.base import super_interaction
from event_testing import results, test_base

TakePregnancyTestInteractions = list()  # type: typing.List[typing.Type[TakePregnancyTestInteraction]]
ReadInstructionsInteractions = list()  # type: typing.List[typing.Type[ReadInstructionsInteraction]]

class TakePregnancyTestInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, super_interaction.SuperInteraction):
	EnablingMethodUse = False  # type: bool

	class DisabledTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self):
			return results.TestResult(False)

		def get_expected_args (self) -> dict:
			pass

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			TakePregnancyTestInteractions.append(cls)

			cls.add_additional_test(cls.DisabledTest())

		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class ReadInstructionsInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, super_interaction.SuperInteraction):
	EnablingMethodUse = False  # type: bool

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			ReadInstructionsInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e
