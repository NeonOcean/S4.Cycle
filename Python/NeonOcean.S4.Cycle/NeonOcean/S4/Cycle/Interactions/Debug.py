from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Interactions.Support import Debug as SupportDebug
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from interactions.base import immediate_interaction, picker_interaction

ShowReproductiveInfoInteractions = list()  # type: typing.List[typing.Type[ShowReproductiveInfoInteraction]]
AddSpermPickerInteractions = list()  # type: typing.List[typing.Type[AddSpermPickerInteraction]]
AddSpermInteractions = list()  # type: typing.List[typing.Type[AddSpermInteraction]]
ClearSpermInteractions = list()  # type: typing.List[typing.Type[ClearSpermInteraction]]
AddOvumInteractions = list()  # type: typing.List[typing.Type[AddOvumInteraction]]
ClearOvaInteractions = list()  # type: typing.List[typing.Type[ClearOvaInteraction]]
MakePregnantPickerInteractions = list()  # type: typing.List[typing.Type[MakePregnantPickerInteraction]]
MakePregnantInteractions = list()  # type: typing.List[typing.Type[MakePregnantInteraction]]
EndPregnancyInteractions = list()  # type: typing.List[typing.Type[EndPregnancyInteraction]]

class ShowReproductiveInfoInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			ShowReproductiveInfoInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

# noinspection PyAbstractClass
class AddSpermPickerInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, picker_interaction.SimPickerInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			AddSpermPickerInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class AddSpermInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			AddSpermInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class ClearSpermInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			ClearSpermInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class AddOvumInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			AddOvumInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class ClearOvaInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			ClearOvaInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

# noinspection PyAbstractClass
class MakePregnantPickerInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, picker_interaction.SimPickerInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			MakePregnantPickerInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class MakePregnantInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			MakePregnantInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class EndPregnancyInteraction(SupportDebug.DebugExtension, Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			EndPregnancyInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e
