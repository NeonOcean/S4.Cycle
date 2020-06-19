from __future__ import annotations

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main.Saving import Save, SaveShared, SectionSims, SectionStandard

_savingObject: SaveShared.Save
_simsSection: SectionSims.SectionSims
_allSimsSection: SectionStandard.SectionStandard

def GetSavingObject () -> SaveShared.Save:
	return _savingObject

def GetSimsSection () -> SectionSims.SectionSims:
	return _simsSection

def GetAllSimsSection () -> SectionStandard.SectionStandard:
	return _allSimsSection

def _Setup () -> None:
	global _savingObject, _simsSection, _allSimsSection

	_savingObject = SaveShared.Save(This.Mod, This.Mod.Namespace.replace(".", "_") + "_Save")
	Save.RegisterSavingObject(_savingObject)

	_simsSection = SectionSims.SectionSims("Sims", _savingObject)
	_savingObject.RegisterSection(_simsSection)

	_allSimsSection = SectionStandard.SectionStandard("AllSims", _savingObject)
	_savingObject.RegisterSection(_allSimsSection)

_Setup()
