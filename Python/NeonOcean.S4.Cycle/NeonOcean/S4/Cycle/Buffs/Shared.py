from __future__ import annotations

import enum_lib
from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Language

ReproductiveSystemBuffReason = Language.String(This.Mod.Namespace + ".Buffs_Reasons.Reproductive_System")  # type: Language.String

class BuffRarity(enum_lib.IntFlag):
	Common = 1  # type: BuffRarity
	Uncommon = 2  # type: BuffRarity
	Rare = 4  # type: BuffRarity
	VeryRare = 8  # type: BuffRarity
