from __future__ import annotations

import enum_lib

class BuffRarity(enum_lib.IntFlag):
	NotApplicable = 0  # type: BuffRarity
	Common = 1  # type: BuffRarity
	Uncommon = 2  # type: BuffRarity
	Rare = 4  # type: BuffRarity
	VeryRare = 8  # type: BuffRarity
