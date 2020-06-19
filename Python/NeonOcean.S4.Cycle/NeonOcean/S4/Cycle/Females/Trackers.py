from NeonOcean.S4.Cycle.Females import CycleTracker, OvumTracker, PregnancyTracker, SpermTracker
from NeonOcean.S4.Cycle import ReproductionTrackers
from NeonOcean.S4.Main import LoadingShared

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ReproductionTrackers.RegisterTrackerType(CycleTracker.CycleTracker.TypeIdentifier, CycleTracker.CycleTracker)
	ReproductionTrackers.RegisterTrackerType(OvumTracker.OvumTracker.TypeIdentifier, OvumTracker.OvumTracker)
	ReproductionTrackers.RegisterTrackerType(PregnancyTracker.PregnancyTracker.TypeIdentifier, PregnancyTracker.PregnancyTracker)
	ReproductionTrackers.RegisterTrackerType(SpermTracker.SpermTracker.TypeIdentifier, SpermTracker.SpermTracker)
