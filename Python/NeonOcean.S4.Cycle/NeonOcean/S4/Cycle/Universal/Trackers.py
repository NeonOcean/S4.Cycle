from NeonOcean.S4.Cycle import ReproductionTrackers
from NeonOcean.S4.Cycle.Universal import EffectTracker, HandlerTracker
from NeonOcean.S4.Main import LoadingShared

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ReproductionTrackers.RegisterTrackerType(EffectTracker.EffectTracker.TypeIdentifier, EffectTracker.EffectTracker)
	ReproductionTrackers.RegisterTrackerType(HandlerTracker.HandlerTracker.TypeIdentifier, HandlerTracker.HandlerTracker)
