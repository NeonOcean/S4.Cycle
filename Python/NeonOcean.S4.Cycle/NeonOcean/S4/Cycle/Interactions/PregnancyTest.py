from __future__ import annotations

import typing

import singletons
from NeonOcean.S4.Cycle import Settings, This
from NeonOcean.S4.Main import Debug, This
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from NeonOcean.S4.Main.Tools import Patcher
from event_testing import results
from interactions.base import basic, immediate_interaction, interaction, super_interaction
from interactions.payment import payment_element, payment_source
from interactions.utils import interaction_elements
from objects import object_tests
from objects.components import inventory_elements

TakePregnancyTestInteractions = list()  # type: typing.List[typing.Type[TakePregnancyTestInteraction]]
TakePregnancyTestStallInteractions = list()  # type: typing.List[typing.Type[TakePregnancyTestStallInteraction]]
ReadInstructionsInteractions = list()  # type: typing.List[typing.Type[ReadInstructionsInteraction]]

class _TakePregnancyTestInteractionBase(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, super_interaction.SuperInteraction):
	class _SettingDependentInventoryTest(object_tests.InventoryTest):
		def __call__ (self, *args, **kwargs):
			if not Settings.PregnancyTestRequiresItem.Get():
				return results.TestResult(True)

			superResults = super().__call__(*args, **kwargs)

			return superResults

	class _SettingDependentPaymentElement(payment_element.PaymentElement):
		def _do_behavior (self):
			if Settings.PregnancyTestRequiresItem.Get():
				return True
			else:
				return super()._do_behavior()

		@classmethod
		def on_affordance_loaded_callback (cls, affordance: interaction.Interaction, paymentElement: payment_element.PaymentElement, object_tuning_id = singletons.DEFAULT):
			# noinspection PyUnresolvedReferences
			paymentElementPayment = paymentElement.payment
			Patcher.Patch(paymentElementPayment, "get_simoleon_delta", cls._PaymentGetSimoleonDeltaPatch, patchType = Patcher.PatchTypes.Custom)
			super().on_affordance_loaded_callback(affordance, paymentElement, object_tuning_id = object_tuning_id)

		@staticmethod
		def _PaymentGetSimoleonDeltaPatch (originalCallable: typing.Callable, *args, **kwargs) -> typing.Any:
			if Settings.PregnancyTestRequiresItem.Get():
				# noinspection PyProtectedMember
				return 0, payment_source._PaymentSourceHousehold()
			else:
				return originalCallable(*args, **kwargs)

	class _SettingDependentDestroyObjectsInInventoryElement(inventory_elements.DestroySpecifiedObjectsFromTargetInventory):
		def _do_behavior (self):
			if not Settings.PregnancyTestRequiresItem.Get():
				return True
			else:
				return super()._do_behavior()

	INSTANCE_TUNABLES = {
		"ItemRequiredDestroyObjectsInInventoryElement": _SettingDependentDestroyObjectsInInventoryElement.TunableFactory(description = "The destroy specified objects from target inventory element to be used if an item is required if an item is required for this interaction."),
		"NoRequiredItemPaymentElement": _SettingDependentPaymentElement.TunableFactory(description = "The payment element to be added as a basic extra if an item is not required for this interaction."),

		"ItemRequiredInventoryTest": _SettingDependentInventoryTest.TunableFactory()
	}

	ItemRequiredDestroyObjectsInInventoryElement: typing.Any
	NoRequiredItemPaymentElement: typing.Any

	ItemRequiredInventoryTest: typing.Any

	@classmethod
	def _tuning_loaded_callback (cls):
		super()._tuning_loaded_callback()

		cls.add_additional_test(cls.ItemRequiredInventoryTest)

		if hasattr(cls.ItemRequiredDestroyObjectsInInventoryElement.factory, basic.AFFORDANCE_LOADED_CALLBACK_STR):
			cls.ItemRequiredDestroyObjectsInInventoryElement.factory.on_affordance_loaded_callback(cls, cls.ItemRequiredDestroyObjectsInInventoryElement)

		if hasattr(cls.NoRequiredItemPaymentElement.factory, basic.AFFORDANCE_LOADED_CALLBACK_STR):
			cls.NoRequiredItemPaymentElement.factory.on_affordance_loaded_callback(cls, cls.NoRequiredItemPaymentElement)

		cls.add_additional_basic_extra(cls.ItemRequiredDestroyObjectsInInventoryElement)
		cls.add_additional_basic_extra(cls.NoRequiredItemPaymentElement)

	@classmethod
	def _verify_tuning_callback (cls):
		if isinstance(cls.ItemRequiredDestroyObjectsInInventoryElement.factory, interaction_elements.XevtTriggeredElement):
			cls.ItemRequiredDestroyObjectsInInventoryElement.factory.validate_tuning_interaction(cls, cls.ItemRequiredDestroyObjectsInInventoryElement)

		if isinstance(cls.NoRequiredItemPaymentElement.factory, interaction_elements.XevtTriggeredElement):
			cls.NoRequiredItemPaymentElement.factory.validate_tuning_interaction(cls, cls.NoRequiredItemPaymentElement)

class TakePregnancyTestInteraction(_TakePregnancyTestInteractionBase):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			TakePregnancyTestInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

class TakePregnancyTestStallInteraction(_TakePregnancyTestInteractionBase):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)
			TakePregnancyTestStallInteractions.append(cls)
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
