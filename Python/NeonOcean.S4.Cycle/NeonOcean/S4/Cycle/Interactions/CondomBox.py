from __future__ import annotations

import typing

import interactions
import services
import snippets
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Safety import WoohooSafety
from NeonOcean.S4.Cycle.Mods import WickedWhims
from NeonOcean.S4.Main import Debug, This
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration, DisableInteraction
from event_testing import results, test_base
from interactions.base import immediate_interaction
from sims import sim, sim_info
from sims4 import resources
from sims4.tuning import tunable

StartUsingInteractions = list()  # type: typing.List[typing.Type[StartUsingInteraction]]
StopUsingInteractions = list()  # type: typing.List[typing.Type[StopUsingInteraction]]
UnpackInteractions = list()  # type: typing.List[typing.Type[UnpackInteraction]]

class _ChangeUseStateInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	class MethodUseTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self, affordance: typing.Type[_ChangeUseStateInteraction], actors: typing.Tuple[sim_info.SimInfo, ...]):
			if affordance is None:
				return results.TestResult(False)

			if not issubclass(affordance, _ChangeUseStateInteraction):
				return results.TestResult(False)

			if len(actors) == 0:
				Debug.Log("Method use test recived an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			if not isinstance(affordance.WoohooSafetyMethod.value, WoohooSafety.WoohooSafetyMethod):
				Debug.Log("Change use state interaction value 'WoohooSafetyMethod' did not point to a valid woohoo safety method snippet.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			if WoohooSafety.IsUsingWoohooSafetyMethod(affordance.WoohooSafetyMethod.value, actors[0]):
				if affordance.EnablingMethodUse:
					return results.TestResult(False)
			else:
				if not affordance.EnablingMethodUse:
					return results.TestResult(False)

			return results.TestResult.TRUE

		def get_expected_args (self) -> dict:
			# noinspection SpellCheckingInspection
			return {
				"affordance": interactions.ParticipantType.Affordance,
				"actors": interactions.ParticipantType.Actor
			}

	EnablingMethodUse = True  # type: bool

	INSTANCE_TUNABLES = {
		"WoohooSafetyMethod": tunable.TunableReference(description = "The woohoo safety method that this interaction is changing the use state of.", manager = services.get_instance_manager(resources.Types.SNIPPET))
	}

	WoohooSafetyMethod: snippets.SnippetInstanceMetaclass

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		hasMethodUseTest = False  # type: bool

		if cls._additional_tests is not None:
			for additionalTest in reversed(cls._additional_tests):
				if isinstance(additionalTest, cls.MethodUseTest):
					hasMethodUseTest = True

		if not hasMethodUseTest:
			cls.add_additional_test(cls.MethodUseTest())

	def OnStarted (self) -> None:
		actor = self.get_participant()

		if actor is None:
			return

		if isinstance(actor, sim.Sim):
			actor = actor.sim_info

		WoohooSafety.SetIsUsingWoohooSafetyMethod(self.WoohooSafetyMethod.value, actor, self.EnablingMethodUse)

class StartUsingInteraction(_ChangeUseStateInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			StartUsingInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class StopUsingInteraction(_ChangeUseStateInteraction):
	EnablingMethodUse = False  # type: bool

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			StopUsingInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class UnpackInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	EnablingMethodUse = False  # type: bool

	def __init_subclass__ (cls, *args, **kwargs):
		"""
		Used when WickedWhims is installed.
		"""

		try:
			super().__init_subclass__(*args, **kwargs)

			if not WickedWhims.ModInstalled() or not WickedWhims.CyclePatchEnabled("AddUnpackCondomBoxInteraction"):
				if cls._additional_tests is not None:
					for additionalTest in reversed(cls._additional_tests):
						if isinstance(additionalTest, DisableInteraction.DisabledInteractionTest):
							return

				cls.add_additional_test(DisableInteraction.DisabledInteractionTest())
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e
