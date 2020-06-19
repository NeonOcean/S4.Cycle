from __future__ import annotations

import typing

import game_services
import services
from NeonOcean.S4.Main.Tools import Exceptions, Savable
from sims import sim_info, sim_info_manager

class SimPointer(Savable.SavableExtension):
	def __init__ (self):
		super().__init__()

		self.SimID = None
		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("SimID", "SimID", None, requiredSuccess = False))

	@property
	def SimID (self) -> typing.Optional[int]:
		"""
		The id of the sim this sim point object targets. This will be used to find the original sim, if they still exist.
		"""

		return self._simID

	@SimID.setter
	def SimID (self, value: typing.Optional[int]) -> None:
		if not isinstance(value, int) and value is not None:
			raise Exceptions.IncorrectTypeException(value, "SimID", (int, None))

		self._simID = value

	@property
	def SimExists (self) -> bool:
		"""
		Whether or not the sim this object points to still exists. This will always return false if this pointer's sim id is none or the
		service manager isn't available.
		"""

		if game_services.service_manager is None:
			return False

		if self.SimID is None:
			return False

		simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager
		originalSim = simInfoManager.get(self.SimID)  # type: sim_info.SimInfo

		return originalSim is not None

	def ChangePointer (self, simInfoOrID: typing.Union[int, sim_info.SimInfo, None]) -> None:
		"""
		Change the sim that this pointer object targets.
		:param simInfoOrID: The sim info object or the sim id of the new sim to point to.
		:type simInfoOrID: int | sim_info.SimInfo | None
		"""

		if not isinstance(simInfoOrID, (int, sim_info.SimInfo)) and simInfoOrID is not None:
			raise Exceptions.IncorrectTypeException(simInfoOrID, "simInfoOrID", (int, sim_info.SimInfo, None))

		if isinstance(simInfoOrID, sim_info.SimInfo):
			simInfoOrID = simInfoOrID.id  # type: int

		self.SimID = simInfoOrID

	def GetSim (self) -> typing.Optional[sim_info.SimInfo]:
		"""
		Get the sim this object points to. An exception will be raised if the service manager is not available.
		"""

		if game_services.service_manager is None:
			raise Exception("Cannot get a sim while the service manager is not available.")

		if self.SimID is not None:
			simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager
			originalSim = simInfoManager.get(self.SimID)  # type: sim_info.SimInfo

			if originalSim is not None:
				return originalSim

		return None

def CreatePointerFor (simInfo: sim_info.SimInfo) -> SimPointer:
	"""
	Create a sim pointer for this currently existing sim.
	"""

	simPointer = SimPointer()  # type: SimPointer
	simPointer.ChangePointer(simInfo)

	return simPointer

