from __future__ import annotations

import abc
import typing

from NeonOcean.S4.Cycle import ReproductionShared, This
from NeonOcean.S4.Main.Tools import Classes, Exceptions, Savable

_handlerTypes = list()  # type: typing.List[typing.Type[HandlerBase]]

class HandlerBase(abc.ABC, Savable.SavableExtension):
	HostNamespace = This.Mod.Namespace

	def __init__ (self, handlingSystem: ReproductionShared.ReproductiveSystem):
		if not isinstance(handlingSystem, ReproductionShared.ReproductiveSystem):
			raise Exceptions.IncorrectTypeException(handlingSystem, "handlingSystem", (ReproductionShared.ReproductiveSystem,))

		super().__init__()

		self._handlingSystem = handlingSystem

	# noinspection PyMethodParameters
	@Classes.ClassProperty
	@abc.abstractmethod
	def TypeIdentifier (cls) -> str:
		"""
		This handler type's identifier, this is used to save and load the handler. Loading will not be possible unless the cycle type is registered
		through the function in the handler types module.
		"""

		...

	@property
	def HandlingSystem (self) -> ReproductionShared.ReproductiveSystem:
		"""
		The reproductive system this object is handling.
		"""

		return self._handlingSystem

	@property
	def ShouldSave (self) -> bool:
		"""
		Whether or not we should save this handler.
		"""

		if len(self._savables) == 0:
			return False

		return True

	def Simulate (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		"""
		Simulate this many ticks in this object, invoking any events that occurred.
		:param simulation: The simulation object that is guiding this simulation.
		:type simulation: ReproductionShared.Simulation
		:param ticks: The number of ticks to simulate.
		:type ticks: int
		:param reproductiveTimeMultiplier: Divided by the amount of game time that the ticks count for to get the amount of time to simulate. All reproductive
		simulations work in real-life time.
		:type reproductiveTimeMultiplier: float
		"""

		if not isinstance(simulation, ReproductionShared.Simulation):
			raise Exceptions.IncorrectTypeException(simulation, "simulation", (ReproductionShared.Simulation,))

		if not isinstance(ticks, int):
			raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

		if not isinstance(reproductiveTimeMultiplier, (float, int)):
			raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

		if ticks <= 0:
			return

		if reproductiveTimeMultiplier <= 0:
			raise ValueError("The parameter 'reproductiveTimeMultiplier' cannot be less than or equal to 0.")

		self._SimulateInternal(simulation, ticks, reproductiveTimeMultiplier)

	def PlanSimulation (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: float) -> None:
		"""
		Plan out a simulation. Any tick that needs to be stopped at within the simulation's remaining ticks will to be added to the schedule. This method may be called
		more than once in a single simulation in order to replan any time remaining.
		:param simulation: The simulation object that needs to be worked on.
		:type simulation: Simulation
		:param reproductiveTimeMultiplier: Divided by the amount of game time that the ticks count for to get the amount of time to simulate.  All reproductive
		simulations work in real-life time
		:type reproductiveTimeMultiplier: float
		"""

		if not isinstance(simulation, ReproductionShared.Simulation):
			raise Exceptions.IncorrectTypeException(simulation, "simulation", (ReproductionShared.Simulation,))

		if not isinstance(reproductiveTimeMultiplier, (float, int)):
			raise Exceptions.IncorrectTypeException(reproductiveTimeMultiplier, "reproductiveTimeMultiplier", (float, int))

		self._PlanSimulationInternal(simulation, reproductiveTimeMultiplier)

	def _OnAdding (self) -> None:
		"""
		Called when the handler is about to be officially added to the handler tracker.
		"""

		pass

	def _OnAdded (self) -> None:
		"""
		Called when the handler has been officially added to the handler tracker.
		"""

		pass

	def _OnRemoving (self) -> None:
		"""
		Called when the handler is about to be removed from the handler tracker.
		"""

		pass

	def _OnRemoved (self) -> None:
		"""
		Called when the handler has been removed from the handler tracker.
		"""

		pass

	def _SimulateInternal (self, simulation: ReproductionShared.Simulation, ticks: int, reproductiveTimeMultiplier: float) -> None:
		pass

	def _PlanSimulationInternal (self, simulation: ReproductionShared.Simulation, reproductiveTimeMultiplier: float) -> None:
		pass


