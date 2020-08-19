from __future__ import annotations

import typing

from NeonOcean.S4.Main.Tools import Savable, Exceptions, Version

class OvumRelease(Savable.SavableExtension):
	_baseReleaseMinuteSavingKey = "BaseReleaseMinute"  # type: str
	_baseReleaseMinuteOldSavingKey = "ReleaseMinute"  # type: str

	def __init__(self):
		"""
		An object to keep track of the release of an individual ovum during a cycle.
		"""

		super().__init__()

		self.BaseReleaseMinute = 20160
		self.ReleaseDelay = 0

		self.Released = False

		self._releaseGuarantors = list()  # type: typing.List[str]
		self._blockGuarantors = list()  # type: typing.List[str]

		self._releaseMinuteGuarantors = list()  # type: typing.List[str]

		# noinspection PyUnusedLocal
		def releaseMinuteUpdater (data: dict, lastVersion: typing.Optional[Version.Version]) -> None:
			if self._baseReleaseMinuteOldSavingKey in data and not self._baseReleaseMinuteSavingKey in data:
				data[self._baseReleaseMinuteSavingKey] = data[self._baseReleaseMinuteOldSavingKey]

		def releaseGuarantorsTypeVerifier (value: typing.List[str]) -> None:
			if not isinstance(value, list):
				raise Exceptions.IncorrectTypeException(value, "ReleaseGuarantors", (list, ))

			for guarantorIndex in range(len(value)):  # type: int
				guarantor = value[guarantorIndex]  # type: str

				if not isinstance(guarantor, str):
					raise Exceptions.IncorrectTypeException(value, "ReleaseGuarantors[%s]" % guarantorIndex, (str, ))

		def blockGuarantorsTypeVerifier (value: typing.List[str]) -> None:
			if not isinstance(value, list):
				raise Exceptions.IncorrectTypeException(value, "BlockGuarantors", (list, ))

			for guarantorIndex in range(len(value)):  # type: int
				guarantor = value[guarantorIndex]  # type: str

				if not isinstance(guarantor, str):
					raise Exceptions.IncorrectTypeException(value, "BlockGuarantors[%s]" % guarantorIndex, (str, ))

		def releaseMinuteGuarantorsTypeVerifier (value: typing.List[str]) -> None:
			if not isinstance(value, list):
				raise Exceptions.IncorrectTypeException(value, "ReleaseMinuteGuarantors", (list, ))

			for guarantorIndex in range(len(value)):  # type: int
				guarantor = value[guarantorIndex]  # type: str

				if not isinstance(guarantor, str):
					raise Exceptions.IncorrectTypeException(value, "ReleaseMinuteGuarantors[%s]" % guarantorIndex, (str, ))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BaseReleaseMinute", "BaseReleaseMinute", self.ReleaseMinute, requiredAttribute = True, updater = releaseMinuteUpdater))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("ReleaseDelay", "ReleaseDelay", self.ReleaseDelay, requiredAttribute = True))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Released", "Released", self.Released))

		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("ReleaseGuarantors", "_releaseGuarantors", list(), typeVerifier = releaseGuarantorsTypeVerifier))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BlockGuarantors", "_blockGuarantors", list(), typeVerifier = blockGuarantorsTypeVerifier))
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("ReleaseMinuteGuarantors", "_releaseMinuteGuarantors", list(), typeVerifier = releaseMinuteGuarantorsTypeVerifier))

	@property
	def ReleaseMinute (self) -> float:
		"""
		The number of reproductive minutes into a cycle this object indicates there should be an ovum release. #TODO update
		"""

		return self.BaseReleaseMinute + self.ReleaseDelay

	@property
	def BaseReleaseMinute (self) -> float:
		"""
		The number of reproductive minutes into a cycle this object indicates there should be an ovum release, as long as its not modified by something else, such as delay.
		"""

		return self._baseReleaseMinute

	@BaseReleaseMinute.setter
	def BaseReleaseMinute (self, value: float) -> None:
		"""
		The number of reproductive minutes into a cycle this object indicates there should be an ovum release.
		"""

		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "BaseReleaseMinute", (float, int))

		self._baseReleaseMinute = value

	@property
	def ReleaseDelay (self) -> float:
		"""
		The amount of time in reproductive minutes that this ovum should be delayed by. This cannot be less than 0.
		"""

		return self._releaseDelay

	@ReleaseDelay.setter
	def ReleaseDelay (self, value: bool) -> None:
		if not isinstance(value, (float, int)):
			raise Exceptions.IncorrectTypeException(value, "ReleaseDelay", (float, int))

		if value < 0:
			raise ValueError("ReleaseDelay values cannot be less than to 0.")

		self._releaseDelay = value

	@property
	def Released (self) -> bool:
		"""
		Whether or not an ovum has already been released for this object.
		"""

		return self._released

	@Released.setter
	def Released (self, value: bool) -> None:
		if not isinstance(value, (bool, )):
			raise Exceptions.IncorrectTypeException(value, "ReleaseMinute", (bool, ))

		self._released = value

	def GuaranteeRelease (self, guarantorIdentifier: str) -> None:
		"""
		Indicate that the release of this particular ovum is guaranteed by a particular system. This doesn't mean that the ovum won't be stopped, just that this
		system should not try to stop it when it does.
		:param guarantorIdentifier: A unique identifier for the system guaranteeing the ovum's release. This identifier should also be used by the system too check if
		it previously guaranteed the ovum.
		:type guarantorIdentifier: str
		"""

		if not isinstance(guarantorIdentifier, str):
			raise Exceptions.IncorrectTypeException(guarantorIdentifier, "guarantorIdentifier", (str, ))

		if not guarantorIdentifier in self._releaseGuarantors:
			self._releaseGuarantors.append(guarantorIdentifier)

	def IsReleaseGuaranteed (self, guarantorIdentifier: str) -> bool:
		"""
		Get whether or not this ovum's release has been guaranteed by a system with this identifier.
		:param guarantorIdentifier: The unique identifier used by the system to guarantee the ovum's release.
		"""

		if not isinstance(guarantorIdentifier, str):
			raise Exceptions.IncorrectTypeException(guarantorIdentifier, "guarantorIdentifier", (str, ))

		return guarantorIdentifier in self._releaseGuarantors

	def GuaranteeBlock (self, guarantorIdentifier: str) -> None:
		"""
		Indicate that the release of this particular ovum is guaranteed to be blocked by a particular system.
		:param guarantorIdentifier: A unique identifier for the system guaranteeing the ovum's block. This identifier should also be used by the system too check if
		it previously guaranteed the ovum.
		:type guarantorIdentifier: str
		"""

		if not isinstance(guarantorIdentifier, str):
			raise Exceptions.IncorrectTypeException(guarantorIdentifier, "guarantorIdentifier", (str, ))

		if not guarantorIdentifier in self._blockGuarantors:
			self._blockGuarantors.append(guarantorIdentifier)

	def IsBlockGuaranteed (self, guarantorIdentifier: str) -> bool:
		"""
		Get whether or not this ovum's release has been guaranteed to be blocked by a system with this identifier.
		:param guarantorIdentifier: The unique identifier used by the system to guarantee the ovum's block.
		"""

		if not isinstance(guarantorIdentifier, str):
			raise Exceptions.IncorrectTypeException(guarantorIdentifier, "guarantorIdentifier", (str, ))

		return guarantorIdentifier in self._blockGuarantors

	def GuaranteeReleaseMinute (self, guarantorIdentifier: str) -> None:
		"""
		Indicate that the release minute of this particular ovum is guaranteed by a particular system. This doesn't mean that the ovum won't be delayed, just that
		this system should not try to delay it when it does.
		:param guarantorIdentifier: A unique identifier for the system guaranteeing the ovum's release minute. This identifier should also be used by the system
		too check if it previously guaranteed the ovum.
		:type guarantorIdentifier: str
		"""

		if not isinstance(guarantorIdentifier, str):
			raise Exceptions.IncorrectTypeException(guarantorIdentifier, "guarantorIdentifier", (str, ))

		if not guarantorIdentifier in self._releaseMinuteGuarantors:
			self._releaseMinuteGuarantors.append(guarantorIdentifier)

	def IsReleaseMinuteGuaranteed (self, guarantorIdentifier: str) -> bool:
		"""
		Get whether or not this ovum's release minute has been guaranteed by a system with this identifier.
		:param guarantorIdentifier: The unique identifier used by the system to guarantee the ovum's release minute.
		"""

		if not isinstance(guarantorIdentifier, str):
			raise Exceptions.IncorrectTypeException(guarantorIdentifier, "guarantorIdentifier", (str, ))

		return guarantorIdentifier in self._releaseMinuteGuarantors