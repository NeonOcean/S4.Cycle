from __future__ import annotations

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Cycle.Saving import LastSimID
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Saving import Save, SaveShared, SectionSims, SectionStandard
from NeonOcean.S4.Main.Tools import Exceptions, Python
from sims import sim_info

_savingObject: SaveShared.Save
_simsSection: SectionSims.SectionSims
_allSimsSection: SectionStandard.SectionStandard

def GetSavingObject () -> SaveShared.Save:
	return _savingObject

def GetSimsSection () -> SectionSims.SectionSims:
	return _simsSection

def GetAllSimsSection () -> SectionStandard.SectionStandard:
	return _allSimsSection

def GetSimSimsSectionBranchKey (targetSimInfo: sim_info.SimInfo) -> str:
	"""
	Get the branch that the target sim has data on in the sims section. If this sim has no saved data, then we will return the sim's id as a string.
	This takes into consideration if the sim has changed their sim id since the last save.
	"""

	if not isinstance(targetSimInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(targetSimInfo, "targetSimInfo", (sim_info.SimInfo,))

	currentSimID = targetSimInfo.id

	try:
		lastSimID = LastSimID.GetLastSimID(targetSimInfo)
	except:
		Debug.Log("Could not retrieve the last sim id for a sim with the current id of '%s'." % currentSimID, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)
		lastSimID = None

	currentSimIDString = str(currentSimID)  # type: str
	lastSimIDString = str(lastSimID)  # type: str

	if lastSimID is None or lastSimID == 0:
		return currentSimIDString

	if lastSimID != currentSimID:
		Debug.Log("Found a sim that seems to have changed their sim id. Current ID: %s Last ID: %s" % (currentSimID, lastSimID), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()), lockThreshold = 5)

	if not GetSimsSection().BranchExists(lastSimIDString):
		return currentSimIDString
	else:
		return lastSimIDString

def _Setup () -> None:
	global _savingObject, _simsSection, _allSimsSection

	_savingObject = SaveShared.Save(This.Mod, This.Mod.Namespace.replace(".", "_") + "_Save")
	Save.RegisterSavingObject(_savingObject)

	_simsSection = SectionSims.SectionSims("Sims", _savingObject)
	_savingObject.RegisterSection(_simsSection)

	_allSimsSection = SectionStandard.SectionStandard("AllSims", _savingObject)
	_savingObject.RegisterSection(_allSimsSection)

_Setup()
