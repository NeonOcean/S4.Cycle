from __future__ import annotations

import typing

import services
import tag
from NeonOcean.S4.Cycle import Insemination, Settings, This
from NeonOcean.S4.Main import Debug, Director
from NeonOcean.S4.Main.Tools import Parse, Patcher
from interactions.base import interaction
from interactions.utils import death, interaction_elements
from sims import sim, sim_info
from sims.pregnancy import pregnancy_element
from sims4 import resources
from sims4.tuning import instance_manager

# noinspection SpellCheckingInspection
_addAccidentElementInteractionIDs = {
	233893,  # dumpster_DiveForThrills_WooHoo
	207257,  # IslandWaterfall_Woohoo
	200300,  # SleepingPod_Woohoo
	193414,  # WalkInSafe_Woohoo
	185490,  # LeafPile_Woohoo
	172276,  # lighthouse_WooHoo
	140975,  # woohoo_Autonomous_RocketShip_Festival_LogicFair
	152810,  # vampire_BatWoohoo_Target
	152769,  # vampire_BatWoohoo
	154858,  # coffin_WooHoo
	123397,  # WooHoo_Closet
	117777,  # hottub_WooHoo
	119531,  # steamRoom_WooHoo
	125228,  # bush_wooHoo
	104135,  # Tent_WooHoo
	13914,  # rocketShip_WooHoo
	13099,  # bed_woohoo
	14387,  # telescope_WooHoo
}  # type: typing.Set[int]  # TODO create automatic detection instead?

class WoohooAccidentElement(interaction_elements.XevtTriggeredElement):
	def _do_behavior (self):
		try:
			handleWoohoo = Settings.EnableWoohooChanges.Get()  # type: bool
			woohooIsAlwaysSafe = Settings.WoohooIsAlwaysSafe.Get()  # type: bool

			if not handleWoohoo:
				return

			inseminatedSim = self.interaction.get_participant(interaction.ParticipantTypeSingleSim.Actor)  # type: sim.Sim

			if inseminatedSim is None or not inseminatedSim.household.free_slot_count:
				return

			if death.get_death_interaction(inseminatedSim) is not None:
				return

			inseminatedSimInfo = inseminatedSim.sim_info  # type: sim_info.SimInfo

			sourceSim = self.interaction.get_participant(interaction.ParticipantTypeSingleSim.TargetSim)  # type: sim.Sim

			if sourceSim is None:
				return

			sourceSimInfo = sourceSim.sim_info  # type: sim_info.SimInfo

			if woohooIsAlwaysSafe:
				arrivingSpermPercentage = 0  # type: typing.Optional[int]
			else:
				arrivingSpermPercentage = None  # type: typing.Optional[int]

			Insemination.AutoInseminate(inseminatedSimInfo, sourceSimInfo, tryingForBaby = False, arrivingSpermPercentage = arrivingSpermPercentage)
		except Exception as e:
			Debug.Log("Failed to handle accidental insemination for a woohoo interaction.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

class _Announcer(Director.Announcer):
	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager) -> None:
		if instanceManager.TYPE != resources.Types.INTERACTION:
			return

		_PrepareWoohooInteractions()

def _Setup () -> None:
	_PatchPregnancyElement()
	
def _PatchPregnancyElement() -> None:
	Patcher.Patch(pregnancy_element.PregnancyElement, "_run", PregnancyElementShouldDoBehaviourPatch, patchType = Patcher.PatchTypes.Custom)
	Patcher.Patch(pregnancy_element.PregnancyElement, "_behavior_element", PregnancyElementShouldDoBehaviourPatch, patchType = Patcher.PatchTypes.Custom)
	Patcher.Patch(pregnancy_element.PregnancyElement, "_behavior_event_handler", PregnancyElementShouldDoBehaviourPatch, patchType = Patcher.PatchTypes.Custom)
	Patcher.Patch(pregnancy_element.PregnancyElement, "_do_behavior", PregnancyElementDoBehaviorPatch, patchType = Patcher.PatchTypes.Custom)

def _PrepareWoohooInteractions () -> None:
	_AddAccidentElements()

def _AddAccidentElements () -> None:
	interactionManager = services.get_instance_manager(resources.Types.INTERACTION)  # type: instance_manager.InstanceManager

	for woohooInteractionKey, woohooInteraction in interactionManager.types.items():  # type: typing.Any, interaction.Interaction
		if woohooInteractionKey.instance in _addAccidentElementInteractionIDs:
			accidentElement = WoohooAccidentElement.TunableFactory().default

			woohooInteraction.add_additional_basic_extra(accidentElement)

def _WoohooIsTryingForBaby (woohooInteraction: interaction.Interaction) -> bool:
	tryForBabyTag = Parse.ParseS4Enum("Interaction_TryForBaby", tag.Tag)

	if tryForBabyTag in woohooInteraction.interaction_category_tags:
		return True

	return False

# noinspection PyUnusedLocal
def PregnancyElementShouldDoBehaviourPatch (originalCallable: typing.Callable, self: pregnancy_element.PregnancyElement, *args, **kwargs) -> typing.Any:
	handleWoohoo = False  # type: bool

	try:
		if Settings.EnableWoohooChanges.Get():
			handleWoohoo = True
	except:
		pass

	if not handleWoohoo:
		originalCallable(self, *args, **kwargs)
	else:
		originallyDoingBehavior = self._should_do_behavior  # type: bool
		self._should_do_behavior = True
		originalCallable(self, *args, **kwargs)
		self._should_do_behavior = originallyDoingBehavior

def PregnancyElementDoBehaviorPatch (originalCallable: typing.Callable, self: pregnancy_element.PregnancyElement, *args, **kwargs) -> typing.Any:
	# The do behaviour seems to be called twice, the first and second calls have different sims as their subject.

	handleWoohoo = False  # type: bool

	try:
		if Settings.EnableWoohooChanges.Get():
			handleWoohoo = True
	except:
		pass

	if not handleWoohoo:
		if self._should_do_behavior:
			return originalCallable(self, *args, **kwargs)
	else:
		try:
			# noinspection PyUnresolvedReferences
			inseminatedSim = self.interaction.get_participant(self.pregnancy_subject)  # type: sim.Sim

			if inseminatedSim is None or not inseminatedSim.household.free_slot_count:
				return

			if death.get_death_interaction(inseminatedSim) is not None:
				return

			inseminatedSimInfo = inseminatedSim.sim_info  # type: sim_info.SimInfo

			# noinspection PyUnresolvedReferences
			sourceSimInfo = self.pregnancy_parent.get_parent(self.interaction, inseminatedSimInfo)  # type: sim_info.SimInfo

			if sourceSimInfo is None:
				return

			Insemination.AutoInseminate(inseminatedSimInfo, sourceSimInfo, tryingForBaby = _WoohooIsTryingForBaby(self.interaction))
		except Exception as e:
			Debug.Log("Failed to handle insemination for a woohoo interaction.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

_Setup()
