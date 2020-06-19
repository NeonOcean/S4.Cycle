from __future__ import annotations

import random
import typing
import copy

from NeonOcean.S4.Main.Tools import Exceptions, Savable
from sims4.tuning import tunable

class Option(Savable.SavableExtension):
	def __init__ (self, identifier: str, weight: float, weightOffset: float = 0):
		"""
		An option for a probability object to select.
		:param identifier: A string that will be returned if the option has been selected. The identifier should be unique to a probability object.
		:type identifier: str
		:param weight: This option's weight. The probability this option will be chosen is option's weight divided by the sum of every option's
		weight. This cannot be less than 0.
		:type weight: float
		:param weightOffset: The amount this option's weight is offset buy. The weight offset can never reduce the option's weight to less than 0.
		:type weightOffset: float
		"""

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		super().__init__()

		self._identifier = identifier  # type: str
		self.BaseWeight = weight  # type: float
		self.WeightOffset = weightOffset  # type: float

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Identifier", "_identifier", "", requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BaseWeight", "_baseWeight", 0, requiredAttribute = True))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("WeightOffset", "_weightOffset", 0, requiredAttribute = True))

	@property
	def Identifier (self) -> str:
		"""
		The string that will be returned when this option is randomly chosen. The identifier should be unique to a probability object.
		"""

		return self._identifier

	@property
	def Weight (self) -> float:
		"""
		This option's weight. The probability this option will be chosen is option's weight divided by the sum of every option's weight. The option's
		weight can never be less than 0.
		"""

		weight = self._baseWeight + self._weightOffset  # type: float
		weight = max(weight, 0.0)

		return weight

	@property
	def BaseWeight (self) -> float:
		"""
		The true weight of this option, its weight when not affected by an offset.
		"""

		return self._baseWeight

	@BaseWeight.setter
	def BaseWeight (self, value: float) -> None:
		"""
		The true weight of this option, its weight when not affected by an offset.
		"""

		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "BaseWeight", (float, int))

		if value < 0:
			raise ValueError("'BaseWeight' values cannot be less than 0.")

		self._baseWeight = value

	@property
	def WeightOffset (self) -> float:
		"""
		The amount this option's weight is offset buy. The weight offset can never reduce the option's weight to less than 0.
		"""

		return self._weightOffset

	@WeightOffset.setter
	def WeightOffset (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "WeightOffset", (float, int))

		self._weightOffset = value

	def __copy__ (self):
		optionCopy = self.__class__(
			self.Identifier,
			self.BaseWeight,
			weightOffset = self.WeightOffset
		)

		return optionCopy

class OptionWeightAdjuster:
	def __init__ (self, offsetChange: float = 0, overrideOffset: bool = True, offsetMaximum: typing.Optional[float] = None, offsetMinimum: typing.Optional[float] = None):
		"""
		An object to handle the adjustment of option weight offsets.
		"""

		self.OffsetChange = offsetChange
		self.OverrideOffset = overrideOffset
		self.OffsetMinimum = offsetMaximum
		self.OffsetMaximum = offsetMinimum

	@property
	def OffsetChange (self) -> float:
		"""
		The amount the option's weight offset will be changed to or adjusted by.
		"""

		return self._offsetChange

	@OffsetChange.setter
	def OffsetChange (self, value: float) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "OffsetChange", (float, int))

		self._offsetChange = value

	@property
	def OverrideOffset (self) -> bool:
		"""
		Whether the offset change should add to the option's weight offset or replace it.
		"""

		return self._overrideOffset

	@OverrideOffset.setter
	def OverrideOffset (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "OverrideOffset", (bool,))

		self._overrideOffset = value

	@property
	def OffsetMaximum (self) -> typing.Optional[float]:
		"""
		The maximum value that the weight offset may be after the adjustment. This may be none, indicating there is no maximum value.
		"""

		return self._offsetMaximum

	@OffsetMaximum.setter
	def OffsetMaximum (self, value: typing.Optional[float]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "OffsetMaximum", (float, int, None))

		self._offsetMaximum = value

	@property
	def OffsetMinimum (self) -> typing.Optional[float]:
		"""
		The minimum value that the weight offset may be after the adjustment. This may be none, indicating there is no minimum value.
		"""

		return self._offsetMinimum

	@OffsetMinimum.setter
	def OffsetMinimum (self, value: typing.Optional[float]) -> None:
		if not isinstance(value, (float, int)) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "OffsetMinimum", (float, int, None))

		self._offsetMinimum = value

	def AdjustOption (self, adjustingOption: Option) -> None:
		adjustedOffset = adjustingOption.WeightOffset  # type: float

		if self.OverrideOffset:
			adjustedOffset = self.OffsetChange
		else:
			adjustedOffset += self.OffsetChange

		if self.OffsetMaximum is not None:
			adjustedOffset = min(adjustedOffset, self.OffsetMaximum)

		if self.OffsetMinimum is not None:
			adjustedOffset = max(adjustedOffset, self.OffsetMinimum)

		adjustingOption.WeightOffset = adjustedOffset

