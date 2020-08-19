from __future__ import annotations

import enum_lib
import typing

from NeonOcean.S4.Cycle import This
from NeonOcean.S4.Main.Tools import Exceptions, Savable, Tunable as ToolsTunable
from sims4.tuning import tunable

class ConnectionType(enum_lib.IntEnum):
	Linear = 0  # type: ConnectionType
	BezierCurve = 1  # type: ConnectionType

class CurvePoint(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, x: typing.Union[float, int] = 0, y: typing.Union[float, int] = 0, connectionType: ConnectionType = ConnectionType.Linear):
		super().__init__()

		if not isinstance(x, (float, int)):
			raise Exceptions.IncorrectTypeException(x, "x", (float, int))

		if not isinstance(y, (float, int)):
			raise Exceptions.IncorrectTypeException(y, "y", (float, int))

		self._x = x  # type: typing.Union[float, int]
		self._y = y  # type: typing.Union[float, int]
		self._connectionType = connectionType  # type: ConnectionType

		def verifyX (value: typing.Union[float, int]) -> None:
			if not isinstance(value, (float, int)):
				raise Exceptions.IncorrectTypeException(value, "X", (float, int))

		def verifyY (value: typing.Union[float, int]) -> None:
			if not isinstance(value, (float, int)):
				raise Exceptions.IncorrectTypeException(value, "Y", (float, int))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("X", "_x", 0, requiredAttribute = True, typeVerifier = verifyX))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Y", "_y", 0, requiredAttribute = True, typeVerifier = verifyY))

	@property
	def X (self) -> typing.Union[float, int]:
		return self._x

	@property
	def Y (self) -> typing.Union[float, int]:
		return self._y

	@property
	def ConnectionType (self) -> ConnectionType:
		return self._connectionType

	def __copy__ (self):
		return self.__class__(x = self.X, y = self.Y)

	def __str__ (self):
		return "(%s, %s)" % (self.X, self.Y)

