from __future__ import annotations

import sys
import random
import typing
import time

from NeonOcean.S4.Cycle import ReproductionShared, Saving, This
from NeonOcean.S4.Main import Debug
from NeonOcean.S4.Main.Saving import SectionBranched
from NeonOcean.S4.Main.Tools import Events, Exceptions, Python, Types
from sims import sim_info

RegisteredReproductiveSystemEvent = Events.EventHandler()  # type: Events.EventHandler
UnregisteredReproductiveSystemEvent = Events.EventHandler()  # type: Events.EventHandler #The event arguments will be of the type RegistrationChangedArguments for both of these.

_reproductiveSystems = dict()  # type: typing.Dict[sim_info.SimInfo, ReproductionShared.ReproductiveSystem]

_fullUpdateTimes = list()  # type: typing.List[float]
_individualUpdateTimes = list()  # type: typing.List[float]

# TODO let the reset interaction to reset the save.

class RegistrationChangedArguments(Events.EventArguments):
	def __init__ (self, reproductiveSystem: ReproductionShared.ReproductiveSystem):
		if not isinstance(reproductiveSystem, ReproductionShared.ReproductiveSystem):
			raise Exceptions.IncorrectTypeException(reproductiveSystem, "reproductiveSystem", (ReproductionShared.ReproductiveSystem,))

		self.ReproductiveSystem = reproductiveSystem

def RegisterReproductiveSystem (reproductiveSystem: ReproductionShared.ReproductiveSystem) -> None:
	"""
	Register a reproductive system to be handled. If a reproductive system is already registered for the system's sim, it will be replaced.
	:param reproductiveSystem: The reproductive system in question.
	:type reproductiveSystem: ReproductionShared.ReproductiveSystem
	"""

	if not isinstance(reproductiveSystem, ReproductionShared.ReproductiveSystem):
		raise Exceptions.IncorrectTypeException(reproductiveSystem, "reproductiveSystem", (ReproductionShared.ReproductiveSystem,))

	_reproductiveSystems[reproductiveSystem.SimInfo] = reproductiveSystem  # type: ReproductionShared.ReproductiveSystem
	InvokeRegisteredReproductiveSystemEvent(reproductiveSystem)

def UnregisterReproductiveSystem (reproductiveSystem: ReproductionShared.ReproductiveSystem) -> None:
	"""
	Unregister a previously registered reproductive system.
	:param reproductiveSystem: The reproductive system in question.
	:type reproductiveSystem: ReproductionShared.ReproductiveSystem
	"""

	if not isinstance(reproductiveSystem, ReproductionShared.ReproductiveSystem):
		raise Exceptions.IncorrectTypeException(reproductiveSystem, "reproductiveSystem", (ReproductionShared.ReproductiveSystem,))

	_reproductiveSystems.pop(reproductiveSystem.SimInfo, None)

	InvokeUnregisteredReproductiveSystemEvent(reproductiveSystem)

def InitiateReproductiveSystem (simInfo: sim_info.SimInfo) -> ReproductionShared.ReproductiveSystem:
	"""
	Create a blank reproductive system for this sim. If one already exists the existing one will be returned as opposed of creating a new one.
	:param simInfo: The target sim's info.
	:type simInfo: sim_info.SimInfo
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	if SimHasSystem(simInfo):
		return GetSimSystem(simInfo)

	simReproductiveSystem = ReproductionShared.ReproductiveSystem(simInfo)
	RegisterReproductiveSystem(simReproductiveSystem)

	return simReproductiveSystem

def GetSimSystem (simInfo: sim_info.SimInfo, automaticallyUpdate: bool = True) -> typing.Optional[ReproductionShared.ReproductiveSystem]:
	"""
	Get the registered reproductive systems associated with this sim. This can return none if not system exists.
	:param simInfo: The target sim's info.
	:type simInfo: sim_info.SimInfo
	:param automaticallyUpdate: Whether or not this function should automatically update the retrieved reproductive system. If this is disabled it is
	recommended to manually update the system before using it.
	:type automaticallyUpdate: bool
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	reproductiveSystem = _reproductiveSystems.get(simInfo, None)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

	if reproductiveSystem is not None and automaticallyUpdate:
		UpdateSystems([reproductiveSystem])

	return reproductiveSystem

