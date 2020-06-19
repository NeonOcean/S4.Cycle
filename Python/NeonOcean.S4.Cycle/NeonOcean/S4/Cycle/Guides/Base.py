from __future__ import annotations

import typing

import snippets
from NeonOcean.S4.Main import Snippets as MainSnippets
from sims4.tuning import tunable

class GuideBase:
	"""
	An object for guiding reproductive systems in handling its sim.
	"""

	@classmethod
	def GetIdentifier (cls) -> str:
		"""
		Get an identifier that can be used to pick out a specific guide from a group.
		"""

		raise NotImplementedError()

class GuideTuningHandler:
	_snippetName: str

	Guide = None  # type: GuideBase

	def __init_subclass__ (cls, **kwargs):
		cls._SetupSnippet()

	@classmethod
	def _GetSnippetTemplate (cls) -> tunable.TunableBase:
		raise NotImplementedError()

	@classmethod
	def _SetupSnippet (cls) -> None:
		snippets.define_snippet(cls._snippetName, cls._GetSnippetTemplate())
		MainSnippets.SetupSnippetScanning(cls._snippetName, cls._SnippetTuningCallback)

	@classmethod
	def _SnippetTuningCallback (cls, guideSnippets: typing.List[snippets.SnippetInstanceMetaclass]) -> None:
		if len(guideSnippets) == 0:
			cls.Guide = cls._GetSnippetTemplate().default
			return

		cls.Guide = guideSnippets[0].value
