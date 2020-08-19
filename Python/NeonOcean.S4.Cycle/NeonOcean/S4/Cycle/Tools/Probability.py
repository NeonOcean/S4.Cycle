from __future__ import annotations

import ast
import copy
import math
import operator
import random
import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Tools import Exceptions, Python, Savable, Types
from sims4.tuning import tunable

class OptionAdjustmentExpression:
	@staticmethod
	def _safeExponentiation (base: float, exponent: float) -> float:
		if exponent > 100:
			raise ValueError("Cannot raise a value to a power of more than 100.")

		return operator.pow(base, exponent)

	_standardBinaryOperators = {
		ast.Add: operator.add,
		ast.Sub: operator.sub,
		ast.Mult: operator.mul,
		ast.Div: operator.truediv,
		ast.Mod: operator.mod,
		ast.Pow: _safeExponentiation,
	}  # type: typing.Dict[typing.Any, typing.Callable[[float, float], float]]

	_standardUnaryOperators = {
		ast.USub: operator.neg,
		ast.UAdd: operator.pos
	}  # type: typing.Dict[typing.Any, typing.Callable[[float], float]]

	# noinspection SpellCheckingInspection
	_standardFunctions = {
		"round": round,
		"abs": abs,
		"max": max,
		"min": min,
		"ceil": math.ceil,
		"floor": math.floor,
		"sqrt": math.sqrt,
		"cos": math.cos,
		"sin": math.sin,
		"tan": math.tan
	}  # type: typing.Dict[typing.Any, typing.Callable]

	_standardVariables = {
		"pi": math.pi,
		"e": math.e
	}  # type: typing.Dict[str, float]

	def __init__ (self, expression: str):
		if not isinstance(expression, str):
			raise Exceptions.IncorrectTypeException(expression, "expression", (str,))

		self._expression = expression  # type: str
		self._additionalVariables = dict()  # type: typing.Dict[str, float]

	@property
	def BinaryOperators (self) -> typing.Dict[typing.Any, typing.Callable[[float, float], float]]:
		return {
			**self._standardBinaryOperators,
		}

	@property
	def UnaryOperators (self) -> typing.Dict[typing.Any, typing.Callable[[float], float]]:
		return {
			**self._standardUnaryOperators,
		}

	@property
	def Functions (self) -> typing.Dict[typing.Any, typing.Callable]:
		return {
			**self._standardFunctions,
		}

	@property
	def Variables (self) -> typing.Dict[typing.Any, float]:
		return {
			**self._standardVariables,
			**self._additionalVariables
		}

	def __copy__ (self):
		adjustmentType = self.__class__  # type: typing.Type[OptionAdjustmentExpression]
		adjustmentCopy = adjustmentType(self._expression)  # type: OptionAdjustmentExpression
		adjustmentCopy._additionalVariables = self._additionalVariables

		return adjustmentCopy

	def AddVariables (self, **additionalVariables) -> None:
		for variableIdentifier, variable in additionalVariables.items():  # type: str, float
			if not isinstance(variable, (float, int)):
				raise Exceptions.IncorrectTypeException(variable, "additionalVariables[%s]" % variableIdentifier, (float, int))

		self._additionalVariables.update(additionalVariables)

	def DoOperation (self, baseValue: float, currentOffsetValue: float, currentValue: float) -> float:
		if not isinstance(baseValue, (float, int)):
			raise Exceptions.IncorrectTypeException(baseValue, "baseValue", (float, int))

		if not isinstance(currentOffsetValue, (float, int)):
			raise Exceptions.IncorrectTypeException(currentOffsetValue, "currentOffsetValue", (float, int))

		if not isinstance(currentValue, (float, int)):
			raise Exceptions.IncorrectTypeException(currentValue, "currentValue", (float, int))

		expressionString = self._expression  # type: str

		try:
			expressionObject = ast.parse(expressionString, mode = "eval")  # type: ast.Expression
		except:
			Debug.Log("Failed to parse an adjustment expression.\nExpression" + expressionString, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			return currentOffsetValue

		binaryOperators = self.BinaryOperators
		unaryOperators = self.UnaryOperators

		functions = self.Functions

		variables = {
			"Base": baseValue,
			"CurrentOffset": currentOffsetValue,
			"Current": currentValue,
			**self.Variables
		}  # type: typing.Dict[str, float]

		try:
			expressionResults = self._EvaluateExpressionNode(expressionObject.body, binaryOperators, unaryOperators, functions, variables)  # type: float

			if not isinstance(expressionResults, float):
				raise Exceptions.IncorrectReturnTypeException(expressionResults, "expression", (float, int))

			if math.isinf(expressionResults) or math.isnan(expressionResults):
				raise ValueError("Adjustment expressions cannot return positive infinity, negative infinity, or nan.")

			return expressionResults
		except ZeroDivisionError:
			return currentOffsetValue
		except:
			Debug.Log("Failed to evaluate an adjustment expression.\nExpression" + expressionString, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":" + str(Python.GetLineNumber()))
			return currentOffsetValue

	def _EvaluateExpressionNode (
			self,
			expressionNode,
			binaryOperators: typing.Dict[typing.Any, typing.Callable[[float, float], float]],
			unaryOperators: typing.Dict[typing.Any, typing.Callable[[float], float]],
			functions: typing.Dict[typing.Any, typing.Callable],
			variables: typing.Dict[str, float]) -> float:

		if isinstance(expressionNode, ast.Num):
			return expressionNode.n
		elif isinstance(expressionNode, ast.BinOp):
			operationCallable = binaryOperators[type(expressionNode.op)]
			leftSide = self._EvaluateExpressionNode(expressionNode.left, binaryOperators, unaryOperators, functions, variables)
			rightSide = self._EvaluateExpressionNode(expressionNode.right, binaryOperators, unaryOperators, functions, variables)

			return operationCallable(leftSide, rightSide)
		elif isinstance(expressionNode, ast.UnaryOp):
			operationCallable = unaryOperators[type(expressionNode.op)]
			operand = self._EvaluateExpressionNode(expressionNode.operand, binaryOperators, unaryOperators, functions, variables)

			return operationCallable(operand)
		elif isinstance(expressionNode, ast.Call):
			if len(expressionNode.keywords) != 0:
				raise ValueError("Expression functions cannot have keyword arguments.")

			functionCallable = functions[expressionNode.func.id]
			functionArguments = (self._EvaluateExpressionNode(argument, binaryOperators, unaryOperators, functions, variables) for argument in expressionNode.args)

			return functionCallable(*functionArguments)
		elif isinstance(expressionNode, ast.Name):
			return variables[expressionNode.id]
		else:
			raise ValueError("Invalid node in found in parsed expression.\nNode Type: " + Types.GetFullName(expressionNode))

class Option(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

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

class OptionAdjuster:
	def __init__ (self,
				  adjustment: typing.Union[float, OptionAdjustmentExpression] = 0,
				  offsetMaximum: typing.Optional[float] = None,
				  offsetMinimum: typing.Optional[float] = None):

		"""
		An object to handle the adjustment of option weight offsets.
		"""

		self.Adjustment = adjustment
		self.OffsetMinimum = offsetMaximum
		self.OffsetMaximum = offsetMinimum

	@property
	def Adjustment (self) -> typing.Union[float, OptionAdjustmentExpression]:
		"""
		The number the weight offset will change to or an expression that will be evaluated to determine what number the weight offset should change to.
		"""

		return self._adjustment

	@Adjustment.setter
	def Adjustment (self, value: float) -> None:
		if not isinstance(value, (float, int, OptionAdjustmentExpression)):
			raise Exceptions.IncorrectTypeException(value, "Adjustment", (float, int, OptionAdjustmentExpression))

		self._adjustment = value

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

	def __copy__ (self):
		objectType = self.__class__  # type: typing.Type[OptionAdjuster]
		objectCopy = objectType(
			adjustment = copy.copy(self.Adjustment),
			offsetMaximum = self.OffsetMaximum,
			offsetMinimum = self.OffsetMinimum
		)  # type: OptionAdjuster

		return objectCopy

	def AdjustOption (self, adjustingOption: Option) -> None:
		baseValue = adjustingOption.BaseWeight  # type: float
		currentOffsetValue = adjustingOption.WeightOffset  # type: float
		currentValue = adjustingOption.Weight  # type: float

		adjustedOffset = self._ResolveAdjustment(baseValue, currentOffsetValue, currentValue)  # type: float

		if self.OffsetMaximum is not None:
			adjustedOffset = min(adjustedOffset, self.OffsetMaximum)

		if self.OffsetMinimum is not None:
			adjustedOffset = max(adjustedOffset, self.OffsetMinimum)

		adjustingOption.WeightOffset = adjustedOffset

	def _ResolveAdjustment (self, baseValue: float, currentOffsetValue: float, currentValue: float) -> float:
		adjustment = self.Adjustment  # type: typing.Union[float, OptionAdjustmentExpression]

		if isinstance(adjustment, (float, int)):
			return adjustment
		elif isinstance(adjustment, OptionAdjustmentExpression):
			return adjustment.DoOperation(baseValue, currentOffsetValue, currentValue)
		else:
			return currentOffsetValue

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

class TunableOptionAdjustmentExpression(tunable.TunableSingletonFactory):
	FACTORY_TYPE = OptionAdjustmentExpression

	def __init__ (self, description = "An expression to determine what value an option's weight offset should have.", **kwargs):
		# noinspection SpellCheckingInspection
		super().__init__(
			description = description,
			expression = tunable.Tunable(
				description = "The expression should be a line of python code that is run in order to get an option's next weight offset.\n"
							  "Exponents must be less than 100 or the expression will fail. All math must also be valid, doing things such as dividing by zero will cause the expression to fail. Failures will cause the current weight offset value to not change."
							  "Valid functions are round, abs, max, min, ceil, floor, sqrt, cos, sin, tan.\n"
							  "Valid variables are pi, e, Base, CurrentOffset, and Current. Base refers to the unmodified weight of the option. CurrentOffset is the amount the the option's weight is currently offset by. Current is the option's current weight, the base and the offset combined.",
				tunable_type = str,
				default = "0"),
			**kwargs)

class TunableOptionAdjuster(tunable.TunableSingletonFactory):
	FACTORY_TYPE = OptionAdjuster

	def __init__ (self, description = "An object to handle the adjustment of probability option weights.", **kwargs):  # TODO add the spacings the ea's tunables use to descriptions?
		super().__init__(
			description = description,
			adjustment = tunable.TunableVariant(
				description = "When a option's weight offset is adjusted by this adjuster, the weight offset value will replaced by either the value or result of the expression.",
				value = tunable.Tunable(tunable_type = float, default = 0),
				expression = TunableOptionAdjustmentExpression(),
				default = "value"
			),
			offsetMaximum = tunable.OptionalTunable(description = "The maximum value that the weight offset may be after the adjustment.", tunable = tunable.Tunable(tunable_type = float, default = 100)),
			offsetMinimum = tunable.OptionalTunable(description = "The minimum value that the weight offset may be after the adjustment.", tunable = tunable.Tunable(tunable_type = float, default = -100)),
			**kwargs)

class TunableProbability(tunable.TunableSingletonFactory):
	FACTORY_TYPE = Probability

	def __init__ (self, description = "An object to randomly select from a set of options.", **kwargs):  # TODO add the spacings the ea's tunables use to descriptions?
		super().__init__(
			description = description,
			options = tunable.TunableList(description = "The set of options for the probability object.", tunable = TunableOption()),
			**kwargs)