class Probability(Savable.SavableExtension):
	def __init__ (self, options: typing.Union[typing.List[Option], typing.Tuple[Option, ...]]):
		"""
		An object to randomly select from a set of options.
		:param options: This object's set of options. Duplicate options in this list will not be added.
		:type options: typing.List[ProbabilityOption]
		"""

		if options is None:
			options = list()

		if not isinstance(options, (list, tuple)):
			raise Exceptions.IncorrectTypeException(options, "options", (list, tuple, None))

		super().__init__()

		self._options = list(options)

		self.RegisterSavableAttribute(Savable.ListedSavableAttributeHandler(
			"Options",
			"_options",
			lambda: Option("", 0),
			lambda: list(),
			requiredAttribute = True)
		)

		self._ClearDuplicateOptions()

	@property
	def Options (self) -> typing.List[Option]:
		"""
		The options of this probability object.
		"""

		return list(self._options)

	@property
	def HasOptions (self) -> bool:
		"""
		Whether or not this object has any options. Attempting to chose an option when no options are available will result in an exception being raise.
		"""

		return len(self._options) != 0


	def __copy__ (self):
		optionsCopy = list()

		for option in self._options:  # type: Option
			optionsCopy.append(copy.copy(option))

		return self.__class__(optionsCopy)

	def AddOption (self, addingOption: Option) -> None:
		"""
		Add an option to this probability object. An exception will be raised if a single probability option instance is being added more than once, or
		a option already exists with the adding option's identifier.
		"""

		if not isinstance(addingOption, Option):
			raise Exceptions.IncorrectTypeException(addingOption, "addingOption", (Option,))

		if self._IsDuplicateOption(addingOption):
			raise ValueError("Could not add an option with the identifier '" + addingOption.Identifier + "', its already been added or another option with the same identifier exists.")

		self._options.append(addingOption)

	def RemoveOption (self, removingOption: Option) -> None:
		"""
		Remove an option from the probability object. If this option has not been added nothing will happen.
		"""

		if not isinstance(removingOption, Option):
			raise Exceptions.IncorrectTypeException(removingOption, "removingOption", (Option,))

		try:
			self._options.remove(removingOption)
		except ValueError:
			pass

	def GetOption (self, optionIdentifier: str) -> typing.Optional[Option]:
		"""
		Get an option by its identifier. If no such option has been added this will return none.
		"""

		if not isinstance(optionIdentifier, str):
			raise Exceptions.IncorrectTypeException(optionIdentifier, "optionIdentifier", (str,))

		for option in self._options:  # type: Option
			if option.Identifier == optionIdentifier:
				return option

		return None

	def ChooseOption (self, seed: typing.Hashable = None, ignoringOptions: typing.Optional[typing.Set[str]] = None) -> Option:
		"""
		Randomly select an option from this object's list of options.
		:param seed: The seed to be used to selected an option.
		:type seed: typing.Hashable
		:param ignoringOptions: A set of option identifiers to be ignored when picking an option.
		:type ignoringOptions: typing.Optional[typing.Set[str]]
		"""

		if len(self._options) == 0:
			raise Exception("Cannot choose an option when no options are available.")

		if ignoringOptions is None:
			ignoringOptions = set()

		if not isinstance(ignoringOptions, set):
			raise Exceptions.IncorrectTypeException(ignoringOptions, "ignoringOptions", (set, None))

		optionWeightSum = 0  # type: float

		for option in self._options:  # type: Option
			if option.Identifier in ignoringOptions:
				continue

			optionWeightSum += option.Weight

		random.seed(seed)
		optionRoll = random.random()  # type: float

		testedChance = 0  # type: float

		selectedOption = None  # type: typing.Optional[Option]
		for selectedOption in self._options:
			if selectedOption.Identifier in ignoringOptions:
				continue

			optionChance = selectedOption.Weight / optionWeightSum  # type: float

			if optionChance + testedChance >= optionRoll:
				break

			testedChance += optionChance

		assert selectedOption is not None

		return selectedOption

	def _IsDuplicateOption (self, testingOption: Option) -> bool:
		for existingOption in self._options:  # type: Option
			if existingOption is testingOption:
				return True

			if existingOption.Identifier == testingOption.Identifier:
				return True

		return False

	def _ClearDuplicateOptions (self) -> None:
		existingIdentifiers = set()  # type: typing.Set[str]

		optionIndex = 0
		while optionIndex < len(self._options):
			option = self._options[optionIndex]  # type: Option

			if option.Identifier in existingIdentifiers:
				self._options.pop(optionIndex)
				continue

			optionIndex += 1

	def _OnLoaded (self) -> None:
		self._ClearDuplicateOptions()

	def _OnResetted (self) -> None:
		self._ClearDuplicateOptions()

