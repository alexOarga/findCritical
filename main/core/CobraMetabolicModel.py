from AbstractMetabolicModel import AbstractMetabolicModel
from State import State
from State import CobraMetabolicStateBuilder
from enum import Enum
import cobra

from math import isnan

from cobra.io.sbml import validate_sbml_model
from cobra.flux_analysis import flux_variability_analysis
from cobra.manipulation import delete
from cobra.manipulation.delete import find_gene_knockout_reactions
from cobra.flux_analysis.deletion import single_reaction_deletion
from cobra.flux_analysis import find_essential_reactions

from optlang.exceptions import SolverError

import itertools
import sys

from time import sleep
import threading
from multiprocessing import Process
import inspect
import ctypes



CONST_EPSILON = 0.000005

class NullDevice():
	def write(self, s):
		pass


class CobraMetabolicModel(AbstractMetabolicModel):
	""" Class containing a metabolic network.
		It implements AbstractMetabolicModel with the cobrapy library

	Attributes
		__cobra_model (): Cobra model of the metabolic network. Class: cobra.core.model.

		__objective_value(): float that saves the result of running Flux Balance Analysis on the model.
			The value initially is None.

		__dem (): Dict containing the dead end metabolites of the model.
			- Key: compartments of the model.
			- Values: list of cobra.core.metabolites containing the dead end metabolites of the compartment.
			If the method find_dem() hasnt been called the value of the attribute is None.

		__chokepoints (): List of objects _MetaboliteReact containing chokepoint reactions of the network.
			If the methos find_chokepoints() hasn't been called the value is None.

		__fva (): List of tuples (cobra.core.reaction, maximun, minimum) containing the result of the Flux Variability Analysis.

		__essential_genes (): List of cobra.core.gene containing the essential genes of the model.
		__essential_genes_reactions (): Dict containing the reactions associated to the essential genes.
			Key: cobra.core.reaction.
			Value: list of cobra.core.gene containing the genes associated to the reaction.
		__essential_reactions (): dict: key: reaction id, value: float or "infeasible"

		__spreadsheet (): xlwt Workbook
	"""

	__cobra_model = None
	__objective_value = None
	__dem = None
	__chokepoints = None
	__fva = None
	__essential_genes = None
	__essential_genes_reactions = None
	__essential_reactions = None
	__states = {}


	__exchange_demand_reactions = {}

	# as we consider reactions with flux (0,0) forward (->) save the original topological
	# direction to avoid a direction swap ((<-) to (->)).
	__initial_backward_reactions = set({})


	def model(self):
		return self.__cobra_model

	def set_state(self, key):
		builder = CobraMetabolicStateBuilder()
		self.__states[key] = builder.buildState(self)

	def get_state(self, key):
		if key not in self.__states:
			raise Exception("Couldn't find state: '" + key + "'. State doesn't exist")
		return self.__states[key]

	def model(self):
		return self.__cobra_model

	def id(self):
		return self.__cobra_model.id

	def objective(self):
		return str(self.__cobra_model.objective.expression)

	def objective_value(self):
		return self.__objective_value

	def set_objective(self, reaction):
		""" Sets the objective function of the cobra model as the reactions passed as parameter.

		:param reaction: reaction id of a cobra.core.reaction object
		:type reaction: str
		:raises: RuntimeError: if the reaction id cant be found on the cobra model.
		"""
		try:
			reaction_obj = self.__cobra_model.reactions.get_by_id(reaction)
			self.__cobra_model.objective = str(reaction_obj.id)
		except KeyError as error:
			raise RuntimeError("Reaction id can't be found on the model.")

	def compartments(self):
		""" Return list with compartments

		:return: list with compartments short name
		:rtype: list of str
		"""
		return list(self.__cobra_model.compartments.keys())


	def reactions(self):
		""" Return list with reactions

		:return: list with the reactions of the model
		:rtype:  list of cobra.core.reaction
		"""
		return self.__cobra_model.reactions


	def metabolites(self):
		""" Return list with metabolites

		:return: list with the metabolites of the model
		:rtype:  list of cobra.core.metabolite
		"""
		return self.__cobra_model.metabolites


	def dem(self):
		""" Returns a dict with compartments and its dead-end metabolites if they have been calculated. Dict has
			the following structure:
				- key: compartment name (can be obtained with 'compartments()' method).
				- value: list with objects cobra.core.metabolite that represent the dead-end of the compartment.

		:return: dict with dead-end metabolite by compartment.
		:rtype: dict({ str : list([cobra.core.metabolites]) })
		:raises: Exception: if dead-end hasnt been calculated.
		"""
		if self.__dem is not None:
			return self.__dem
		else:
			raise Exception("Dead End metabolites hasn't been calculated. Please run 'find_dem()'.")


	def chokepoints(self):
		""" Returns a list of tuples of (cobra.core.reaction, cobra.core.metabolite) containing the chokepoint reactions of the model.

		:return: list of tuples (reaction, metabolite) of chokepoint reactions and the metabolite they consume/produce.
		:rtype: list( tuple( cobra.core.reaction, cobra.core.metabolite ) )
		"""
		if self.__chokepoints is not None:
			return [(mtb_rct.reaction, mtb_rct.metabolite) for mtb_rct in self.__chokepoints]
		else:
			raise Exception("Chokepoint reactions hasn't been calculated. Please run 'find_chokepoints()'.")


	def get_fva(self):
		""" Returns the result of running Flux Variability Analysis on the model

		:return: List of tuples (cobra.core.reaction, maximum flux, minimum flux) with the reactions and its flux.
		:rtype: list([ tuple( (cobra.core.reaction, float, float) ) ])
		"""
		if self.__fva is not None:
			return self.__fva
		else:
			raise Exception("Flux Variability hasn't been run. Please run 'fva()'.")


	def genes(self):
		return self.__cobra_model.genes

	def essential_genes(self):
		if self.__essential_genes is not None:
			return self.__essential_genes
		else:
			raise Exception("Essential genes hasn't been calculated. Please run 'find_essential_genes_1()'.")

	def essential_genes_reactions(self):
		if self.__essential_genes_reactions is not None:
			return self.__essential_genes_reactions
		else:
			raise Exception("Essential genes reactions hasn't been calculated. Please run 'find_essential_genes_reactions()'.")

	def essential_reactions(self):
		if self.__essential_reactions is not None:
			return self.__essential_reactions
		else:
			raise Exception("Essential reactions hasn't been calculated. Please run 'find_essential_reactions_1()'.")

	def reversible_reactions(self):
		""" Returns a list of reversible reactions of the model

		:return: List of cobra.core.reaction with reversible direction.
		:rtype: list([ cobra.core.reaction ])
		"""
		return list(filter(lambda x: self.__reaction_direction(x) == self._Direction.REVERSIBLE, self.__cobra_model.reactions))

	def dead_reactions(self):
		""" Returns a list of reactions with upper bound = 0 AND lower bound = 0

		:return: List of cobra.core.reaction with dead-reactions
		:rtype: list([ cobra.core.reaction ])
		"""
		return list(filter(lambda reaction: abs(reaction.upper_bound) < CONST_EPSILON and abs(reaction.lower_bound) < CONST_EPSILON, self.__cobra_model.reactions))

	def exchange_demand_reactions(self):
		return self.__exchange_demand_reactions

	def __id(self, e):
		return e.id


	class _Direction(Enum):
		FORWARD = 0
		BACKWARD = 1
		REVERSIBLE = 2


	def __init__(self, path=None):
		if path is not None:
			self.read_model(path)


	def __print_errors(self, errors):
		for elem in errors:
			aux = errors.get(elem)
			if len(aux) > 0:
				print(elem)
				for error in aux:
					print("    ", error)


	def read_model(self, path):
		""" Reads a cobra model from a file. Assigns it to __cobra_model attribute.

		Args:
			path (): File direction of the cobra model

		:raises RuntimeError: if the input file format is not .xml, .json or .yml.
		:raises FileNotFoundError: if the input file can't be found.
		:raises Exception: if cobrapy throws an exception reading the model (model has errors).
		"""
		original_stderr = sys.stderr  # keep a reference to STDERR
		sys.stderr = NullDevice()  # redirect the real STDERR
		try:
			# check if file exists
			open(path, 'r')
			# read model
			if path[-4:] == ".xml":
				self.__cobra_model = cobra.io.read_sbml_model(path)
			elif path[-5:] == ".json":
				self.__cobra_model = cobra.io.load_json_model(path)
			elif path[-4:] == ".yml":
				self.__cobra_model = cobra.io.load_yaml_model(path)
			else:
				sys.stderr = original_stderr  # turn STDERR back on
				raise RuntimeError("Model file must be either .xml .json .yml")

			# Generate exchange/demand reactions list
			exchanges = self.__cobra_model.exchanges
			demands = self.__cobra_model.demands
			self.__exchange_demand_reactions = set(exchanges).union(set(demands))
			for reaction in self.__cobra_model.reactions:
				if (len(reaction.reactants) == 0 and len(reaction.products) == 1) or (len(reaction.reactants) == 1 and len(reaction.products) == 0):
					self.__exchange_demand_reactions.add(reaction)
				if self.__reaction_direction(reaction) == self._Direction.BACKWARD:
					self.__initial_backward_reactions.add(reaction)

		except FileNotFoundError:
			sys.stderr = original_stderr  # turn STDERR back on
			raise FileNotFoundError("File not found: '", path, "'")
			#exit(1)
		except RuntimeError as errorFormat:
			# Formato del fichero incorrecto
			raise(errorFormat)
		except Exception as exception:
			sys.stderr = original_stderr  # turn STDERR back on
			# raise Exception(exception)
			# exit(1)
			(model, errors) = validate_sbml_model(path)
			for code in ['SBML_ERROR', 'SBML_SCHEMA_ERROR', 'SBML_FATAL', 'COBRA_FATAL', 'COBRA_ERROR']:
				error_list = errors[code]
				if error_list != []:
					raise Exception("Error reading model: " + error_list[0])

		sys.stderr = original_stderr  # turn STDERR back on


	def save_model(self, path):
		""" Saves the Cobra Model into a file.

		Args:
			path (): Destination file path. Possible file formats:
				- SBML: 	.xml (default)
				- JSON: 	.json
				- YAML: 	.yml
		"""
		if path[-4:] == ".xml":
			cobra.io.write_sbml_model(self.__cobra_model, path)
		elif path[-5:] == ".json":
			cobra.io.save_json_model(self.__cobra_model, path)
		elif path[-4:] == ".yml":
			cobra.io.save_yaml_model(self.__cobra_model, path)
		else:
			raise RuntimeError("Destination file must be either .xml .json .yml")


	def reaction_direction(self, reaction):
		return self.__reaction_direction(reaction)

	def __reaction_direction(self, reaction):
		""" Checks the direction of a reaction given his upper and lower bounds.

		Args:
			reaction (): Class cobra.core.reaction

		Returns: Enum: FORWARD/BACKWARD/REVERSIBLE depending on the direction of the reaction.

		"""
		if reaction.upper_bound > - CONST_EPSILON and reaction.upper_bound < CONST_EPSILON:
			upper = 0
		else:
			upper = reaction.upper_bound
		if reaction.lower_bound > - CONST_EPSILON and reaction.lower_bound < CONST_EPSILON:
			lower = 0
		else:
			lower = reaction.lower_bound
		if lower == 0 and upper == 0:
			if reaction in self.__initial_backward_reactions:
				return self._Direction.BACKWARD
			else:
				return self._Direction.FORWARD
		elif lower >= 0:
			return self._Direction.FORWARD
		elif upper > 0:
			return self._Direction.REVERSIBLE
		else:
			return self._Direction.BACKWARD


	def __is_dead_reaction(self, reaction):
		return abs(reaction.upper_bound) < CONST_EPSILON and abs(reaction.lower_bound) < CONST_EPSILON


	def find_dem_2(self, compartment="ALL"):
		""" Finds the dead end metabolites of the model or a specific comparment.
			When searched, it saves them in the '__dem' class atribute with the compartment as a key and
			a list of cobra.core.metabolite as value representing the DEM of that compartment.

		:param compartment: String representing the compartment in which the search is made. "ALL" by default
		:type compartment: str
		:return: dict with dead - end metabolites by compartment.
		:rtype: dict({str: list([cobra.core.metabolites])})
		"""
		if self.__dem == None:
			self.__dem = {}
		list_dem = []
		for metabolite in self.__cobra_model.metabolites:
			# If the metabolite is in the choosen compartment. Else we ignore it
			if (metabolite.compartment == compartment) or (compartment == "ALL"):
				# If metabolite only appears in one reaction and it's not reversible -> dead end
				if len(metabolite.reactions) == 1:
					reaction = list(metabolite.reactions)[0]
					if self.__reaction_direction(reaction) != self._Direction.REVERSIBLE:
						list_dem = list_dem + [metabolite]
				# If metabolite appears in more than one reacion
				# Check if it's always product or reactant
				else:
					reactions = list(metabolite.reactions)
					i = 0
					end = False
					reactant = None 	# variable for comparing each reaction with the previous one
					while i < len(reactions) and not end:
						reaction = reactions[i]
						# If reaction is reversible -> not dead end
						if self.__reaction_direction(reaction) == self._Direction.REVERSIBLE:
							end = True
						else:
							# first time entering
							if reactant == None:

								if (self.__reaction_direction(reaction) == self._Direction.FORWARD and metabolite in reaction.reactants) \
									or (self.__reaction_direction(reaction) == self._Direction.BACKWARD and metabolite in reaction.products):
									reactant = True
								else:
									reactant = False
							# not first time -> 'reactant' already assigned
							else:
								if (self.__reaction_direction(reaction) == self._Direction.FORWARD and metabolite in reaction.reactants) \
									or (self.__reaction_direction(reaction) == self._Direction.BACKWARD and metabolite in reaction.products):
									if not reactant:
										end = True
								else:
									if reactant:
										end = True
						i = i + 1
					if not end:
						list_dem = list_dem + [metabolite]
		if compartment != "ALL":
			self.__dem[compartment] = list_dem
		else:
			for comprt in self.__cobra_model.compartments:
				self.__dem[comprt] = []
			for metabolite in list_dem:
				self.__dem[metabolite.compartment].append(metabolite)
		return list_dem


	def find_dem(self, compartment="ALL"):
		""" Finds the dead end metabolites of the model or a specific comparment.
			When searched, it saves them in the '__dem' class atribute with the compartment as a key and
			a list of cobra.core.metabolite as value representing the DEM of that compartment.

		:param compartment: String representing the compartment in which the search is made. "ALL" by default
		:type compartment: str
		:return: dict with dead - end metabolites by compartment.
		:rtype: dict({str: list([cobra.core.metabolites])})
		"""
		if self.__dem == None:
			self.__dem = {}
		reactants = set({})
		products = set({})
		for reaction in self.__cobra_model.reactions:
			direction = self.__reaction_direction(reaction)
			if direction == self._Direction.REVERSIBLE:
				# All metabolites are reactants and products
				for metabolite in reaction.metabolites:
					if (compartment == "ALL") or (metabolite.compartment == compartment):
						reactants.add(metabolite)
						products.add(metabolite)
			elif direction == self._Direction.BACKWARD:
				# If reaction is backward -> products are reactants and reactants are products
				for metabolite in reaction.reactants:
					if (compartment == "ALL") or (metabolite.compartment == compartment):
						products.add(metabolite)
				for metabolite in reaction.products:
					if (compartment == "ALL") or (metabolite.compartment == compartment):
						reactants.add(metabolite)
			else:
				# Forward reaction
				for metabolite in reaction.reactants:
					if (compartment == "ALL") or (metabolite.compartment == compartment):
						reactants.add(metabolite)
				for metabolite in reaction.products:
					if (compartment == "ALL") or (metabolite.compartment == compartment):
						products.add(metabolite)
		# Diferrence beetwen sets
		dem_reactants = reactants.difference(products)
		dem_products = products.difference(reactants)
		# All dem = sum of dem produced and dem consumed
		dem = list(dem_reactants) + list(dem_products)
		if compartment != "ALL":
			self.__dem[compartment] = dem
		else:
			for comprt in self.__cobra_model.compartments:
				self.__dem[comprt] = []
			for metabolite in dem:
				self.__dem[metabolite.compartment].append(metabolite)
		return dem


	def __check_dem(self, compartment="ALL"):
		""" Checks if the dead end metabolites of the model or a specific compartmet has been searched.
			If not searches the dead end metabolites.

		Args:
			compartment (): limit the checkup to a specific compartment. "ALL" by default
		"""
		if (compartment == "ALL"):
			if (self.__dem == None):
				self.find_dem()
			else:
				for cmprt in self.__cobra_model.compartments:
					if cmprt not in self.__dem:
						self.find_dem(cmprt)
		elif (self.__dem == None) or (compartment not in self.__dem):
			self.find_dem(compartment)


	class _MetaboliteReact:
		""" Class composed by a metabolite and a reaction containing it.

		Attributes
			metabolite : Class cobra.core.metabolite
			reaction : Class cobra.core.reaction
		"""

		def __init__(self, metabolite, reaction):
			""" Private class initiator.
			"""
			self.metabolite = metabolite
			self.reaction = reaction


	def __metabolite_id(self, obj):
		""" Given an object _MetaboliteReact it returns the 'id' of the metabolite

		Args:
			obj (): Object cobra.core.metabolite

		Returns: 'id' field of the metabolite

		"""
		return obj.metabolite.id


	def __reaction_id(self, obj):
		""" Given an object _MetaboliteReact it returns the 'id' of the reaction

		Args:
			obj (): Object cobra.core.reaction

		Returns: 'id' field of the reaction

		"""
		return obj.reaction.id


	def find_chokepoints(self, exclude_dead_reactions=False):
		""" Finds chokepoint reactions of the cobra model

		Returns: List of objects of class _MetaboliteReact containing a chokepoint reaction
				 and the metabolite consumed/produced

		"""
		reactants = []	# List of reactants metabolites with it's reaction
		products = []	# List of products metabolites with it's reaction
		for reaction in self.__cobra_model.reactions:
			direction = self.__reaction_direction(reaction)
			is_dead_reaction = self.__is_dead_reaction(reaction)
			if (not exclude_dead_reactions) or (exclude_dead_reactions and not is_dead_reaction):
				if direction == self._Direction.REVERSIBLE:
					# If reaction is reversible all metabolites are reactants and products
					for metabolite in reaction.metabolites:
						mtb = self._MetaboliteReact(metabolite, reaction)
						reactants.append(mtb)
						products.append(mtb)
				else:
					if direction == self._Direction.FORWARD:
						reac_reactants = reaction.reactants
						reac_prodcuts = reaction.products
					else:
						# If reaction is backward reactants=products and products=reactants
						reac_reactants = reaction.products
						reac_prodcuts = reaction.reactants
					# add reactants and products of the reaction to the list
					for metabolite in reac_prodcuts:
						mtb = self._MetaboliteReact(metabolite, reaction)
						products.append(mtb)
					for metabolite in reac_reactants:
						mtb = self._MetaboliteReact(metabolite, reaction)
						reactants.append(mtb)

		# Order lists
		reactants.sort(key=self.__metabolite_id)
		products.sort(key=self.__metabolite_id)

		i = 0
		j = 0
		chokepoints = []

		# Pair metabolites of ordered lists of reactants and products
		# 	If a metabolite appears 1 time in one list and more than 1 time on the other -> 
		#	The reaction on the 1 time side is a chokepoint reaction
		while i < len(reactants) and j < len(products):
			mtb1 = reactants[i].metabolite.id
			mtb2 = products[j].metabolite.id
			if mtb1 < mtb2:
				i = i + 1
			elif mtb1 > mtb2:
				j = j + 1
			else:  # mtb1 = mtb2	Metabolites are the same
				# Pairing the 2 metabolites
				num1 = 1 # Number of times de first metabolite appears
				num2 = 1 # Number of times the second metabolite appears
				i = i + 1
				j = j + 1
				while i < len(reactants) and reactants[i].metabolite.id == mtb1:
					num1 = num1 + 1
					i = i + 1
				while j < len(products) and products[j].metabolite.id == mtb2:
					num2 = num2 + 1
					j = j + 1
				#if num1 == 1 and num2 >= 1:
				if num1 == 1:
					chokepoints.append(reactants[i - 1])
					if num2 == 1:
						chokepoints.append(products[j - 1])
				#elif num2 == 1 and num1 >= 1:
				elif num2 == 1:
					chokepoints.append(products[j - 1])
					if num1 == 1:
						chokepoints.append(reactants[i - 1])
		self.__chokepoints = chokepoints
		return chokepoints


	def __remove_dem(self, delete_exchange=False, keep_all_incomplete_reactions=True):
		""" Auxiliar method for 'remove_dem()'

		"""
		while True:
			dem = list(itertools.chain.from_iterable(self.__dem.values()))
			num_mtbs = len(self.__cobra_model.metabolites)
			self.__cobra_model.remove_metabolites(dem)
			reactions = []
			# Delete the reactions that doesnt produce or doesnt consume
			if delete_exchange:
				for reaction in self.__cobra_model.reactions:
					if len(reaction.reactants) == 0 or len(reaction.products) == 0:
						reactions.append(reaction)
			else:
				if keep_all_incomplete_reactions:
					for reaction in self.__cobra_model.reactions:
						if (len(reaction.reactants) == 0 or len(reaction.products) == 0) and (reaction not in self.__exchange_demand_reactions):
							reactions.append(reaction)
				else:
					exchange_and_demand = set(exchanges).union(set(demands))
					for reaction in self.__cobra_model.reactions:
						if (len(reaction.reactants) == 0 or len(reaction.products) == 0) and (reaction not in exchange_and_demand):
							reactions.append(reaction)
			self.__cobra_model.remove_reactions(reactions)
			self.find_dem()
			# Loop continues while the number of metabolites doenst change
			if num_mtbs == len(self.__cobra_model.metabolites):
				break


	def remove_dem(self, delete_exchange=False, keep_all_incomplete_reactions=True):
		""" While there network changes, eliminates dead ends metabolites
			and reactions that only produce or consume

			- delete_exchange:
				- True: all the reactions that are produce or consume 0 metabolites are deleted whether they are exchange/demand or not.
				- False: deleted according to 'keep_all_incomplete_reactions' param.
			- keep_all_incomplete_reactions:
				- False: if a reactions is in [cobra Boundary reactions](https://cobrapy.readthedocs.io/en/latest/media.html#Boundary-reactions) (calculated by heuristics) that reaction can't be deleted.
				- True: if a reaction initially doesn't produce or consume any metabolite that reaction can't be deleted.

		:param delete_exchange: if True exchange and demand reactions are deleted
		:type delete_exchange: bool
		:param keep_all_incomplete_reactions: If True all reactions that initially dont consume or dont produce any
				metabolite are kept.
		:type keep_all_incomplete_reactions: bool
		:return:
		:rtype:
		"""

		self.__check_dem()

		if delete_exchange == True:
			self.__remove_dem(True, keep_all_incomplete_reactions)
		elif len(self.__cobra_model.exchanges) == 0:
			self.__remove_dem(True, keep_all_incomplete_reactions)
		else:
			self.__remove_dem(False, keep_all_incomplete_reactions)

		""" 

		Args:
			loopless (): Runs a lopeless analysis
			verbose (): Prints the results obtained in the analysis
			update_flux (): Updates the bounds of the reaction with the values obtained with the F.V.A.
		"""
	def fva(self, loopless=False, verbose=False, update_flux=False, threshold=None, pfba_factor=None):
		""" If possible, runs a Flux Variability Analysis on the model and saves the result on the '__fva' class atribute.
			Returns a list of errors. If there wasn't any error while running FVA it return an empty list: []

			For more info about the params see: https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/flux_analysis/variability/index.html?highlight=flux_varia#cobra.flux_analysis.variability.flux_variability_analysis

		:param loopless: Runs a lopeless analysis
		:type loopless: bool
		:param verbose: Print the result of FVA while running the analysis.
		:type verbose: bool
		:param update_flux: Updates the bounds of the reaction with the values obtained with the F.V.A.
		:type update_flux: bool
		:param threshold: Must be <= 1.0. If is None: deafult = 1.0. factor of the maximum objective value.
		:type threshold: float
		:param pfba_factor: Add an additional constraint to the model that requires the total sum of absolute fluxes
				must not be larger than this value times the smallest possible sum of absolute fluxes
		:type pfba_factor: float
		:return: list of errors if there was any. Else return an empty list: []
		:rtype: list([ str ])
		"""
		errors = []
		if verbose:
			print("FLUX VARIABILITY ANALYSIS: ",  self.__cobra_model.id)
		try:
			i = 0
			fva_result = []
			# Run FVA analysis
			if threshold is None and pfba_factor is None:
				fva_reactions = flux_variability_analysis(self.__cobra_model, loopless=loopless)
			else:
				fva_reactions = flux_variability_analysis(self.__cobra_model, loopless=loopless, fraction_of_optimum=threshold,  pfba_factor=pfba_factor)
			for reaction_id in fva_reactions.index:
				reaction = self.__cobra_model.reactions.get_by_id(reaction_id)
				fva_lower = float(fva_reactions.values[i][0])
				fva_upper = float(fva_reactions.values[i][1])
				# Print info
				if verbose:
					print("REACTION: ", reaction.name)
					if update_flux:
						print("    model bounds: [", str(reaction.upper_bound)[:10].ljust(10), ", ", str(reaction.lower_bound)[:10].ljust(10), "]")
					print("    fva ranges:   [", str(fva_upper)[:10].ljust(10), ", ", str(fva_lower)[:10].ljust(10), "]")
				# Update bounds
				if update_flux:
					reaction.lower_bound = fva_lower
					reaction.upper_bound = fva_upper
				i = i + 1
				# Add results to list
				fva_result.append( (reaction, fva_upper, fva_lower)  )
			self.__fva = fva_result
		except cobra.exceptions.Infeasible as error:
			self.__fva = []
			errors.append("Model is infeasable")
		except Exception as error:
			self.__fva = []
			if "unbounded" in str(error):
				errors.append("Model is unbounded")
			else:
				errors.append(str(error))
		return errors


	def get_growth(self):
		""" Runs flux balance analysis (slim_optimize() from cobrapy) and returns the objective value.
			Saves the objective value in __objective_value attribute.

		:return: objective value
		:rtype: float
		"""
		model = self.__cobra_model
		try:
			if 'moma_old_objective' in model.solver.variables:
				model.slim_optimize()
				growth = model.solver.variables.moma_old_objective.primal
			else:
				growth = model.slim_optimize()
			self.__objective_value = growth
		except SolverError:
			growth = float('nan')
		except Exception as timeout:
			growth = float('-1')
		return growth


	def find_essential_reactions_1(self):
		errors = []
		try:
			self.__objective_value = self.get_growth()
			if isnan(self.__objective_value):
				self.__objective_value = None
			self.__essential_reactions = {}
			deletions = single_reaction_deletion(self.__cobra_model, method='fba', processes=1)
			essential = deletions.loc[:, :]['growth']
			for frozset in essential.index.values:
				reaction = self.__cobra_model.reactions.get_by_id(list(frozset)[0])
				self.__essential_reactions[reaction] = essential[frozset]
		except Exception as error:
			errors.append(str(error))
			self.__essential_reactions = {}
		return errors


	def find_essential_genes_1(self):
		""" If the model has genes, finds the essential genes and assigns them to the '__essential_genes' class atribute.

		"""
		errors = []
		try:
			# TODO: check processes number (because deadlock)
			aux = cobra.flux_analysis.variability.find_essential_genes(self.__cobra_model, processes=1)
			self.__essential_genes = aux
		except cobra.exceptions.Infeasible as error:
			self.__essential_genes = []
			errors.append("Model is infeasable")
		except Exception as error:
			self.__essential_genes = []
			if "unbounded" in str(error):
				errors.append("Model is unbounded")
			else:
				errors.append(str(error))
		return errors

	def find_essential_genes_reactions(self):
		""" If the model has genes finds the reactions associated with the essential genes.
			Searches essential genes if hasn't done before.

		"""
		errors = []
		try:
			if self.__essential_genes is not None:
				# Dict with reaction as key and list of genes as value
				reactions = {}
				for gene in self.__essential_genes:
					reactions_knock = find_gene_knockout_reactions(self.__cobra_model, [gene])
					for reaction in reactions_knock:
						if reaction in reactions:
							reactions[reaction].append(gene)
						else:
							reactions[reaction] = [gene]
				self.__essential_genes_reactions = reactions
		except Exception as error:
			self.__essential_genes_reactions = {}
			errors.append(str(error))
		return errors


	def print_model_info(self):
		""" Prints model general info

		"""
		print("MODEL INFO")
		print('-' * 55)
		print("MODEL: ", self.__cobra_model.id)
		print("REACTIONS: ", len(self.__cobra_model.reactions))
		print("METABOLITES: ", len(self.__cobra_model.metabolites))
		print("GENES: ", len(self.__cobra_model.genes))
		if len(self.__cobra_model.compartments):
			print("COMPARTMENTS: ",  list(self.__cobra_model.compartments)[0])
			i = 1
			while i < len(self.__cobra_model.compartments):
				print("".ljust(14), list(self.__cobra_model.compartments)[i])
				i = i + 1
		print()

	def print_metabolites(self, ordered=False):
		""" Prints metabolites and its reactions of the cobra model

			Args:
				ordered (): print the metabolites in alphabetical order by id

		"""
		metabolites = self.__cobra_model.metabolites
		if ordered:
			metabolites.sort(key=self.__id)
		print("MODEL: ", self.__cobra_model.id, " - NUMBER OF METABOLITES: ", len(self.__cobra_model.metabolites))
		print("METABOLITE".ljust(10), " | ", "COMPARTMENT".ljust(15), " | ", "REACTION ID")
		print('-' * 55)
		for metabolite in metabolites:
			print(metabolite.id.ljust(10), " | ", metabolite.compartment.ljust(15), " | ",list(metabolite.reactions)[0].id)
			i = 1
			while i < len(list(metabolite.reactions)):
				print("".ljust(10), " | ", "".ljust(15), " | ", list(metabolite.reactions)[i].id)
				i = i + 1
		print()


	def print_reactions(self, ordered=False):
		""" Prints reactions of the cobra model

			Args:
				ordered (): print the reactions in alphabetical order by id

		"""
		reactions = self.__cobra_model.reactions
		if ordered:
			reactions.sort(key=self.__id)
		print("MODEL: ", self.__cobra_model.id, " - NUMBER OF REACTIONS: ", len(self.__cobra_model.reactions))
		print("REACTION ID | UPPER BOUND | LOWER BOUND | REACTION")
		print('-' * 55)
		for reaction in reactions:
			print(reaction.id.ljust(10), " |  ", str(reaction.upper_bound)[:8].ljust(8), " | ", str(reaction.lower_bound)[:9].ljust(9), " | ", reaction.reaction)
		print()


	def print_genes(self, ordered=False):
		""" If the model has genes prints the essential genes of the model. If essential genes hasn't been searched it
			searches them.

		Args:
			ordered (): print the essential genes in alphabetical order by id

		"""
		genes = list(self.__cobra_model.genes)
		print("MODEL: ", self.__cobra_model.id, " - NUMBER OF GENES: ", len(genes))
		print("GENE ID".ljust(10), " | ", "GENE NAME".ljust(10), " | ", "REACTION ID".ljust(10), "| ", "GPR RELATION")
		print('-' * 55)
		if ordered:
			genes.sort(key=self.__id)
		for gene in genes:
			reactions = list(gene.reactions)
			print(gene.id.ljust(10), " | ", gene.name.ljust(10), " | ",  reactions[0].id.ljust(10), " | ",  reactions[0].gene_reaction_rule.ljust(15))
			i = 1
			while i < len(reactions):
				print("".ljust(10), " | ", "".ljust(10), " | ", reactions[i].id.ljust(10), " | ",  reactions[i].gene_reaction_rule.ljust(15))
				i = i + 1
		print()


	def print_dem(self, ordered=False, compartment="ALL"):
		""" Prints dead end metabolites of the cobra model

			Args:
				ordered (): print the dead end metabolites in alphabetical order by id
				compartment (): show the dead end metabolites of a specific compartment. "ALL" by default.
		"""
		self.__check_dem(compartment)
		if compartment == "ALL":
			metabolites = list(itertools.chain.from_iterable(self.__dem.values()))
		else:
			metabolites = self.__dem[compartment]
		if ordered:
			metabolites.sort(key=self.__id)
		print("MODEL: ", self.__cobra_model.id, " - NUMBER OF DEM: ", len(self.__dem), " - COMPARTMENT: ", compartment)
		print("METABOLITE".ljust(10), " | ", "COMPARTMENT".ljust(15), " | ", "REACTION ID")
		print('-' * 55)
		for metabolite in metabolites:
			print(metabolite.id.ljust(10), " | ", metabolite.compartment.ljust(15), " | ",list(metabolite.reactions)[0].id)
			i = 1
			while i < len(list(metabolite.reactions)):
				print("".ljust(10), " | ", "".ljust(15), " | ", list(metabolite.reactions)[i].id)
				i = i + 1
		print()


	def print_chokepoints(self, ordered=False):
		""" Prints chokepoints reactions of the cobra model and its consumed/produced metabolites.

			Args:
				ordered (): print the chokepoint reactions in alphabetical order by id

		"""
		if self.__chokepoints is None:
			self.find_chokepoints()
		chokepoints = self.__chokepoints
		if ordered:
			chokepoints.sort(key=self.__reaction_id)
		print("MODEL: ", self.__cobra_model.id, " - NUMBER OF CHOKEPOINTS: ", len(self.__chokepoints))
		print("METABOLITE ID | ", "METABOLITE NAME".ljust(40), " | REACTION ID | REACTION NAME")
		print('-' * 60)
		for mtb_rct in chokepoints:
			print(mtb_rct.metabolite.id.ljust(12), " | ", mtb_rct.metabolite.name.ljust(40), " | ", mtb_rct.reaction.id.ljust(9)," | ", mtb_rct.reaction.name)
		print()



	def print_essential_genes(self, ordered=False):
		""" If the model has genes prints the essential genes of the model. If essential genes hasn't been searched it
			searches them.

		Args:
			ordered (): print the essential genes in alphabetical order by id

		"""
		errors = []
		if self.__essential_genes is None:
			#print("Essential genes hasn't been searched")
			#print("Searching essential genes...")
			errors = self.find_essential_genes_1()
		if errors != []:
			print(errors[0])
		else:
			genes = list(self.__essential_genes)
			print("MODEL: ", self.__cobra_model.id, " - NUMBER OF GENES: ", len(genes))
			print("GENE ID".ljust(10), " | ", "GENE NAME".ljust(10), " | ", "REACTION ID".ljust(10), "| ","GPR RELATION")
			print('-' * 55)
			if ordered:
				genes.sort(key=self.__id)
			for gene in genes:
				reactions = list(gene.reactions)
				print(gene.id.ljust(10), " | ", gene.name.ljust(10), " | ", reactions[0].id.ljust(10), " | ",reactions[0].gene_reaction_rule.ljust(15))
				i = 1
				while i < len(reactions):
					print("".ljust(10), " | ", "".ljust(10), " | ", reactions[i].id.ljust(10), " | ",reactions[i].gene_reaction_rule.ljust(15))
					i = i + 1
			print()


	def print_essential_genes_reactions(self, ordered=False):
		""" If the model has genes prints the reactions associated to the essential genes of the model.
			If essential genes hasn't been searched it searches them.

			Args:
				ordered (): print the reactions in alphabetical order by id

			"""
		errors = []
		if self.__essential_genes_reactions is None:
			#print("Essential genes hasn't been searched")
			#print("Searching essential genes...")
			errors = self.find_essential_genes_reactions()
		if errors != []:
			print(errors[0])
		else:
			print("MODEL: ", self.__cobra_model.id, " - NUMBER OF ESSENTIAL GENES REACTIONS: ", len(self.__essential_genes_reactions))
			print("REACTION ID | GENE ID     | GPR RELATION ")
			print('-' * 60)
			reactions = self.__essential_genes_reactions
			reactions_key = reactions.keys()
			if ordered:
				reactions_key = sorted(reactions.keys(), key=self.__id)
			for reaction in reactions_key:
				genes = reactions[reaction]
				print(reaction.id.ljust(10), " | ", genes[0].id.ljust(10), "|", reaction.gene_reaction_rule)
				i = 1
				while i < len(genes):
					print("".ljust(10), " | ", genes[0].id.ljust(10), "|", reaction.gene_reaction_rule)
					i = i + 1
			print()

	def print_essential_reactions(self, ordered=False):
		"""
		"""
		errors = []
		if self.__essential_reactions is None:
			#print("Essential genes hasn't been searched")
			#print("Searching essential genes...")
			errors = self.find_essential_reactions_1()
		if errors != []:
			print(errors[0])
		else:
			print("MODEL: ", self.__cobra_model.id, " - REACTIONS KNOCKOUT RESULT")
			print("REACTION ID     | FBA OBJECTIVE ")
			print('-' * 60)
			reactions = self.__essential_reactions
			reactions_key = reactions.keys()
			if ordered:
				reactions_key = sorted(reactions.keys(), key=self.__id)
			for reaction in reactions_key:
				print(reaction.id.ljust(15), "|", reactions[reaction])
			print()



