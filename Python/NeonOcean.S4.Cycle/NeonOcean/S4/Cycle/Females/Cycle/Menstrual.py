from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import Events as CycleEvents, Guides as CycleGuides, ReproductionShared
from NeonOcean.S4.Cycle.Females.Cycle import Base as CycleBase, Shared as CycleShared, Types as CycleTypes
from NeonOcean.S4.Main import LoadingShared
from NeonOcean.S4.Main.Tools import Classes, Exceptions, Savable

class MenstrualCycle(CycleBase.CycleBase):
	def __init__ (self):
		"""
		A cycle for creatures such as humans.
		"""

		super().__init__()

		self.FollicularLength = 20160  # type: float
		self.OvulationLength = 1800  # type: float
		self.LutealLength = 20160  # type: float
		self.MenstruationLength = 5760  # type: float

		self._phases.update(
			{
				CycleShared.MenstrualCyclePhases.Follicular: self._Phase(
					lambda: self.InFollicularPhase, lambda: self.FollicularLength, lambda: self.FollicularStartMinute, lambda: self.FollicularEndMinute
				),
				CycleShared.MenstrualCyclePhases.Ovulation: self._Phase(
					lambda: self.Ovulating, lambda: self.OvulationLength, lambda: self.OvulationStartMinute, lambda: self.OvulationEndMinute
				),
				CycleShared.MenstrualCyclePhases.Luteal: self._Phase(
					lambda: self.InLutealPhase, lambda: self.LutealLength, lambda: self.LutealStartMinute, lambda: self.LutealEndMinute
				),
				CycleShared.MenstrualCyclePhases.Menstruation: self._Phase(
					lambda: self.Menstruating, lambda: self.MenstruationLength, lambda: self.MenstruationStartMinute, lambda: self.MenstruationEndMinute
				),
			})

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FollicularLength", "FollicularLength", self.FollicularLength, requiredSuccess = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("OvulationLength", "OvulationLength", self.OvulationLength, requiredSuccess = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("LutealLength", "LutealLength", self.LutealLength, requiredSuccess = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("MenstruationLength", "MenstruationLength", self.MenstruationLength, requiredSuccess = True))

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	def TypeIdentifier (cls) -> str:
		"""
		This cycle type's identifier, this is used to save and load the cycle. Loading will not be possible unless the cycle type is registered
		through the function in the cycle types module.
		"""

		return CycleShared.MenstrualCycleTypeIdentifier

	@property
	def Lifetime (self) -> float:
		"""
		The exact life time of the cycle in reproductive minutes.
		"""

		return self.LutealEndMinute

	@property
	def FollicularLength (self) -> float:
		"""
		The amount of time in reproductive minutes of the cycle's follicular phase.
		"""

		return self._follicularLength

	@FollicularLength.setter
	def FollicularLength (self, value: float) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "FollicularLength", (float, int))

		if value < 0:
			raise ValueError("FollicularLength values must be greater than or equal to 0.")

		self._follicularLength = value

	@property
	def FollicularStartMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that the follicular phase will start.
		"""

		return 0

	@property
	def FollicularEndMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that the follicular phase will end.
		"""

		return self.FollicularLength

	@property
	def InFollicularPhase (self) -> bool:
		"""
		Whether or not the cycle is in the follicular phase.
		"""

		return self.FollicularStartMinute <= self.Age < self.FollicularEndMinute

	@property
	def OvulationLength (self) -> float:
		"""
		The amount of time in reproductive minutes in which ovulation will occur, this will not affect the length of the cycle. The sim will start ovulating
		half of this many minutes before the follicular phase ends, and will stop ovulating half of this many minutes after the luteal phase starts.
		"""

		return self._ovulationLength

	@OvulationLength.setter
	def OvulationLength (self, value: float) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "OvulationLength", (float, int))

		if value < 0:
			raise ValueError("OvulationLength values must be greater than or equal to 0.")

		self._ovulationLength = value

	@property
	def OvulationStartMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that ovulation will start.
		"""

		return self.FollicularLength - self.OvulationLength / 2

	@property
	def OvulationEndMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that ovulation will end.
		"""

		return self.FollicularLength + self.OvulationLength / 2

	@property
	def Ovulating (self) -> bool:
		"""
		Whether or not ovulation is occurring.
		"""

		return self.OvulationStartMinute <= self.Age < self.OvulationEndMinute

	@property
	def LutealLength (self) -> float:
		"""
		The amount of time in reproductive minutes of the cycle's luteal phase.
		"""

		return self._lutealLength

	@LutealLength.setter
	def LutealLength (self, value: float) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "LutealLength", (float, int))

		if value < 0:
			raise ValueError("LutealLength values must be greater than or equal to 0.")

		self._lutealLength = value

	@property
	def LutealStartMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that the luteal phase will start.
		"""

		return self.FollicularLength

	@property
	def LutealEndMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that the luteal phase will end.
		"""

		return self.FollicularLength + self.LutealLength

	@property
	def InLutealPhase (self) -> bool:
		"""
		Whether or not the cycle is in the luteal phase.
		"""

		return self.LutealStartMinute <= self.Age < self.LutealEndMinute

	@property
	def MenstruationLength (self) -> float:
		"""
		The amount of time in reproductive minutes for which ovulation will occur, this does not affect the length of this menstrual cycle.
		The sim will start menstruating this many minutes before the luteal phase ends and stop menstruating at the same time the luteal phase ends.
		"""

		return self._menstruationLength

	@MenstruationLength.setter
	def MenstruationLength (self, value: float) -> None:
		if not isinstance(value, float) and not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "MenstruationLength", (float, int))

		if value < 0:
			raise ValueError("MenstruationLength values must be greater than or equal to 0.")

		self._menstruationLength = value

	@property
	def MenstruationStartMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that menstruation will start.
		"""

		return self.LutealEndMinute - self.MenstruationLength

	@property
	def MenstruationEndMinute (self) -> float:
		"""
		The amount of time in reproductive minutes into the cycle that menstruation will end.
		"""

		return self.LutealEndMinute

	@property
	def Menstruating (self) -> bool:
		"""
		Whether or not menstruation is occurring.
		"""

		return self.MenstruationStartMinute < self.Age <= self.MenstruationEndMinute

	@classmethod
	def GetGenerationArgumentsType (cls, target: ReproductionShared.ReproductiveSystem) -> typing.Type[CycleEvents.CycleGeneratingArguments]:
		"""
		Get the type of generating event arguments to be used in generating a cycle.
		"""

		return CycleEvents.CycleMenstrualGeneratingArguments

	@classmethod
	def GetCycleGuide (cls, target: ReproductionShared.ReproductiveSystem) -> CycleGuides.CycleGuide:
		"""
		Get the cycle guide applicable to this cycle type.
		"""

		return CycleGuides.CycleMenstrualGuide.GetGuide(target.GuideGroup)

	def GetDebugNotificationString (self) -> str:
		debugString = super().GetDebugNotificationString()  # type: str

		menstrualDebugFormatting = "\n" \
								   "   Follicular Length: %s minutes\n" \
								   "   Ovulation Length: %s minutes\n" \
								   "   Luteal Length: %s minutes\n" \
								   "   Menstruation Length: %s minutes\n"

		follicularLength = round(self.FollicularLength)  # type: float
		ovulationLength = round(self.OvulationLength)  # type: float
		lutealLength = round(self.LutealLength)  # type: float
		menstruationLength = round(self.MenstruationLength)  # type: float

		return debugString + (menstrualDebugFormatting % (follicularLength, ovulationLength, lutealLength, menstruationLength))

	def _GenerateInternal (self, generatingArguments: CycleEvents.CycleMenstrualGeneratingArguments) -> None:
		super()._GenerateInternal(generatingArguments)

		self.LutealLength = generatingArguments.GetLutealLength()
		self.OvulationLength = generatingArguments.GetOvulationLength()
		self.FollicularLength = generatingArguments.GetFollicularLength()
		self.MenstruationLength = generatingArguments.GetMenstruationLength()

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	CycleTypes.RegisterCycleType(MenstrualCycle.TypeIdentifier, MenstrualCycle)