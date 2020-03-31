from AbstractMetabolicModel import AbstractMetabolicModel


class MetabolicModel(AbstractMetabolicModel):
	""" Class that works as an abstraction of a MetabolicModel model

		Attributes
			__model (): object that implements MetabolicModel
	"""

	__model = None

	def __init__(self, model):
		self.__model = model

	def read_model(self, path):
		self.__model.read_model(path)

	def save_model(self, path):
		self.__model.save_model(path)

	def set_state(self, key):
		self.__model.set_state(key)

	def get_state(self, key):
		return self.__model.get_state(key)

	def model(self):
		return self.__model.model()

	def id(self):
		return self.__model.id()

	def compartments(self):
		return self.__model.compartments()

	def objective(self):
		return self.__model.objective()

	def set_objective(self, reaction):
		self.__model.set_objective(reaction)

	def objective_value(self):
		return self.__model.objective_value()

	def reactions(self):
		return self.__model.reactions()

	def metabolites(self):
		return self.__model.metabolites()

	def dem(self):
		return self.__model.dem()

	def chokepoints(self):
		return self.__model.chokepoints()

	def get_fva(self):
		return self.__model.get_fva()

	def genes(self):
		return self.__model.genes()

	def essential_genes(self):
		return self.__model.essential_genes()

	def essential_genes_reactions(self):
		return self.__model.essential_genes_reactions()

	def essential_reactions(self):
		return self.__model.essential_reactions()

	def find_dem(self, compartment="ALL"):
		return self.__model.find_dem(compartment)

	def find_chokepoints(self, exclude_dead_reactions=False):
		return self.__model.find_chokepoints(exclude_dead_reactions)
	
	def remove_dem(self, delete_exchange=False, keep_all_incomplete_reactions=True):
		self.__model.remove_dem(delete_exchange, keep_all_incomplete_reactions)

	def fva(self, loopless=False, verbose=False, update_flux=False, threshold=None, pfba_factor=None):
		return self.__model.fva(loopless, verbose, update_flux, threshold, pfba_factor)

	def find_essential_genes_1(self):
		return self.__model.find_essential_genes_1()

	def find_essential_genes_reactions(self):
		return self.__model.find_essential_genes_reactions()

	def get_growth(self):
		return self.__model.get_growth()

	def find_essential_reactions_1(self):
		self.__model.find_essential_reactions_1()

	def print_model_info(self):
		self.__model.print_model_info()

	def print_metabolites(self, ordered=False):
		self.__model.print_metabolites(ordered)

	def print_reactions(self, ordered=False):
		self.__model.print_reactions(ordered)

	def print_genes(self, ordered=False):
		self.__model.print_genes(ordered)

	def print_dem(self, ordered=False, compartment="ALL"):
		self.__model.print_dem(ordered, compartment)

	def print_chokepoints(self, ordered=False):
		self.__model.print_chokepoints(ordered)

	def print_essential_genes(self, ordered=False):
		self.__model.print_essential_genes(ordered)

	def print_essential_reactions(self, ordered=False):
		self.__model.print_essential_reactions(ordered)

	def print_essential_genes_reactions(self, ordered=False):
		self.__model.print_essential_genes_reactions(ordered)
