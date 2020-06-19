from __future__ import annotations

import types
import typing

import services
from NeonOcean.S4.Main import Debug, LoadingShared
from NeonOcean.S4.Main.Tools import Exceptions
from NeonOcean.S4.Cycle import Settings, This
from NeonOcean.S4.Cycle.Settings import Base as SettingsBase
from sims.aging import aging_service, aging_tuning
from sims4 import collections

def EnforceLifeSpanMultiplierSettings () -> None:
	SetLifeSpanMultipliers(short = Settings.LifeSpanShortMultiplier.Get(), normal = Settings.LifeSpanNormalMultiplier.Get(), long = Settings.LifeSpanLongMultiplier.Get())

def SetLifeSpanMultipliers (short: typing.Union[int, float, None] = None, normal: typing.Union[int, float, None] = None, long: typing.Union[int, float, None] = None) -> None:
	if not isinstance(short, int) and not isinstance(short, float) and short is not None:
		raise Exceptions.IncorrectTypeException(short, "short", (int, float, None))

	if not isinstance(normal, int) and not isinstance(normal, float) and normal is not None:
		raise Exceptions.IncorrectTypeException(normal, "normal", (int, float, None))

	if not isinstance(long, int) and not isinstance(long, float) and long is not None:
		raise Exceptions.IncorrectTypeException(long, "long", (int, float, None))

	currentMultipliers = aging_tuning.AgingTuning.AGE_SPEED_SETTING_MULTIPLIER

	if short is None:
		short = currentMultipliers[aging_tuning.AgeSpeeds.FAST]

	if normal is None:
		normal = currentMultipliers[aging_tuning.AgeSpeeds.NORMAL]

	if long is None:
		long = currentMultipliers[aging_tuning.AgeSpeeds.SLOW]

	if short != currentMultipliers[aging_tuning.AgeSpeeds.FAST] and normal != currentMultipliers[aging_tuning.AgeSpeeds.NORMAL] and long != currentMultipliers[aging_tuning.AgeSpeeds.SLOW]:
		return

	changingMultipliers = {
		aging_tuning.AgeSpeeds.FAST: short,
		aging_tuning.AgeSpeeds.NORMAL: normal,
		aging_tuning.AgeSpeeds.SLOW: long
	}

	# noinspection PyUnresolvedReferences
	newMultipliers = collections.frozendict(currentMultipliers.items(), **changingMultipliers)  # TODO way to revert
	aging_tuning.AgingTuning.AGE_SPEED_SETTING_MULTIPLIER = newMultipliers

	agingService = None  # type: typing.Optional[aging_service.AgingService]

	try:
		agingService = services.get_aging_service()  # type: aging_service.AgingService
	except Exception:
		pass

	if agingService is not None:
		agingService.set_aging_speed(agingService.aging_speed)

def ResetLifeSpanMultipliers () -> None:
	"""
	Reset the lifespan multipliers to what it was when this mod loaded.
	"""

	pass

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	#_SettingsOnUpdate()

	#Settings.RegisterOnUpdateCallback(_SettingsOnUpdate) #TODO fix up the lifespan settings and re-add these lines.

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	#Settings.RegisterOnUpdateCallback(_SettingsOnUpdate)

def _SettingsOnUpdate (owner: typing.Optional[types.ModuleType] = None, eventArguments: typing.Optional[SettingsBase.UpdateEventArguments] = None) -> None:
	_UpdateLifeSpanMultipliers(owner = owner, eventArguments = eventArguments)

# TODO maybe wait till the zone loads to change this stuff?

def _UpdateLifeSpanMultipliers (owner: typing.Optional[types.ModuleType] = None, eventArguments: typing.Optional[SettingsBase.UpdateEventArguments] = None) -> None:
	if owner:
		pass

	handlingSettings = [
		Settings.LifeSpanShortMultiplier,
		Settings.LifeSpanNormalMultiplier,
		Settings.LifeSpanLongMultiplier
	]

	def Changed (checkingSetting: Settings.SettingsBase) -> bool:
		if eventArguments is not None:
			if checkingSetting.Key in eventArguments.ChangedSettings:
				return True
			else:
				return False
		else:
			return True

	anySettingChanged = False  # type: bool

	for handlingSetting in handlingSettings:  # type: Settings.SettingsBase
		handlingSettingChanged = Changed(handlingSetting)  # type: bool

		if handlingSettingChanged:
			Debug.Log("Updating setting '" + handlingSetting.Key + "' to '" + str(handlingSetting.Get()) + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
			anySettingChanged = True

	if not anySettingChanged:
		return

	EnforceLifeSpanMultiplierSettings()
