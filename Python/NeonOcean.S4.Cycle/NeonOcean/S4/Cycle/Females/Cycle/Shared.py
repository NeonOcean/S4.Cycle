from __future__ import annotations

import enum_lib

MenstrualCycleTypeIdentifier = "Menstrual"  # type: str

class CompletionReasons(enum_lib.IntFlag):
	Unknown = 1  # type: CompletionReasons
	Finished = 2  # type: CompletionReasons
	Canceled = 4  # type: CompletionReasons
	Pregnancy = 8  # type: CompletionReasons

class MenstrualCyclePhases(enum_lib.IntEnum):
	Follicular = 1  # type: MenstrualCyclePhases
	Ovulation = 2  # type: MenstrualCyclePhases
	Luteal = 3  # type: MenstrualCyclePhases
	Menstruation = 4  # type: MenstrualCyclePhases