class Curve(Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	SecantMethodMaxIterations = 15

	def __init__ (self, points: typing.Union[typing.Tuple[CurvePoint, ...], typing.List[CurvePoint]] = None):
		super().__init__()

		if not isinstance(points, (list, tuple)) and points is not None:
			raise Exceptions.IncorrectTypeException(points, "points", (list, tuple, None))

		if points is None:
			points = list()
		else:
			points = list(points)

		for pointIndex in range(len(points)):
			point = points[pointIndex]  # type: CurvePoint

			if not isinstance(point, CurvePoint):
				raise Exceptions.IncorrectTypeException(point, "points[%s]" % pointIndex, (CurvePoint,))

		self._points = points  # type: typing.List[CurvePoint]
		self._SortPoints()

		self.RegisterSavableAttribute(Savable.ListedSavableAttributeHandler(
			"Points",
			"_points",
			lambda: CurvePoint(),
			lambda: list(),
			requiredAttribute = True
		))

	@property
	def Points (self) -> typing.List[CurvePoint]:
		return list(self._points)

	def __copy__ (self):
		copiedPoints = list(point.__copy__() for point in self._points)
		return self.__class__(points = copiedPoints)

	def AddPoint (self, point: CurvePoint) -> None:
		if not isinstance(point, CurvePoint):
			raise Exceptions.IncorrectTypeException(point, "point", (CurvePoint,))

		self._points.append(point)
		self._SortPoints()

	def RemovePoint (self, point: CurvePoint) -> None:
		if not isinstance(point, CurvePoint):
			raise Exceptions.IncorrectTypeException(point, "point", (CurvePoint,))

		self._points.remove(point)

	def CreateOffsetCurve (self, xOffset: float = 0, yOffset: float = 0) -> typing.Any:
		"""
		Get a copy of this curve with all points offset by these amounts.
		"""

		if not isinstance(xOffset, (float, int)):
			raise Exceptions.IncorrectTypeException(xOffset, "xOffset", (float, int))

		if not isinstance(yOffset, (float, int)):
			raise Exceptions.IncorrectTypeException(yOffset, "yOffset", (float, int))

		if xOffset == 0 and yOffset == 0:
			return

		offsetPoints = list()  # type: typing.List[CurvePoint]

		for point in self._points:  # type: CurvePoint
			offsetPoints.append(CurvePoint(point.X + xOffset, point.Y + yOffset))

		return self.__class__(points = offsetPoints)

	def ClosestPoint (self, x: float) -> CurvePoint:
		"""
		Get the point with an x value closest to the input x value.
		"""

		return self._points[self.ClosestPointIndex(x)]

	def ClosestPointIndex (self, x: float) -> int:
		"""
		Get the index of the point with an x value closest to the input x value.
		"""

		if not isinstance(x, (float, int)):
			raise Exceptions.IncorrectTypeException(x, "x", (float, int))

		if len(self._points) <= 0:
			raise Exception("Cannot work on a curve with no points.")

		closestIndex = None  # type: typing.Optional[int]
		closestDistance = None  # type: typing.Union[float, None]

		for pointIndex in range(len(self._points)):  # type: int
			point = self._points[pointIndex]  # type: CurvePoint

			distance = abs(point.X - x)  # type: float

			if closestIndex is not None:
				if distance > closestDistance:
					break

			closestIndex = pointIndex
			closestDistance = distance

			if point.X >= x:
				break

		assert closestIndex is not None

		return closestIndex

	def PointAt (self, x: float) -> typing.Optional[CurvePoint]:
		"""
		Get the point with the same x value as the input. This will return None if no such point exists.
		"""

		foundIndex = self.PointIndexAt(x)  # type: typing.Optional[int]

		if foundIndex is None:
			return None
		else:
			return self._points[self.PointIndexAt(x)]

	def PointIndexAt (self, x: float) -> typing.Optional[int]:
		"""
		Get the index of the point with the same x value as the input. This will return None if no such point exists.
		"""

		if not isinstance(x, (float, int)):
			raise Exceptions.IncorrectTypeException(x, "x", (float, int))

		foundIndex = None  # type: typing.Optional[int]

		for pointIndex in range(len(self._points)):  # type: int
			point = self._points[pointIndex]  # type: CurvePoint

			if point.X != x:
				if foundIndex is not None:
					break
				else:
					continue

			foundIndex = pointIndex

		return foundIndex

	def Evaluate (self, x: float) -> float:
		"""
		Get the y value at which curve the crosses this x axis.
		"""

		if not isinstance(x, (float, int)):
			raise Exceptions.IncorrectTypeException(x, "x", (float, int))

		if len(self._points) <= 0:
			return 0

		if self._points[0].X >= x:
			return self._points[0].Y

		if self._points[-1].X <= x:
			return self._points[-1].Y

		lowPoint = self._points[0]  # type: CurvePoint
		highPoint = self._points[-1]  # type: CurvePoint

		for pointIndex in range(len(self._points)):
			point = self._points[pointIndex]  # type: CurvePoint

			if x <= point.X:
				highPoint = self._points[pointIndex]
				lowPoint = self._points[pointIndex - 1]
				break

		if highPoint.X == x:
			return highPoint.Y
		elif lowPoint.X == x:
			return lowPoint.Y

		if lowPoint.ConnectionType == ConnectionType.Linear:
			y = self._LinearFunction(x, lowPoint.X, lowPoint.Y, highPoint.X, highPoint.Y)  # type: float
		else:
			y = self._BezierCurveFunction(x, lowPoint.X, lowPoint.Y, highPoint.X, highPoint.Y)  # type: float

		return y

	def EvaluateSingleInverse (self, y: float, lowerBound: typing.Union[float, None] = None, upperBound: typing.Union[float, None] = None) -> typing.Optional[float]:
		"""
		Get the first x value at which curve the crosses this y axis. This will return None if the curve never crosses the input y axis.
		:param y: The y axis to search for crossing points at.
		:param lowerBound: Limits the search to all x values greater than or equal to this number. Let this be none to have no lower bound for the search.
		:type lowerBound: float | int | None
		:param upperBound: Limits the search to all x values less than or equal to this number. Let this be none to have no upper bound for the search.
		:type upperBound: float | int | None
		"""

		foundPoints = self._EvaluateInverseInternal(y, lowerBound = lowerBound, upperBound = upperBound, findOne = True)  # type: typing.List[float]

		if len(foundPoints) == 0:
			return None

		foundPoint = foundPoints[0]  # type: float

		assert isinstance(foundPoint, (float, int))
		return foundPoint

	def EvaluateInverse (self, y: float, lowerBound: typing.Union[float, None] = None, upperBound: typing.Union[float, None] = None) -> typing.List[float]:
		"""
		Get a list of x values at which curve the crosses this y axis. This will return an empty list if the curve never crosses the input y axis.
		:param y: The y axis to search for crossing points at.
		:param lowerBound: Limits the search to all x values greater than or equal to this number. Let this be none to have no lower bound for the search.
		:type lowerBound: float | int | None
		:param upperBound: Limits the search to all x values less than or equal to this number. Let this be none to have no upper bound for the search.
		:type upperBound: float | int | None
		"""

		foundPoints = self._EvaluateInverseInternal(y, lowerBound = lowerBound, upperBound = upperBound, findOne = False)  # type: typing.List[float]
		return foundPoints

	def _EvaluateInverseInternal (
			self,
			y: float,
			lowerBound: typing.Union[float, None] = None,
			upperBound: typing.Union[float, None] = None,
			findOne: bool = False) -> typing.List[float]:

		if len(self._points) <= 0:
			return [0]

		xValues = list()  # type: typing.List[float]

		pointCount = len(self._points)  # type: int
		pointsMaxIndex = pointCount - 1  # type: int

		lastPoint = None  # type: typing.Optional[CurvePoint]
		point = self._points[0]  # type: CurvePoint
		nextPoint = self._points[1]  # type: CurvePoint

		def secantMethod (
				evaluationFunction: typing.Callable,
				secantLowX: float, secantLowY: float,
				secantHighX: float, secantHighY: float,
				secantLowerXBound: typing.Union[float, None], secantUpperXBound: typing.Union[float, None]) -> typing.Union[float, None]:

			secantX0 = secantLowerXBound  # type: float
			secantX1 = secantUpperXBound  # type: float

			secantY0 = evaluationFunction(secantX0, secantLowX, secantLowY, secantHighX, secantHighY) - y  # type: float
			secantY1 = evaluationFunction(secantX1, secantLowX, secantLowY, secantHighX, secantHighY) - y  # type: float

			if secantY0 > y or secantY1 < y:
				return None

			result = None  # type: typing.Union[None, float, int]

			for iteration in range(self.SecantMethodMaxIterations):  # type: int
				if iteration != 0:
					secantX0 = secantX1
					secantY0 = secantY1

					secantX1 = result
					secantY1 = evaluationFunction(result, secantLowX, secantLowY, secantHighX, secantHighY) - y

				if secantY1 == 0 or secantY0 == secantY1:
					result = secantX1
					break

				result = secantX1 - secantY1 * (secantX1 - secantX0) / (secantY1 - secantY0)

			assert result is not None

			return result

		for pointIndex in range(pointCount):
			if len(xValues) != 0 and findOne:
				break

			if pointIndex != 0:
				lastPoint = point  # type: typing.Optional[CurvePoint]
				point = nextPoint  # type: CurvePoint
				nextPoint = self._points[pointIndex + 1] if pointIndex != pointsMaxIndex else None  # type: typing.Optional[CurvePoint]

			if lowerBound is not None and (nextPoint is not None and nextPoint.X < lowerBound):
				continue

			if upperBound is not None and point.X > upperBound:
				continue

			if point.Y == y and \
					(lowerBound is None or point.X >= lowerBound) and \
					(lastPoint is None or lastPoint.Y != point.Y):

				xValues.append(point.X)

			if nextPoint is None:
				continue

			if nextPoint.Y == y:
				continue

			if not ((point.Y < y < nextPoint.Y) or (point.Y > y > nextPoint.Y)):
				continue

			if point.X == nextPoint.X:
				xValues.append(point.X)
				continue

			if point.ConnectionType == ConnectionType.Linear:
				xValues.append(self._LinearFunctionInverse(y, point.X, point.Y, nextPoint.X, nextPoint.Y))
				continue
			else:
				secantResult = secantMethod(self._BezierCurveFunction, point.X, point.Y, nextPoint.X, nextPoint.Y, lowerBound, upperBound)  # type: float

				if secantResult is None:
					continue

				xValues.append(secantResult)
				continue

		return xValues

	@staticmethod
	def _LinearFunction (
			x: float,
			lowX: float, lowY: float,
			highX: float, highY: float) -> float:

		if highX == lowX or highY == lowY:
			lineSlope = 0.0
		else:
			lineSlope = ((highY - lowY) / (highX - lowX))  # type: float

		return lowY + (x - lowX) * lineSlope

	@staticmethod
	def _LinearFunctionInverse (
			y: float,
			lowX: float, lowY: float,
			highX: float, highY: float) -> float:

		if highX == lowX or highY == lowY:
			lineSlope = 0.0
		else:
			lineSlope = ((highY - lowY) / (highX - lowX))  # type: float

		if lineSlope == 0:
			return lowX

		return (y - lowY) / lineSlope + lowX

	@staticmethod
	def _BezierCurveFunction (x: float,
							  lowX: float, lowY: float,
							  highX: float, highY: float) -> float:

		xDistance = highX - lowX  # type: float
		yDistance = highY - lowY  # type: float

		if xDistance != 0:
			return (3 * ((x - lowX) / xDistance) ** 2 - 2 * ((x - lowX) / xDistance) ** 3) * yDistance + lowY
		else:
			return (3 * (x - lowX) ** 2 - 2 * (x - lowX) ** 3) * yDistance + lowY

	def _SortPoints (self) -> None:
		self._points = sorted(self._points, key = lambda point: point.X)

class TunableCurvePoint(tunable.TunableSingletonFactory):
	FACTORY_TYPE = CurvePoint

	def __init__ (self, description = "A single point on a curved line.", **kwargs):
		super().__init__(
			description = description,
			x = tunable.Tunable(description = "The x value for this point.", tunable_type = float, default = 0),
			y = tunable.Tunable(description = "The y value for this point.", tunable_type = float, default = 0),
			connectionType = ToolsTunable.TunablePythonEnumEntry(description = "The type of connection this point has to the next point in the chain.", enumType = ConnectionType, default = ConnectionType.Linear),
			**kwargs)

class TunableCurve(tunable.TunableSingletonFactory):
	FACTORY_TYPE = Curve

	def __init__ (self, description = "A curved line graph.", **kwargs):
		super().__init__(
			description = description,
			points = tunable.TunableList(description = "The points that make up this curved line.", tunable = TunableCurvePoint()),
			**kwargs)
