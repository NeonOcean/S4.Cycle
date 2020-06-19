from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This, Settings
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Interactions.Support import Dependent, Events, Registration
from event_testing import results, test_base
from interactions.base import picker_interaction
from sims4.tuning import tunable, tunable_base
from ui import ui_dialog_notification

PurchaseWithComputerInteractions = list()  # type: typing.List[typing.Type[PurchaseWithComputerInteraction]]
PurchaseWithMailboxInteractions = list()  # type: typing.List[typing.Type[PurchaseWithMailboxInteraction]]

# noinspection PyAbstractClass
class _PurchaseWithInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, picker_interaction.PurchasePickerInteraction):
	DependentMod = This.Mod

	REMOVE_INSTANCE_TUNABLES = ("delivery_method",)

	INSTANCE_TUNABLES = {
		"MailDelivery": picker_interaction.MailmanDelivery(description = "The delivery method to be used when the immediate contraceptive arrival setting is false."),
		"MailDeliveryNotification": tunable.OptionalTunable(description = "A notification to be show when a purchase is made. This notification will be the one to appear if the immediate contraceptive arrival setting is false.", tunable = ui_dialog_notification.TunableUiDialogNotificationSnippet(), tuning_group = tunable_base.GroupNames.PICKERTUNING),
		
		"InventoryDelivery": picker_interaction.PurchaseToInventory(description = "The delivery method to be used when the immediate contraceptive arrival setting is true."),
		"InventoryDeliveryNotification": tunable.OptionalTunable(description = "A notification to be show when a purchase is made. This notification will be the one to appear if the immediate contraceptive arrival setting is true.", tunable = ui_dialog_notification.TunableUiDialogNotificationSnippet(), tuning_group = tunable_base.GroupNames.PICKERTUNING),
	}

	MailDelivery: typing.Callable
	MailDeliveryNotification: typing.Any

	InventoryDelivery: typing.Callable
	InventoryDeliveryNotification: typing.Any

	class _InteractionEnabledTest(test_base.BaseTest):
		# noinspection SpellCheckingInspection
		def __call__ (self):
			if Settings.ShowPurchaseContraceptivesInteractions.Get():
				return results.TestResult(True)
			else:
				return results.TestResult(False)

		def get_expected_args (self) -> dict:
			return dict()

	def __init_subclass__ (cls, *args, **kwargs):
		cls.add_additional_test(cls._InteractionEnabledTest())

	@property
	def delivery_method (self) -> typing.Any:
		if Settings.ImmediateContraceptiveArrival.Get():
			return self.InventoryDelivery
		else:
			return self.MailDelivery

	@delivery_method.setter
	def delivery_method (self, value: typing.Any) -> None:
		pass

	@property
	def purchase_notification (self) -> typing.Any:
		if Settings.ImmediateContraceptiveArrival.Get():
			return self.InventoryDeliveryNotification
		else:
			return self.MailDeliveryNotification

	@purchase_notification.setter
	def purchase_notification (self, value: typing.Any) -> None:
		pass

# noinspection PyAbstractClass
class PurchaseWithComputerInteraction(_PurchaseWithInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			PurchaseWithComputerInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e

# noinspection PyAbstractClass
class PurchaseWithMailboxInteraction(_PurchaseWithInteraction):
	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			PurchaseWithMailboxInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			raise e