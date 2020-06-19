
from NeonOcean.S4.Cycle import ReproductionShared

EffectTrackerIdentifier = "EffectTracker"  # type: str
HandlerTrackerIdentifier = "HandlerTracker"  # type: str

def GetEffectTrackerReproductiveTimeMultiplier () -> float:
	return ReproductionShared.GetGeneralReproductiveTimeMultiplier()

def GetHandlerTrackerReproductiveTimeMultiplier () -> float:
	return ReproductionShared.GetGeneralReproductiveTimeMultiplier()