def GetAllSystems (automaticallyUpdate: bool = True) -> typing.List[ReproductionShared.ReproductiveSystem]:
	"""
	Get all registered reproductive systems.
	:param automaticallyUpdate: Whether or not this function should automatically update all retrieved reproductive systems. If this is disabled it is
	recommended to manually update any reproductive system before using them.
	:type automaticallyUpdate: bool
	:return: All registered reproductive system objects.
	:rtype: list
	"""

	reproductiveSystems = list(_reproductiveSystems.values())  # type: list

	if automaticallyUpdate:
		UpdateSystems(reproductiveSystems)

	return reproductiveSystems

def SimHasSystem (simInfo: sim_info.SimInfo) -> bool:
	"""
	Get whether or not a reproductive system exists for this sim.
	:param simInfo: The target sim's info.
	:type simInfo: sim_info.SimInfo
	"""

	return GetSimSystem(simInfo, automaticallyUpdate = False) is not None

def RemoveSimSystem (simInfo: sim_info.SimInfo) -> None:
	"""
	Unregister the registered reproductive systems associated with this sim.
	:param simInfo: The target sim's info.
	:type simInfo: sim_info.SimInfo
	"""

	if not isinstance(simInfo, sim_info.SimInfo):
		raise Exceptions.IncorrectTypeException(simInfo, "simInfo", (sim_info.SimInfo,))

	_reproductiveSystems.pop(simInfo, None)