# An experimental version of the sim pointer that can allow for the cloning / recreation of the original sim.
#
#
#
# import copy
# import enum_lib
# import typing
#
# import game_services
# import services
# from NeonOcean.S4.Cycle import This
# from NeonOcean.S4.Cycle.Tools import Savable
# from NeonOcean.S4.Main.Tools import Exceptions, Parse
# from sims import genealogy_tracker, sim_info, sim_info_manager, sim_info_types, sim_spawner
#
# class InformationCategories(enum_lib.IntFlag):
# 	"""
# 	An enum to control the amount of information about a sim to be stored in a pointer.
# 	"""
#
# 	Nothing = 1  # type: InformationCategories
# 	Name = 2  # type: InformationCategories
# 	Basic = 4  # type: InformationCategories  # Their breed, gender, age, and species.
# 	Genetic = 8  # type: InformationCategories  # Information to create offspring for this sim.
# 	Appearance = 16  # type: InformationCategories  # Information to create a sim that looks and sounds near identical to the original.
# 	Traits = 32  # type: InformationCategories
# 	Everything = Name | Basic | Genetic | Appearance | Traits  # type: InformationCategories
#
# class SimPointer(Savable.SavableExtension):
# 	CreationSource = This.Mod.Namespace + "-Sim_Pointer"  # type: str
#
# 	def __init__ (self):
# 		"""
# 		An object to store information about a sim. This can be used to find the original or create a clone in the event the original was deleted.
# 		"""
#
# 		super().__init__()
#
# 		self.SimID = None
#
# 		self.Age = None  # type: typing.Optional[sim_info_types.Age]
# 		self.Gender = None  # type: typing.Optional[sim_info_types.Gender]
# 		self.Species = None  # type: typing.Optional[sim_info_types.SpeciesExtended]
#
# 		self.FirstName = None  # type: typing.Optional[str]
# 		self.FirstNameKey = None  # type: typing.Optional[int]
# 		self.LastName = None  # type: typing.Optional[str]
# 		self.LastNameKey = None  # type: typing.Optional[int]
# 		self.FullNameKey = None  # type: typing.Optional[int]
# 		self.BreedName = None  # type: typing.Optional[str]
# 		self.BreedNameKey = None  # type: typing.Optional[str]
#
# 		self.BaseTraitIDs = None  # type: typing.Optional[typing.List[int]]
# 		self.FacialAttributes = None  # type: typing.Optional[bytes]
# 		self.FamilyRelations = None  # type: typing.Optional[typing.Dict[genealogy_tracker.FamilyRelationshipIndex, int]]
# 		self.Flags = None  # type: typing.Optional[int]
# 		self.GeneticData = None  # type: typing.Optional[bytes]
# 		self.Outfits = None  # type: typing.Optional[bytes]
# 		self.PeltLayers = None  # type: typing.Optional[bytes]
# 		self.Physique = None  # type: typing.Optional[str]
# 		self.SkinTone = None  # type: typing.Optional[int]
# 		self.VoiceActor = None  # type: typing.Optional[int]
# 		self.VoiceEffect = None  # type: typing.Optional[int]
# 		self.VoicePitch = None  # type: typing.Optional[typing.Union[float, int]]
#
# 		encodeEnum = lambda value: value.name if value is not None else None
# 		decodeAge = lambda valueString: Parse.ParseS4Enum(valueString, sim_info_types.Age) if valueString is not None else None
# 		decodeGender = lambda valueString: Parse.ParseS4Enum(valueString, sim_info_types.Gender) if valueString is not None else None
# 		decodeSpecies = lambda valueString: Parse.ParseS4Enum(valueString, sim_info_types.SpeciesExtended) if valueString is not None else None
#
# 		encodeBytes = lambda value: value.hex() if value is not None else None
# 		decodeBytes = lambda valueString: bytes.fromhex(valueString) if valueString is not None else None
#
# 		encodeOptionalBytes = lambda value: value.hex() if value is not None else None
# 		decodeOptionalBytes = lambda valueString: bytes.fromhex(valueString) if valueString is not None else None
#
# 		def encodeFamilyRelations (familyRelations: typing.Optional[dict]) -> typing.Optional[dict]:
# 			if familyRelations is None:
# 				return None
#
# 			encodedFamilyRelations = dict()  # type: typing.Optional[typing.Dict[int, int]]
#
# 			for relationshipIndex, relatedSimID in familyRelations.items():  # type: genealogy_tracker.FamilyRelationshipIndex, int
# 				relationshipIndexValue = relationshipIndex.value  # type: int
# 				encodedFamilyRelations[relationshipIndexValue] = relatedSimID
#
# 			return encodedFamilyRelations
#
# 		def decodeFamilyRelations (encodedFamilyRelations: typing.Optional[dict]) -> typing.Optional[dict]:
# 			if encodedFamilyRelations is None:
# 				return None
#
# 			familyRelations = dict()  # type: typing.Optional[typing.Dict[genealogy_tracker.FamilyRelationshipIndex, int]]
#
# 			for relationshipIndexValue, relatedSimID in encodedFamilyRelations.items():  # type: int, int
# 				relationshipIndex = genealogy_tracker.FamilyRelationshipIndex(relationshipIndexValue)  # type: genealogy_tracker.FamilyRelationshipIndex
# 				familyRelations[relationshipIndex] = relatedSimID
#
# 			return familyRelations
#
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("SimID", "SimID", None, requiredSuccess = False))
#
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Age", "Age", None, encoder = encodeEnum, decoder = decodeAge, skipSaveTest = lambda: self.Age is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Gender", "Gender", None, encoder = encodeEnum, decoder = decodeGender, skipSaveTest = lambda: self.Gender is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Species", "Species", None, encoder = encodeEnum, decoder = decodeSpecies, skipSaveTest = lambda: self.Species is None))
#
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FirstName", "FirstName", None, skipSaveTest = lambda: self.FirstName is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FirstNameKey", "FirstNameKey", None, skipSaveTest = lambda: self.FirstNameKey is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("LastName", "LastName", None, skipSaveTest = lambda: self.LastName is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("LastNameKey", "LastNameKey", None, skipSaveTest = lambda: self.LastNameKey is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FullNameKey", "FullNameKey", None, skipSaveTest = lambda: self.FullNameKey is None))
#
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BreedName", "BreedName", None, skipSaveTest = lambda: self.BreedName is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BreedNameKey", "BreedNameKey", None, skipSaveTest = lambda: self.BreedNameKey is None))
#
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("BaseTraitIDs", "BaseTraitIDs", None, requiredSuccess = False, skipSaveTest = lambda: self.BaseTraitIDs is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FacialAttributes", "FacialAttributes", None, requiredSuccess = False, encoder = encodeBytes, decoder = decodeBytes, skipSaveTest = lambda: self.FacialAttributes is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("FamilyRelations", "FamilyRelations", None, requiredSuccess = False, encoder = encodeFamilyRelations, decoder = decodeFamilyRelations, skipSaveTest = lambda: self.FamilyRelations is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("GeneticData", "GeneticData", None, requiredSuccess = False, encoder = encodeBytes, decoder = decodeBytes, skipSaveTest = lambda: self.GeneticData is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Outfits", "Outfits", None, requiredSuccess = False, encoder = encodeBytes, decoder = decodeBytes, skipSaveTest = lambda: self.Outfits is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("PeltLayers", "PeltLayers", None, requiredSuccess = False, encoder = encodeOptionalBytes, decoder = decodeOptionalBytes, skipSaveTest = lambda: self.PeltLayers is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("Physique", "Physique", None, requiredSuccess = False, skipSaveTest = lambda: self.Physique is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("SkinTone", "SkinTone", None, requiredSuccess = False, skipSaveTest = lambda: self.SkinTone is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("VoiceActor", "VoiceActor", None, requiredSuccess = False, skipSaveTest = lambda: self.VoiceActor is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("VoiceEffect", "VoiceEffect", None, requiredSuccess = False, skipSaveTest = lambda: self.VoiceEffect is None))
# 		self.RegisterSavableAttribute(Savable.StandardAttributeHandler("VoicePitch", "VoicePitch", None, requiredSuccess = False, skipSaveTest = lambda: self.VoicePitch is None))
#
# 	@property
# 	def SimID (self) -> typing.Optional[int]:
#		"""
#		The id of the sim this sim point object targets. This will be used to find the original sim, if they still exist.
#		"""
#
# 		return self._simID
#
# 	@SimID.setter
# 	def SimID (self, value: typing.Optional[int]) -> None:
# 		if not isinstance(value, int) and value is not None:
# 			raise Exceptions.IncorrectTypeException(value, "SimID", (int, None))
#
# 		self._simID = value
#
# 	@property
# 	def SimExists (self) -> bool:
# 		"""
# 		Whether or not the sim this object points to still exists. This will always return false if this pointer's sim id is none or the
# 		service manager isn't available.
# 		"""
#
# 		if game_services.service_manager is None:
# 			return False
#
# 		if self.SimID is None:
# 			return False
#
# 		simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager
# 		originalSim = simInfoManager.get(self.SimID)  # type: sim_info.SimInfo
#
# 		return originalSim is not None
#
# 	def ChangePointer (self, simInfoOrID: typing.Union[int, sim_info.SimInfo, None], clearInformation: bool = False) -> None:
# 		"""
# 		Change the sim that this pointer object targets.
# 		:param simInfoOrID: The sim info object or the sim id of the new sim to point to.
# 		:type simInfoOrID: int | sim_info.SimInfo | None
# 		:param clearInformation: Whether or not we should clear any information taken from the previous target sim.
# 		:type clearInformation: bool
# 		:return:
# 		"""
#
#		if not isinstance(simInfoOrID, (int, sim_info.SimInfo)) and simInfoOrID is not None:
#			raise Exceptions.IncorrectTypeException(simInfoOrID, "simInfoOrID", (int, sim_info.SimInfo, None))
#
# 		if not isinstance(clearInformation, bool):
# 			raise Exceptions.IncorrectTypeException(clearInformation, "clearInformation", (bool,))
#
# 		if clearInformation:
# 			self.ClearInformation()
#
# 		if isinstance(simInfoOrID, sim_info.SimInfo):
# 			simInfoOrID = simInfoOrID.id  # type: int
#
# 		self.SimID = simInfoOrID
#
# 	def GetSim (self, createClone: bool = True) -> typing.Optional[sim_info.SimInfo]:
# 		"""
# 		Get or create (if necessary and permitted) the sim this object points to. An exception will be raised if the service manager is not available.
# 		:param createClone: Whether or not we should create a clone of the pointed to sim if the original doesn't exist.
# 		:type createClone: bool
#
# 		"""
#
# 		if game_services.service_manager is None:
# 			raise Exception("Cannot get a sim while the service manager is not available.")
#
# 		if self.SimID is not None:
# 			simInfoManager = services.sim_info_manager()  # type: sim_info_manager.SimInfoManager
# 			originalSim = simInfoManager.get(self.SimID)  # type: sim_info.SimInfo
#
# 			if originalSim is not None:
# 				return originalSim
#
# 		if not createClone:
# 			return None
#
# 		return self.GenerateClone()
#
# 	def ClearInformation (self) -> None:
# 		"""
# 		Clear the information stored on the targeted sim.
# 		"""
#
# 		self.Age = None
# 		self.Gender = None
# 		self.Species = None
#
# 		self.FirstName = None
# 		self.FirstNameKey = None
# 		self.LastName = None
# 		self.LastNameKey = None
# 		self.FullNameKey = None
# 		self.BreedName = None
# 		self.BreedNameKey = None
#
# 		self.BaseTraitIDs = None
# 		self.FacialAttributes = None
# 		self.FamilyRelations = None
# 		self.Flags = None
# 		self.GeneticData = None
# 		self.Outfits = None
# 		self.PeltLayers = None
# 		self.Physique = None
# 		self.SkinTone = None
# 		self.VoiceActor = None
# 		self.VoiceEffect = None
# 		self.VoicePitch = None
#
# 	# noinspection PyPropertyAccess
# 	def UpdateSimInformation (self, informationCategories: InformationCategories) -> None:
# 		"""
# 		Bring the information stored in this pointer up to date. Nothing will happen if this pointer's sim could not be found.
# 		:param informationCategories: The categories of information that should be updated.
# 		:type informationCategories InformationCategories
# 		"""
#
# 		if not isinstance(informationCategories, InformationCategories):
# 			raise Exceptions.IncorrectTypeException(informationCategories, "informationCategories", (InformationCategories,))
#
# 		sourceSimInfo = self.GetSim(createClone = False)  # type: typing.Optional[sim_info.SimInfo]
#
# 		if sourceSimInfo is None:
# 			return
#
# 		if informationCategories == InformationCategories.Nothing:
# 			return
#
# 		if InformationCategories.Name in informationCategories:
# 			self.FirstName = sourceSimInfo.first_name if sourceSimInfo.first_name != "" else None
# 			self.FirstNameKey = sourceSimInfo.first_name_key if sourceSimInfo.first_name_key != 0 else None
#
# 			self.LastName = sourceSimInfo.last_name if sourceSimInfo.last_name != "" else None
# 			self.LastNameKey = sourceSimInfo.last_name_key if sourceSimInfo.last_name_key != 0 else None
#
# 			self.FullNameKey = sourceSimInfo.full_name_key if sourceSimInfo.full_name_key != 0 else None
#
# 			self.BreedName = sourceSimInfo.breed_name if sourceSimInfo.breed_name != "" else None
# 			self.BreedNameKey = sourceSimInfo.breed_name_key if sourceSimInfo.breed_name_key != 0 else None
#
# 		if InformationCategories.Basic in informationCategories:
# 			self.Age = sourceSimInfo.age
# 			self.Gender = sourceSimInfo.gender
# 			self.Species = sourceSimInfo.species
#
# 		if InformationCategories.Genetic in informationCategories:
# 			# noinspection PyProtectedMember
# 			self.FamilyRelations = dict(sourceSimInfo.genealogy._family_relations)
# 			self.GeneticData = sourceSimInfo.genetic_data  # TODO the genetic data can be a protocol buffer
#
# 		if informationCategories >= InformationCategories.Appearance:
# 			self.Physique = sourceSimInfo.physique
# 			self.VoiceActor = sourceSimInfo.voice_actor
# 			self.VoiceEffect = sourceSimInfo.voice_effect
# 			self.VoicePitch = sourceSimInfo.voice_pitch
#
# 		if InformationCategories.Genetic or InformationCategories.Appearance in informationCategories:
# 			self.FacialAttributes = copy.copy(sourceSimInfo.facial_attributes)
# 			# noinspection PyProtectedMember
#
# 			self.Outfits = sourceSimInfo.save_outfits().SerializeToString()
#
# 			# self.Outfits = copy.copy(sourceSimInfo._base.outfits)  # The sim's outfit data is included in the genetic category because it contains things like hair color.
#
# 			if hasattr(sourceSimInfo, "pelt_layers"):
# 				self.PeltLayers = copy.copy(sourceSimInfo.pelt_layers)
#
# 			self.SkinTone = sourceSimInfo.skin_tone
#
# 	# if InformationCategories.Traits in informationCategories:
# 	#	if hasattr(sourceSimInfo, "base_trait_ids"):
# 	#		self.BaseTraitIDs = list(sourceSimInfo.base_trait_ids)
#
# 	def GenerateClone (self) -> sim_info.SimInfo:
# 		"""
# 		Generate a clone of the sim this object points to with the information we have.
# 		"""
# 		# TODO have an option to allow the clone to not be saved by the game.
# 		cloneCreator = sim_spawner.SimCreator(
# 			gender = self.Gender,
# 			age = self.Age,
# 			species = self.Species,
# 			first_name = self.FirstName if self.FirstName is not None else "",
# 			first_name_key = self.FirstNameKey if self.FirstNameKey is not None else 0,
# 			last_name = self.LastName if self.LastName is not None else "",
# 			last_name_key = self.LastNameKey if self.LastNameKey is not None else 0,
# 			full_name_key = self.FullNameKey if self.FullNameKey is not None else 0,
# 			breed_name = self.BreedName if self.BreedName is not None else "",
# 			breed_name_key = self.BreedNameKey if self.BreedNameKey is not None else 0
# 		)  # type: sim_spawner.SimCreator
#
# 		# noinspection PyProtectedMember
# 		cloneSimInfo = sim_spawner.SimSpawner.create_sim_infos(
# 			[cloneCreator],
# 			creation_source = self.CreationSource
# 		)[0][0]  # type: sim_info.SimInfo
#
# 		# if self.BaseTraitIDs is not None:
# 		#	cloneSimInfo.base_trait_ids = list(self.BaseTraitIDs) #TODO this doesn't copy the sim's traits / having any traits causes an exception and crashes the game if the debugger is attached.
#
# 		if self.FacialAttributes is not None:
# 			# TODO this causes lod problems with the source sim for some reason. The sim begins to appear skinny when zoomed out after the clone sim de-spawns.
# 			# TODO fixing this seems to require at least one body modifier amount value to be changed / the change cannot be to low or it doesnt fix the prob / min tested change - 0.000001
# 			cloneSimInfo.facial_attributes = self.FacialAttributes
#
# 		if self.FamilyRelations is not None:
# 			# noinspection PyProtectedMember
# 			cloneSimInfo.genealogy._family_relations = dict(self.FamilyRelations)
#
# 		if self.Flags is not None:
# 			cloneSimInfo.flags = self.Flags
#
# 		if self.GeneticData is not None:
# 			cloneSimInfo.genetic_data = self.GeneticData
#
# 		if self.Outfits is not None:
# 			# noinspection PyProtectedMember
# 			cloneSimInfo._base.outfits = self.Outfits
#
# 		if self.PeltLayers is not None:
# 			cloneSimInfo.pelt_layers = self.PeltLayers
#
# 		if self.Physique is not None:
# 			cloneSimInfo.physique = self.Physique
#
# 		if self.SkinTone is not None:
# 			cloneSimInfo.skin_tone = self.SkinTone
#
# 		if self.VoiceActor is not None:
# 			cloneSimInfo.voice_actor = self.VoiceActor
#
# 		if self.VoiceEffect is not None:
# 			cloneSimInfo.voice_effect = self.VoiceEffect
#
# 		if self.VoicePitch is not None:
# 			cloneSimInfo.voice_pitch = self.VoicePitch
#
# 		cloneSimInfo.resend_physical_attributes()
# 		cloneSimInfo.resend_current_outfit()
#
# 		return cloneSimInfo
#
# def CreatePointerFor (simInfo: sim_info.SimInfo, informationCategories: InformationCategories = InformationCategories.Nothing) -> SimPointer:
# 	"""
# 	Create a sim pointer for this currently existing sim.
# 	"""
#
# 	simPointer = SimPointer()  # type: SimPointer
# 	simPointer.ChangePointer(simInfo)
# 	simPointer.UpdateSimInformation(informationCategories)
#
# 	return simPointer
