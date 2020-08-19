from __future__ import annotations, annotations

import typing

from NeonOcean.S4.Cycle import Reproduction, ReproductionShared
from NeonOcean.S4.Cycle.Effects import EmergencyContraceptivePill as EffectsEmergencyContraceptivePill, Shared as EffectsShared
from NeonOcean.S4.Cycle.Universal import EffectTracker, Shared as UniversalShared
from NeonOcean.S4.Main.Tools import Exceptions
from objects import script_object
from sims import sim_info

def TakePill (
		targetSimInfo: sim_info.SimInfo,
		pillsObject: typing.Optional[script_object.ScriptObject],
		requiresPill: bool = True,
		removePill: bool = True,
		showGeneralFeedback: bool = True) -> bool:
	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	if not isinstance(pillsObject, script_object.ScriptObject) and pillsObject is not None:
		raise Exceptions.IncorrectTypeException(pillsObject, "pillsObject", (script_object.ScriptObject, None))

	if not isinstance(requiresPill, bool):
		raise Exceptions.IncorrectTypeException(requiresPill, "requiresPill", (bool,))

	if not isinstance(removePill, bool):
		raise Exceptions.IncorrectTypeException(removePill, "removePill", (bool,))

	if pillsObject is None and (requiresPill or removePill):
		raise ValueError("The 'pillsObject' parameter cannot be none if the requires pill or remove pill parameters are true.")

	if not isinstance(showGeneralFeedback, bool):
		raise Exceptions.IncorrectTypeException(showGeneralFeedback, "showGeneralFeedback", (bool,))

	targetSystem = Reproduction.GetSimSystem(targetSimInfo)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

	if targetSystem is None:
		return False

	effectTracker = targetSystem.GetTracker(UniversalShared.EffectTrackerIdentifier)  # type: typing.Optional[EffectTracker.EffectTracker]

	if effectTracker is None:
		return False

	emergencyContraceptivePillEffect = effectTracker.GetEffect(EffectsShared.EmergencyContraceptivePillEffectTypeIdentifier)  # type: typing.Optional[EffectsEmergencyContraceptivePill.EmergencyContraceptivePillEffect]

	if emergencyContraceptivePillEffect is None:
		return False

	emergencyContraceptivePillEffect.NotifyOfTakenPill()

	if removePill:
		pillsObject.destroy()
