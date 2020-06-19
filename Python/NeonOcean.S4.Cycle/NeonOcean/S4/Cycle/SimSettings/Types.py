from __future__ import annotations

from NeonOcean.S4.Cycle.SimSettings import Base as SettingsBase
from NeonOcean.S4.Main.Tools import Exceptions, Version

class WoohooSafetyMethodUseSetting(SettingsBase.Setting):
	Type = dict

	@classmethod
	def Verify (cls, value: dict, lastChangeVersion: Version.Version = None) -> dict:
		if not isinstance(value, dict):
			raise Exceptions.IncorrectTypeException(value, "value", (dict,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		for methodID, usingMethod in value.items():  # type: int, bool
			if not isinstance(methodID, int):
				raise Exceptions.IncorrectTypeException(methodID, "value<Key>", (int,))

			if not isinstance(usingMethod, int):
				raise Exceptions.IncorrectTypeException(usingMethod, "value[%s]" % methodID, (bool,))

		return value
