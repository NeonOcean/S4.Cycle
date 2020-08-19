from __future__ import annotations

import typing

import interactions
from NeonOcean.S4.Cycle import Dot, Reproduction, ReproductionShared, This
from NeonOcean.S4.Cycle.Females import Shared as FemalesShared
from NeonOcean.S4.Main import Debug, This
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from NeonOcean.S4.Main.Tools import Python, Tunable as ToolsTunable
from event_testing import results, test_base
from interactions.base import immediate_interaction
from sims import sim_info
from sims4.tuning import tunable

DownloadInteractions = list()  # type: typing.List[typing.Type[DownloadInteraction]]
DeleteInteractions = list()  # type: typing.List[typing.Type[DeleteInteraction]]
CheckStatusInteractions = list()  # type: typing.List[typing.Type[CheckStatusInteraction]]
EnableFertilityNotificationsInteractions = list()  # type: typing.List[typing.Type[EnableFertilityNotificationsInteraction]]
DisableFertilityNotificationsInteractions = list()  # type: typing.List[typing.Type[DisableFertilityNotificationsInteraction]]

class _DotAppInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	class DotEnabledStateTest(test_base.BaseTest):
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

			if affordance.RequiredDotEnabledState is None:
				return results.TestResult(True)
			else:
				return results.TestResult(dotInformation.Enabled == affordance.RequiredDotEnabledState)

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

	class DotShowFertilityNotificationsStateTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self, affordance: typing.Type[_DotAppInteraction], actors: typing.Tuple[sim_info.SimInfo, ...]):
			if affordance is None:
				return results.TestResult(False)

			if not issubclass(affordance, _DotAppInteraction):
				return results.TestResult(False)

			if len(actors) == 0:
				Debug.Log("Dot app notify of fertility test recived an empty actors parameter.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return results.TestResult(False)

			targetSimInfo = actors[0]  # type: sim_info.SimInfo

			dotInformation = Dot.GetDotInformation(targetSimInfo)  # type: typing.Optional[Dot.DotInformation]

			if dotInformation is None:
				Debug.Log("Missing dot information for a sim with the id '%s'." % targetSimInfo.id, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockReference = targetSimInfo)
				return results.TestResult(False)

			if affordance.RequiredDotShowFertilityNotificationsState is None:
				return results.TestResult(True)
			else:
				return results.TestResult(dotInformation.ShowFertilityNotifications == affordance.RequiredDotShowFertilityNotificationsState)

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
		"RequiredDotEnabledState": tunable.OptionalTunable(description = "If this is true, the sim needs to have the dot app installed for this interaction to appear. If false, it will appear if not installed. This can be left disabled to imply all states are valid.", tunable = tunable.Tunable(tunable_type = bool, default = True)),
		"RequiredDotTrackingMode": tunable.OptionalTunable(description = "The tracking mode a sim needs the dot app be in to use this interaction. If this is left disabled we will assume all tracking modes are valid.", tunable = ToolsTunable.TunablePythonEnumEntry(enumType = Dot.TrackingMode, default = Dot.TrackingMode.Cycle)),
		"RequiredDotShowFertilityNotificationsState": tunable.OptionalTunable(description = "If this is true, the sim needs to be getting fertility notifications for this interaction to appear. If false, it will appear if they are not getting fertility notifications. This can be left disabled to imply all states are valid.", tunable = tunable.Tunable(tunable_type = bool, default = False))
	}

	RequiredDotEnabledState: typing.Optional[bool]
	RequiredDotTrackingMode: typing.Optional[Dot.TrackingMode]
	RequiredDotShowFertilityNotificationsState: typing.Optional[bool]

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		hasDotEnabledStateTest = False  # type: bool
		hasDotTrackerModeTest = False  # type: bool
		hasDotShowFertilityNotificationsStateTest = False  # type: bool
		hasHasCycleTrackerTest = False  # type: bool

		if cls._additional_tests is not None:
			for additionalTest in reversed(cls._additional_tests):
				if not hasDotEnabledStateTest and isinstance(additionalTest, cls.DotEnabledStateTest):
					hasDotEnabledStateTest = True
				elif not hasDotTrackerModeTest and isinstance(additionalTest, cls.DotTrackerModeTest):
					hasDotTrackerModeTest = True
				elif not hasDotShowFertilityNotificationsStateTest and isinstance(additionalTest, cls.DotShowFertilityNotificationsStateTest):
					hasDotTrackerModeTest = True
				elif not hasHasCycleTrackerTest and isinstance(additionalTest, cls.HasCycleTrackerTest):
					hasHasCycleTrackerTest = True

		if not hasDotEnabledStateTest:
			cls.add_additional_test(cls.DotEnabledStateTest())

		if not hasDotTrackerModeTest:
			cls.add_additional_test(cls.DotTrackerModeTest())

		if not hasDotShowFertilityNotificationsStateTest:
			cls.add_additional_test(cls.DotShowFertilityNotificationsStateTest())

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

class EnableFertilityNotificationsInteraction(_DotAppInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			EnableFertilityNotificationsInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class DisableFertilityNotificationsInteraction(_DotAppInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			DisableFertilityNotificationsInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e
