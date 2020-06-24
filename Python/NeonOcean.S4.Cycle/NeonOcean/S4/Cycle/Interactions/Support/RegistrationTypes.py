from __future__ import annotations

import tag
from NeonOcean.S4.Main.Interactions.Support import RegistrationTypes
from objects import definition

_toiletTag = tag.Tag("Func_Toilet")  # type: tag.Tag

def _OnStart (cause) -> None:
	if cause:
		pass

	if not RegistrationTypes.ObjectTypeOrganizer.HasDeterminerForType("Toilet"):
		RegistrationTypes.ObjectTypeOrganizer.RegisterTypeDeterminer("Toilet", _ToiletDeterminer)

def _ToiletDeterminer (objectDefinition: definition.Definition) -> bool:
	return objectDefinition.has_build_buy_tag(_toiletTag)
