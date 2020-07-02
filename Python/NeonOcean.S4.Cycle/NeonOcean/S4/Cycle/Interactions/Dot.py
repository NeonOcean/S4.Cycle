from __future__ import annotations

import enum_lib
import typing

import interactions
from NeonOcean.S4.Cycle import Dot, Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Main import Debug, This
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from NeonOcean.S4.Main.Tools import Tunable as ToolsTunable, Python
from event_testing import results, test_base
from interactions.base import immediate_interaction
from sims import sim_info
from sims4.tuning import tunable

DownloadInteractions = list()  # type: typing.List[typing.Type[DownloadInteraction]]
DeleteInteractions = list()  # type: typing.List[typing.Type[DeleteInteraction]]
CheckStatusInteractions = list()  # type: typing.List[typing.Type[CheckStatusInteraction]]

class _DotAppInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	class DotAppState(enum_lib.IntEnum):
		Enabled = 1  # type: _DotAppInteraction.DotAppState
		Disabled = 2  # type: _DotAppInteraction.DotAppState

	class DotAppStateTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self, affordance: typing.Type[_DotAppInteraction], actors: typing.Tuple[sim_info.SimInfo, ...]):
			if affordance is None:
				return results.TestResult(False)

			if not issubclass(affordance, _DotAppInteraction):
				return results.TestResult(False)

			if len(actors) == 0:
				Debug.Log("Dot app state test recived an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
				return results.TestResult(False)

			targetSimInfo = actors[0]  # type: sim_info.SimInfo

			dotInformation = Dot.GetDotInformation(targetSimInfo)  # type: typing.Optional[Dot.DotInformation]

			if dotInformation is None:
				Debug.Log("Missing dot information for a sim with the id '%s'." % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = targetSimInfo)
				return results.TestResult(False)

			if affordance.RequiredDotAppState is None:
				return results.TestResult(True)
			if affordance.RequiredDotAppState == affordance.DotAppState.Enabled:
				return results.TestResult(dotInformation.Enabled)
			else:
				return results.TestResult(not dotInformation.Enabled)

		def get_expected_args (self) -> dict:
			return {
				"affordance": interactions.ParticipantType.Affordance,
				"actors": interactions.ParticipantType.Actor
			}

	class DotTrackerModeTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self, affordance: typing.Type[_DotAppInteraction], actors: typing.Tuple[sim_info.SimInfo, ...]):
			if affordance is None:
				return results.TestResult(False)

			if not issubclass(affordance, _DotAppInteraction):
				return results.TestResult(False)

			if len(actors) == 0:
				Debug.Log("Dot app state test recived an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			targetSimInfo = actors[0]  # type: sim_info.SimInfo

			dotInformation = Dot.GetDotInformation(targetSimInfo)  # type: typing.Optional[Dot.DotInformation]

			if dotInformation is None:
				Debug.Log("Missing dot information for a sim with the id '%s'." % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = targetSimInfo)
				return results.TestResult(False)

			if affordance.RequiredDotTrackingMode is None:
				return results.TestResult(True)
			else:
				return results.TestResult(dotInformation.TrackingMode == affordance.RequiredDotTrackingMode)

		def get_expected_args (self) -> dict:
			return {
				"affordance": interactions.ParticipantType.Affordance,
				"actors": interactions.ParticipantType.Actor
			}

	class HasCycleTrackerTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self, actors: typing.Tuple[sim_info.SimInfo, ...]):
			if len(actors) == 0:
				Debug.Log("Has cycle tracker test recived an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			targetSimInfo = actors[0]  # type: sim_info.SimInfo

			targetSimSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

			if targetSimSystem is None:
				return results.TestResult(False)

			return results.TestResult(targetSimSystem.HasTracker(FemalesShared.CycleTrackerIdentifier))

		def get_expected_args (self) -> dict:
			return {
				"actors": interactions.ParticipantType.Actor
			}

	INSTANCE_TUNABLES = {
		"RequiredDotAppState": tunable.OptionalTunable(description = "The state a sim needs the dot app be in to use this interaction. If this is left disabled we will assume all states are valid.", tunable = ToolsTunable.TunablePythonEnumEntry(enumType = DotAppState, default = DotAppState.Enabled)),
		"RequiredDotTrackingMode": tunable.OptionalTunable(description = "The tracking mode a sim needs the dot app be in to use this interaction. If this is left disabled we will assume all tracking modes are valid.", tunable = ToolsTunable.TunablePythonEnumEntry(enumType = Dot.TrackingMode, default = Dot.TrackingMode.Cycle)),
	}

	RequiredDotAppState: typing.Optional[DotAppState]
	RequiredDotTrackingMode: typing.Optional[Dot.TrackingMode]

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		hasDotAppStateTest = False  # type: bool
		hasDotTrackerModeTest = False  # type: bool
		hasHasCycleTrackerTest = False  # type: bool

		if cls._additional_tests is not None:
			for additionalTest in reversed(cls._additional_tests):
				if not hasDotAppStateTest and isinstance(additionalTest, cls.DotAppStateTest):
					hasDotAppStateTest = True
				elif not hasDotTrackerModeTest and isinstance(additionalTest, cls.DotTrackerModeTest):
					hasDotTrackerModeTest = True
				elif not hasHasCycleTrackerTest and isinstance(additionalTest, cls.HasCycleTrackerTest):
					hasHasCycleTrackerTest = True

		if not hasDotAppStateTest:
			cls.add_additional_test(cls.DotAppStateTest())

		if not hasDotTrackerModeTest:
			cls.add_additional_test(cls.DotTrackerModeTest())

		if not hasHasCycleTrackerTest:
			cls.add_additional_test(cls.HasCycleTrackerTest())

class DownloadInteraction(_DotAppInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			DownloadInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class DeleteInteraction(_DotAppInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			DeleteInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class CheckStatusInteraction(_DotAppInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			CheckStatusInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e
