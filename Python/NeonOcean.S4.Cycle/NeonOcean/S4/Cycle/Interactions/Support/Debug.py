from __future__ import annotations

import typing

import interactions
from NeonOcean.S4.Cycle import Settings
from event_testing import results, test_base

DebugInteractions = list()  # type: typing.List[typing.Type[DebugExtension]]

class DebugEnabledTest(test_base.BaseTest):
	# noinspection SpellCheckingInspection
	def __call__ (self, affordance):
		if affordance is None:
			return results.TestResult(False)

		if not issubclass(affordance, DebugExtension):
			return results.TestResult(True)

		if not Settings.DebugMode.Get():
			return results.TestResult(False)

		return results.TestResult(True)

	def get_expected_args (self) -> dict:
		return {
			"affordance": interactions.ParticipantType.Affordance
		}

class DebugExtension:
	DependentOnMod: bool

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		if hasattr(cls, "_additional_tests"):
			if cls._additional_tests is not None:
				for additionalTest in reversed(cls._additional_tests):
					if isinstance(additionalTest, DebugEnabledTest):
						return

		if hasattr(cls, "add_additional_test"):
			cls.add_additional_test(DebugEnabledTest())

		DebugInteractions.append(cls)
