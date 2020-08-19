from __future__ import annotations

from NeonOcean.S4.Main import Director
from NeonOcean.S4.Main.Interactions.Support import DisableInteraction
from interactions.base import interaction
from sims4 import resources
from sims4.tuning import instance_manager

TakePregnancyTestInteractionID = 14434  # type: int
TakePregnancyTestStallInteractionID = 214057  # type: int

class _Announcer(Director.Announcer):
	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager) -> None:
		if instanceManager.TYPE != resources.Types.INTERACTION:
			return

		for testingInteraction in instanceManager.types.values():  # type: interaction.Interaction
			if testingInteraction.guid64 == TakePregnancyTestInteractionID or \
					testingInteraction.guid64 == TakePregnancyTestStallInteractionID:

				_PatchPregnancyTestInteraction(testingInteraction)

def _PatchPregnancyTestInteraction (testInteraction: interaction.Interaction) -> None:
	testInteraction.add_additional_test(DisableInteraction.DisabledInteractionTest())
