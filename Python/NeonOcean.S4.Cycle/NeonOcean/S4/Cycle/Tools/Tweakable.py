from __future__ import annotations

import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main.Tools import Exceptions, Savable

class TweakableBoolean(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, value: bool):
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		self._baseValue = value

		self.Locked = False

		self.Value = value

		super().__init__()

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BaseValue", "_baseValue", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Value", "Value", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Locked", "Locked", False, requiredAttribute = True))

	@property
	def BaseValue (self) -> bool:
		return self._baseValue

	@property
	def Value (self) -> bool:
		return self._value

	@Value.setter
	def Value (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Value", (bool,))

		if self.Locked:
			return

		self._value = value

	@property
	def Locked (self) -> bool:
		"""
		Whether or not current value is locked in place. Locked values cannot normally be changed unless this property is set to False.
		"""

		return self._locked

	@Locked.setter
	def Locked (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Locked", (bool,))

		self._locked = value

	def __copy__ (self):
		tweakableClass = self.__class__  # type: typing.Type[TweakableBoolean]
		tweakableCopy = tweakableClass(self._baseValue)  # type: TweakableBoolean
		tweakableCopy._value = self._value
		tweakableCopy._locked = self._locked

class TweakableInteger(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, value: int):
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "value", (int,))

		self._baseValue = value

		self.Locked = False

		self.UpperBound = None
		self.LowerBound = None

		self.Value = value

		super().__init__()

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BaseValue", "_baseValue", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Value", "Value", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Locked", "Locked", False, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("UpperBound", "UpperBound", None, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("LowerBound", "LowerBound", None, requiredAttribute = True))

	@property
	def BaseValue (self) -> int:
		return self._baseValue

	@property
	def Value (self) -> int:
		return self._value

	@Value.setter
	def Value (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Value", (int,))

		if self.Locked:
			return

		if self.UpperBound is not None:
			value = min(value, self.UpperBound)

		if self.LowerBound is not None:
			value = max(value, self.LowerBound)

		self._value = value

	@property
	def Locked (self) -> bool:
		"""
		Whether or not current value is locked in place. Locked values cannot normally be changed unless this property is set to False.
		"""

		return self._locked

	@Locked.setter
	def Locked (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Locked", (bool,))

		self._locked = value

	@property
	def UpperBound (self) -> typing.Optional[int]:
		"""
		The value will can be no greater than the upper bound, let this be None to have no bound.
		"""

		return self._upperBound

	@UpperBound.setter
	def UpperBound (self, value: typing.Optional[int]) -> None:
		if not isinstance(value, int) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "UpperBound", (int, None))

		self._upperBound = value

	@property
	def LowerBound (self) -> typing.Optional[int]:
		"""
		The value will can be no less than the lower bound, let this be None to have no bound.
		"""

		return self._lowerBound

	@LowerBound.setter
	def LowerBound (self, value: typing.Optional[int]) -> None:
		if not isinstance(value, int) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "LowerBound", (int, None))

		self._lowerBound = value

	def __copy__ (self):
		tweakableClass = self.__class__  # type: typing.Type[TweakableInteger]
		tweakableCopy = tweakableClass(self._baseValue)  # type: TweakableInteger
		tweakableCopy._value = self._value
		tweakableCopy._locked = self._locked
		tweakableCopy._upperBound = self._upperBound
		tweakableCopy._lowerBound = self._lowerBound

class TweakableRealNumber(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, value: typing.Union[float, int]):
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "value", (float, int))

		self._baseValue = value

		self.Locked = False

		self.UpperBound = None
		self.LowerBound = None

		self.Value = value

		super().__init__()

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BaseValue", "_baseValue", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Value", "Value", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Locked", "Locked", False, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("UpperBound", "UpperBound", None, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("LowerBound", "LowerBound", None, requiredAttribute = True))

	@property
	def BaseValue (self) -> typing.Union[float, int]:
		return self._baseValue

	@property
	def Value (self) -> typing.Union[float, int]:
		return self._value

	@Value.setter
	def Value (self, value: typing.Union[float, int]) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "value", (float, int))

		if self.Locked:
			return

		if self.UpperBound is not None:
			value = min(value, self.UpperBound)

		if self.LowerBound is not None:
			value = max(value, self.LowerBound)

		self._value = value

	@property
	def Locked (self) -> bool:
		"""
		Whether or not current value is locked in place. Locked values cannot normally be changed unless this property is set to False.
		"""

		return self._locked

	@Locked.setter
	def Locked (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "Locked", (bool,))

		self._locked = value

	@property
	def UpperBound (self) -> typing.Optional[typing.Union[float, int]]:
		"""
		The value will can be no greater than the upper bound, let this be None to have no bound.
		"""

		return self._upperBound

	@UpperBound.setter
	def UpperBound (self, value: typing.Optional[typing.Union[float, int]]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "UpperBound", (float, int, None))

		self._upperBound = value

	@property
	def LowerBound (self) -> typing.Optional[int]:
		"""
		The value will can be no less than the lower bound, let this be None to have no bound.
		"""

		return self._lowerBound

	@LowerBound.setter
	def LowerBound (self, value: typing.Optional[typing.Union[float, int]]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "LowerBound", (float, int, None))

		self._lowerBound = value

	def __copy__ (self):
		tweakableClass = self.__class__  # type: typing.Type[TweakableRealNumber]
		tweakableCopy = tweakableClass(self._baseValue)  # type: TweakableRealNumber
		tweakableCopy._value = self._value
		tweakableCopy._locked = self._locked
		tweakableCopy._upperBound = self._upperBound
		tweakableCopy._lowerBound = self._lowerBound
