from abc import ABC, abstractmethod


class AbstractMetabolicModel(ABC):
	""" Abstract class defining the interface of a metabolic network

	"""

	@abstractmethod
	def read_model(self, path):
		""" Loads a metabolic network from a file

		Args:
			path (): Direction containing the metabolic network
		"""
		pass

	@abstractmethod
	def save_model(self, path):
		""" Saves metabolic network to a file

        Args:
            path (): File path
        """
		pass


	@abstractmethod
	def set_state(self, key):
		pass

	@abstractmethod
	def get_state(self, key):
		pass

	@abstractmethod
	def model(self):
		pass

	@abstractmethod
	def id(self):
		pass

	@abstractmethod
	def objective(self):
		""" Returns the objective function of the model

		"""
		pass

	@abstractmethod
	def set_objective(self, reaction):
		""" Sets the reaction param as the objective function of the model

		:param reaction: reaction to set as objective
		"""
		pass

	@abstractmethod
	def objective_value(self):
		pass

	@abstractmethod
	def compartments(self):
		pass

	@abstractmethod
	def reactions(self):
		pass

	@abstractmethod
	def metabolites(self):
		pass

	@abstractmethod
	def dem(self):
		pass

	@abstractmethod
	def chokepoints(self):
		pass

	@abstractmethod
	def get_fva(self):
		pass

	@abstractmethod
	def essential_genes(self):
		pass

	@abstractmethod
	def essential_genes_reactions(self):
		pass

	@abstractmethod
	def essential_reactions(self):
		pass


	@abstractmethod	
	def find_dem(self, compartment):
		""" Finds the dead end metabolites of the metabolic network in a selected compartment

		Args:
			compartment (): Compartment in which the search is done.
		"""
		pass


	@abstractmethod
	def find_chokepoints(self, exclude_dead_reactions):
		""" Finds the chokepoint reactions of the metabolic network

		Args:
			loopless (): Exclude dead reactions from the computed list of chokepoints

		"""
		pass


	@abstractmethod	
	def remove_dem(self, remove_exchange):
		""" While not changing removes the dead end metabolites and reactions only consuming/producing
			of the network

		"""
		pass


	@abstractmethod
	def fva(self, loopless, verbose, update_flux, threshold, pfba_factor):
		""" If possible, runs a Flux Variability Analysis (F.V.A) on the model.

		Args:
			loopless (): Avoids loops of the standard F.V.A.
			verbose (): Print the reusult of the f.v.a.
			update_flux (): Update the upper and lower bounds of the reactions with the ones obtained
							with the f.v.a.
		"""
		pass


	@abstractmethod
	def get_growth(self):
		""" Runs Flux Balance Analysis on the model and returns the objective value.

		"""
		pass


	@abstractmethod
	def find_essential_genes_1(self):
		""" Finds the essential genes of the metabolic network

		"""
		pass


	@abstractmethod
	def find_essential_genes_reactions(self):
		""" Finds the reactions associated to essential genes

		"""
		pass

	@abstractmethod
	def find_essential_reactions_1(self):
		pass


	@abstractmethod
	def print_model_info(self):
		""" Shows info about the metabolic network

		"""
		pass


	@abstractmethod
	def print_metabolites(self, ordered):
		""" Shows the metabolites of the metabolic network

			Args:
				ordered (): Print the metabolites in alphabetic order
		"""
		pass


	@abstractmethod
	def print_reactions(self, ordered):
		""" Shows the reactions of the metabolic network

			Args:
				ordered (): Print the reactions in alphabetic order
		"""
		pass


	@abstractmethod
	def print_genes(self, sorted):
		""" If possible, shows the essential genes of the metabolic network

		Args:
			ordered (): Print the genes in alphabetic order
		"""
		pass

	@abstractmethod
	def print_dem(self, ordered, compartment):
		""" Shows the dead end metabolites of the metabolic network

			Args:
				ordered (): Print the metabolites in alphabetic order
				compartment (): Restric the dead end metabolites shown to a given compartment
		"""
		pass


	@abstractmethod
	def print_chokepoints(self, ordered):
		""" Shows the chokepoint reactions of the metabolic network

			Args:
				ordered (): Print the chokepoint reactions in alphabetic order
		"""
		pass


	@abstractmethod
	def print_essential_genes(self, sorted):
		""" If possible, shows the essential genes of the metabolic network

		Args:
			ordered (): Print the genes in alphabetic order
		"""
		pass

	@abstractmethod
	def print_essential_reactions(self, sorted):
		""" If possible, shows the essential reactions of the metabolic network

		Args:
			ordered (): Print the reactions in alphabetic order
		"""
		pass

	@abstractmethod
	def print_essential_genes_reactions(self, ordered):
		""" If possible, shows the reactions associated to the essential genes of the metabolic network

		Args:
			ordered (): Print the reactions in alphabetic order
		"""
		pass