class TunableOption(tunable.TunableSingletonFactory):
	FACTORY_TYPE = Option

	def __init__ (self, description = "An option for a probability object to select.", **kwargs):  # TODO add the spacings the ea's tunables use to descriptions?
		super().__init__(
			description = description,
			identifier = tunable.Tunable(description = "A string that will be returned if the option has been selected. The identifier should be unique to a probability object.", tunable_type = str, default = ""),
			weight = tunable.TunableRange(description = "This option's weight. The probability this option will be chosen is option's weight divided by the sum of every option's weight. This cannot be less than 0.", tunable_type = float, default = 0, minimum = 0),
			**kwargs)

class TunableOptionWeightAdjuster(tunable.TunableSingletonFactory):
	FACTORY_TYPE = OptionWeightAdjuster

	def __init__ (self, description = "An object to handle the adjustment of probability option weights.", **kwargs):  # TODO add the spacings the ea's tunables use to descriptions?
		super().__init__(
			description = description, #TODO allow offset math operator selection
			offsetChange = tunable.Tunable(description = "The amount the option's weight offset will be changed to or adjusted by.", tunable_type = float, default = 0),
			overrideOffset = tunable.Tunable(description = "Whether the offset change should add to the option's weight offset or replace it.", tunable_type = bool, default = True),
			offsetMaximum = tunable.OptionalTunable(description = "The maximum value that the weight offset may be after the adjustment.", tunable = tunable.Tunable(tunable_type = float, default = 0)),
			offsetMinimum = tunable.OptionalTunable(description = "The minimum value that the weight offset may be after the adjustment.", tunable = tunable.Tunable(tunable_type = float, default = 0)),
			**kwargs)

class TunableProbability(tunable.TunableSingletonFactory):
	FACTORY_TYPE = Probability

	def __init__ (self, description = "An object to randomly select from a set of options.", **kwargs):  # TODO add the spacings the ea's tunables use to descriptions?
		super().__init__(
			description = description,
			options = tunable.TunableList(description = "The set of options for the probability object.", tunable = TunableOption()),
			**kwargs)
