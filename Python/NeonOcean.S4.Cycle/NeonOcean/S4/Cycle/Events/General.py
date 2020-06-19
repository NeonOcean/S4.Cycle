from __future__ import annotations

import typing

from NeonOcean.S4.Cycle.Events import Base as EventsBase
from NeonOcean.S4.Main.Tools import Exceptions

class TrackerAddedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, tracker, *args, **kwargs):
		"""
		Event arguments for times when a tracker is added to a reproductive system.

		:param tracker: The tracker that has just been registered to the reproductive system.
		:type tracker: ReproductionShared.ReproductiveSystem
		"""

		from NeonOcean.S4.Cycle import ReproductionShared

		if not isinstance(tracker, ReproductionShared.TrackerBase):
			raise Exceptions.IncorrectTypeException(tracker, "tracker", (ReproductionShared.TrackerBase,))

		super().__init__(*args, **kwargs)

		self._tracker = tracker  # type: ReproductionShared.TrackerBase

	@property
	def Tracker (self):
		"""
		The tracker that has just been registered to the reproductive system.
		"""

		return self._tracker

class TrackerRemovedArguments(EventsBase.ReproductiveArguments):
	def __init__ (self, tracker, *args, **kwargs):
		"""
		Event arguments for times when a tracker is removed from a reproductive system.

		:param tracker: The tracker that has just been registered to the reproductive system.
		:type tracker: ReproductionShared.ReproductiveSystem
		"""

		from NeonOcean.S4.Cycle import ReproductionShared

		if not isinstance(tracker, ReproductionShared.TrackerBase):
			raise Exceptions.IncorrectTypeException(tracker, "tracker", (ReproductionShared.TrackerBase,))

		super().__init__(*args, **kwargs)

		self._tracker = tracker  # type: ReproductionShared.TrackerBase

	@property
	def Tracker (self):
		"""
		The tracker that has just been registered to the reproductive system.
		"""

		return self._tracker

class PlanUpdateArguments(EventsBase.ReproductiveArguments):
	def __init__(self, *args, **kwargs):
		"""
		Event arguments for times when we need to plan when the next update call should happen.
		"""

		super().__init__(*args, **kwargs)

		self._requestedTick = None

	@property
	def RequestedTick (self) -> typing.Optional[int]:
		"""
		The tick that we have requested the update to occur. This may be none if no request has been made.
		"""

		return self._requestedTick

	def RequestTick (self, tick: int, setTick: bool = False) -> None:
		"""
		Request that the next update call occur this many ticks into the future. If an earlier time has already been requested nothing will happen.
		:param tick: The number of game ticks into the future the update method should be called. This cannot be less than or equal to 0.
		:type tick: int
		:param setTick: Whether or not ignore previously requested ticks.
		:type setTick: bool
		"""

		if not isinstance(tick, (int, )):
			raise Exceptions.IncorrectTypeException(tick, "tick", (int, ))

		if not isinstance(setTick, bool):
			raise Exceptions.IncorrectTypeException(setTick, "setTick", (bool, ))

		if tick <= 0:
			raise ValueError("Attempted to request a tick less than or equal to 0.")

		if self._requestedTick is None or self._requestedTick > tick:
			self._requestedTick = tick