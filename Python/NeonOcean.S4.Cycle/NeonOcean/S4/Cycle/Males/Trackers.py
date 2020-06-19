from NeonOcean.S4.Cycle.Males import SpermProductionTracker
from NeonOcean.S4.Cycle import ReproductionTrackers
from NeonOcean.S4.Main import LoadingShared

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ReproductionTrackers.RegisterTrackerType(SpermProductionTracker.SpermProductionTracker.TypeIdentifier, SpermProductionTracker.SpermProductionTracker)