def LoadAllSystems (simsSection: SectionBranched.SectionBranched = None) -> bool:
	"""
	Load all reproductive system data in this saving section.
	:param simsSection: The sims saving section the reproductive systems will be written to. If this is none this method will use Cycle's main sim saving section.
	:type simsSection: None | SectionSims.SectionSims
	:return: This function will return False if an error occurred. Otherwise this function will return True if it behaved as expected.
	:rtype: bool
	"""

	if not isinstance(simsSection, SectionBranched.SectionBranched) and simsSection is not None:
		raise Exceptions.IncorrectTypeException(simsSection, "simsSection", (SectionBranched.SectionBranched, "None"))

	operationSuccessful = True  # type: bool

	if simsSection is None:
		simsSection = Saving.GetSimsSection()  # type: SectionBranched.SectionBranched

	allReproductiveSystems = GetAllSystems()  # type: typing.List[ReproductionShared.ReproductiveSystem]

	for reproductiveSystem in allReproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		try:
			if not reproductiveSystem.Load(simsSection):
				operationSuccessful = False
		except:
			Debug.Log("Failed to load a reproductive system.\n." + reproductiveSystem.DebugInformation, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			operationSuccessful = False

	return operationSuccessful

def SaveAllSystems (simsSection: SectionBranched.SectionBranched = None) -> bool:
	"""
	Save all reproductive system data to this saving section.
	:param simsSection: The sims saving section the reproductive systems will be written to. If this is none this method will use Cycle's main sim saving section.
	:type simsSection: None | SectionSims.SectionSims
	:return: This function will return False if an error occurred. Otherwise this function will return True if it behaved as expected.
	:rtype: bool
	"""

	if not isinstance(simsSection, SectionBranched.SectionBranched) and simsSection is not None:
		raise Exceptions.IncorrectTypeException(simsSection, "simsSection", (SectionBranched.SectionBranched, "None"))

	operationSuccessful = True  # type: bool

	if simsSection is None:
		simsSection = Saving.GetSimsSection()  # type: SectionBranched.SectionBranched

	allReproductiveSystems = GetAllSystems()  # type: typing.List[ReproductionShared.ReproductiveSystem]

	for reproductiveSystem in allReproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		try:
			if not reproductiveSystem.Save(simsSection):
				operationSuccessful = False
		except:
			Debug.Log("Failed to save a reproductive system.\n." + reproductiveSystem.DebugInformation, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			operationSuccessful = False

	return operationSuccessful

def ResetSystems (reproductiveSystems: typing.Optional[typing.Iterable[ReproductionShared.ReproductiveSystem]] = None) -> bool:
	"""
	Reset all specified reproductive systems.
	:param reproductiveSystems: All reproductive systems that need to be reset. If this is None the function will go through all registered reproductive systems.
	:type reproductiveSystems: typing.Iterable[ReproductionShared.ReproductiveSystem] | None
	:return: This function will return False if an error occurred. Otherwise this function will return True if it behaved as expected.
	:rtype: bool
	"""

	operationSuccessful = True  # type: bool

	if reproductiveSystems is None:
		reproductiveSystems = GetAllSystems(automaticallyUpdate = False)

	for reproductiveSystem in reproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		try:
			if not reproductiveSystem.Reset():
				operationSuccessful = False
		except:
			Debug.Log("Failed to reset a reproductive system.\n." + reproductiveSystem.DebugInformation, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			operationSuccessful = False

	return operationSuccessful

def VerifySystems (reproductiveSystems: typing.Optional[typing.Iterable[ReproductionShared.ReproductiveSystem]] = None) -> None:
	"""
	Verify that all specified reproductive systems should exist and that their values are valid.
	:param reproductiveSystems: All reproductive systems that need to be verified. If this is None the function will go through all registered reproductive systems.
	:type reproductiveSystems: typing.Iterable[ReproductionShared.ReproductiveSystem] | None
	"""

	if reproductiveSystems is None:
		reproductiveSystems = GetAllSystems(automaticallyUpdate = False)

	for reproductiveSystem in reproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		reportLockIdentifier = __name__ + ":" + str(Python.GetLineNumber())  # type: str
		reportLockReference = reproductiveSystem

		try:
			if not reproductiveSystem.ShouldExist:
				UnregisterReproductiveSystem(reproductiveSystem)
				continue

			reproductiveSystem.Verify()
		except:
			Debug.Log("Failed to verify a reproductive system.\n" + reproductiveSystem.DebugInformation,
					  This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = reportLockIdentifier, lockReference = reportLockReference)
		else:
			Debug.Unlock(reportLockIdentifier, reportLockReference)

def UpdateSystems (reproductiveSystems: typing.Optional[typing.Iterable[ReproductionShared.ReproductiveSystem]] = None) -> None:
	"""
	Update all specified reproductive systems.
	:param reproductiveSystems: All reproductive systems that need to be updated. If this is None the function will go through all registered reproductive systems.
	:type reproductiveSystems: typing.Iterable[ReproductionShared.ReproductiveSystem] | None
	"""

	if reproductiveSystems is None:
		reproductiveSystems = GetAllSystems(automaticallyUpdate = False)

	if len(reproductiveSystems) == 0:
		return

	updateTimedRoll = random.random()  # type: float
	updateTimedProbability = 0.125  # type: float

	maximumSavedUpdateTimes = 200  # type: int

	if len(_fullUpdateTimes) == 0:
		updateTimed = True
	else:
		updateTimed = len(_fullUpdateTimes) != maximumSavedUpdateTimes and updateTimedRoll <= updateTimedProbability  # type: bool

	if updateTimed:
		fullUpdateStartTime = time.time()  # type: typing.Optional[float]
		chosenTimedSystem = random.choice(reproductiveSystems)  # type: typing.Optional[ReproductionShared.ReproductiveSystem]
	else:
		fullUpdateStartTime = None  # type: typing.Optional[float]
		chosenTimedSystem = None  # type: typing.Optional[ReproductionShared.ReproductiveSystem]

	for reproductiveSystem in reproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		reportLockIdentifier = __name__ + ":" + str(Python.GetLineNumber())  # type: str
		reportLockReference = reproductiveSystem

		if updateTimed and reproductiveSystem is chosenTimedSystem:
			individualUpdateStartTime = time.time()  # type: typing.Optional[float]
		else:
			individualUpdateStartTime = None  # type: typing.Optional[float]

		try:
			if reproductiveSystem.ShouldUpdate:
				reproductiveSystem.Update()
		except:
			Debug.Log("Failed to update a reproductive system\n." + reproductiveSystem.DebugInformation, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = reportLockIdentifier, lockReference = reportLockReference)
		else:
			Debug.Unlock(reportLockIdentifier, reportLockReference)

		if individualUpdateStartTime is not None:
			_individualUpdateTimes.append(time.time() - individualUpdateStartTime)

	if fullUpdateStartTime is not None:
		_fullUpdateTimes.append(time.time() - fullUpdateStartTime)

def SimulateSystems (ticks: int, reproductiveSystems: typing.Optional[typing.Iterable[ReproductionShared.ReproductiveSystem]] = None) -> None:
	"""
	Simulate this many ticks in the specified reproductive systems. All out of date reproductive systems will be updated before simulating.
	:param ticks: The number of ticks to simulate.
	:type ticks: int
	:param reproductiveSystems: All reproductive systems that need to be simulated. If this is None the function will go through all registered reproductive systems.
	:type reproductiveSystems: typing.Iterable[ReproductionShared.ReproductiveSystem] | None
	"""

	if not isinstance(ticks, int):
		raise Exceptions.IncorrectTypeException(ticks, "ticks", (int,))

	if reproductiveSystems is None:
		reproductiveSystems = GetAllSystems()

	for reproductiveSystem in reproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		reportLockIdentifier = __name__ + ":" + str(Python.GetLineNumber())  # type: str
		reportLockReference = reproductiveSystem

		try:
			reproductiveSystem.Simulate(ticks)
		except:
			Debug.Log("Failed to simulate a reproductive system\n." + reproductiveSystem.DebugInformation, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = reportLockIdentifier, lockReference = reportLockReference)
		else:
			Debug.Unlock(reportLockIdentifier, reportLockReference)

def GetUpdateTicks (maximumTick: int, reproductiveSystems: typing.Optional[typing.Iterable[ReproductionShared.ReproductiveSystem]] = None) -> typing.Dict[int, typing.List[ReproductionShared.ReproductiveSystem]]:
	"""
	Get a dictionary of ticks paired with lists of reproductive systems that should update on them.
	:param maximumTick: Planned updates beyond this tick will be ignored.
	:type maximumTick: int
	:param reproductiveSystems: The reproductive systems to get an update tick for. If this is None the function will go through all registered reproductive systems.
	:type reproductiveSystems: typing.Iterable[ReproductionShared.ReproductiveSystem] | None
	"""

	if reproductiveSystems is None:
		reproductiveSystems = GetAllSystems()

	updateTicks = dict()  # type: typing.Dict[int, typing.List[ReproductionShared.ReproductiveSystem]]

	for reproductiveSystem in reproductiveSystems:  # type: ReproductionShared.ReproductiveSystem
		reportLockIdentifier = __name__ + ":" + str(Python.GetLineNumber())  # type: str
		reportLockReference = reproductiveSystem

		try:
			planUpdateArguments = reproductiveSystem.PlanUpdate()

			plannedTick = planUpdateArguments.RequestedTick

			if plannedTick is None or plannedTick >= maximumTick:
				plannedTick = maximumTick

			plannedTickSystems = updateTicks.get(plannedTick, None)  # type: typing.Optional[typing.List[ReproductionShared.ReproductiveSystem]]

			if plannedTickSystems is None:
				plannedTickSystems = list()
				updateTicks[plannedTick] = plannedTickSystems

			plannedTickSystems.append(reproductiveSystem)
		except:
			Debug.Log("Failed to plan the update of a reproductive system\n." + reproductiveSystem.DebugInformation, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, lockIdentifier = reportLockIdentifier, lockReference = reportLockReference)
		else:
			Debug.Unlock(reportLockIdentifier, reportLockReference)

	return updateTicks

def InvokeRegisteredReproductiveSystemEvent (reproductiveSystem: ReproductionShared.ReproductiveSystem) -> None:
	thisModule = sys.modules[__name__]
	registeredArguments = RegistrationChangedArguments(reproductiveSystem)

	for registeredEventCallback in RegisteredReproductiveSystemEvent:
		try:
			registeredEventCallback(thisModule, registeredArguments)
		except:
			Debug.Log("Failed to run registered reproductive system event callback " + Types.GetFullName(registeredEventCallback), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

def InvokeUnregisteredReproductiveSystemEvent (reproductiveSystem: ReproductionShared.ReproductiveSystem) -> None:
	thisModule = sys.modules[__name__]
	registeredArguments = RegistrationChangedArguments(reproductiveSystem)

	for unregisteredEventCallback in UnregisteredReproductiveSystemEvent:
		try:
			unregisteredEventCallback(thisModule, registeredArguments)
		except:
			Debug.Log("Failed to run unregistered reproductive system event callback " + Types.GetFullName(unregisteredEventCallback), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

# noinspection PyUnusedLocal
def _OnStop (cause) -> None:
	if len(_fullUpdateTimes) != 0:
		averageFullUpdateTime = round(sum(_fullUpdateTimes) / len(_fullUpdateTimes), 5)  # type: float

		Debug.Log("Average full reproductive system update time for session: %s seconds." % str(averageFullUpdateTime), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	if len(_individualUpdateTimes) != 0:
		averageIndividualUpdateTime = round(sum(_individualUpdateTimes) / len(_individualUpdateTimes), 5)  # type: float


		Debug.Log("Average individual reproductive system update time for session: %s seconds." % str(averageIndividualUpdateTime), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
