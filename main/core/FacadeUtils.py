from MetabolicModel import MetabolicModel
from CobraMetabolicModel import CobraMetabolicModel
from Spreadsheet import Spreadsheet

class ErrorGeneratingModel(Exception):
	pass


class FacadeUtils:
	def run_summary_model(self, model_path, print_f, arg1, arg2):
		#verboseprint = print if verbose else lambda *a, **k: None

		print_f("Reading model...", arg1, arg2)
		model = MetabolicModel(CobraMetabolicModel(model_path))

		model.set_state("initial")
		model.set_state("dem")
		model.set_state("fva")
		model.set_state("fva_dem")

		s = Spreadsheet()
		s.spreadsheet_write_model_info(model, "model_info")
		s.spreadsheet_write_reactions(model, "reactions", ordered=True)
		s.spreadsheet_write_metabolites(model, "metabolites", ordered=True, print_reactions=True)
		s.spreadsheet_write_genes(model, "genes", ordered=True, print_reactions=True)

		print_f("Generating models...", arg1, arg2)

		model.find_essential_genes_reactions()
		print_f("Searching Dead End Metabolites (D.E.M.)...", arg1, arg2)
		model.find_dem()
		print_f("Searching chokepoint reactions...", arg1, arg2)
		model.find_chokepoints()
		print_f("Searching essential reactions...", arg1, arg2)
		model.find_essential_reactions_1()
		print_f("Searching essential genes...", arg1, arg2)
		errors_initial = model.find_essential_genes_1()
		if errors_initial != []:
			MSG = "Couldn't find essential genes: " + str(errors_initial[0])
			print_f(MSG)
		else:
			print_f("Searching essential genes reactions...", arg1, arg2)
			model.find_essential_genes_reactions()

		model.set_state("initial")

		print_f("Removing Dead End Metabolites (D.E.M.)...", arg1, arg2)
		model.remove_dem()
		print_f("Searching essential reactions...", arg1, arg2)
		model.find_essential_reactions_1()
		print_f("Searching new chokepoint reactions...", arg1, arg2)
		model.find_chokepoints()

		if errors_initial == []:
			print_f("Searching essential genes...", arg1, arg2)
			errors_dem = model.find_essential_genes_1()
			if errors_dem == []:
				print_f("Searching essential genes reactions...", arg1, arg2)
				model.find_essential_genes_reactions()

		model.set_state("dem")

		print_f("Running Flux Variability Analysis...", arg1, arg2)
		model = MetabolicModel(CobraMetabolicModel(model_path))
		errors_fva = model.fva(update_flux=True)

		if errors_fva != []:
			MSG = "Couldn't run Flux Variability Analysis: " + str(errors_fva[0])
			print_f(MSG, arg1, arg2)
		else:
			print_f("Searching Dead End Metabolites (D.E.M.)...", arg1, arg2)
			model.find_dem()
			print_f("Searching new chokepoint reactions...", arg1, arg2)
			model.find_chokepoints()
			print_f("Searching essential genes...", arg1, arg2)
			errors_fva_genes = model.find_essential_genes_1()
			if errors_fva_genes != []:
				MSG = "Couldn't find essential genes: " + str(errors_fva_genes[0])
				print_f(MSG)
			else:
				print_f("Searching essential genes reactions...", arg1, arg2)
				model.find_essential_genes_reactions()
			print_f("Searching essential reactions...", arg1, arg2)
			model.find_essential_reactions_1()

			s.spreadsheet_write_reactions(model, "reactions_FVA", ordered=True)

			model.set_state("fva")

			print_f("Removing Dead End Metabolites (D.E.M.)...", arg1, arg2)
			model.remove_dem()
			print_f("Searching essential reactions...", arg1, arg2)
			model.find_essential_reactions_1()
			print_f("Searching new chokepoint reactions...", arg1, arg2)
			model.find_chokepoints()
			if errors_fva_genes == []:
				print_f("Searching essential genes...", arg1, arg2)
				model.find_essential_genes_1()
				print_f("Searching essential genes reactions...", arg1, arg2)
				model.find_essential_genes_reactions()

			model.set_state("fva_dem")

		print_f("Generating spreadsheet...", arg1, arg2)
		s.spreadsheet_write_summary_reactions("chokepoints", model.get_state("initial"), model.get_state("dem"),
		                                      model.get_state("fva"),
		                                      model.get_state("fva_dem"))
		s.spreadsheet_write_summary_metabolites("dead-end", model.get_state("initial"), model.get_state("fva"))
		s.spreadsheet_write_chokepoints_genes("comparison", model.get_state("initial"),
		                                      model.get_state("dem"),
		                                      model.get_state("fva"), model.get_state("fva_dem"))
		s.spreadsheet_write_essential_reactions("essential reactions", model.get_state("initial"),
		                                      model.get_state("dem"),
		                                      model.get_state("fva"), model.get_state("fva_dem"), ordered=True)
		s.spreadsheet_write_summary("summary", model.get_state("initial"),
		                                      model.get_state("dem"),
		                                      model.get_state("fva"), model.get_state("fva_dem"))

		return s

	def find_and_remove_dem(self, model_path):
		model = MetabolicModel(CobraMetabolicModel(model_path))
		model.find_dem()
		model.remove_dem()
		return model

	def run_fva(self, model_path):
		model = MetabolicModel(CobraMetabolicModel(model_path))
		errors = model.fva(update_flux=True)
		if errors != []:
			return (model, errors[0])
		else:
			return (model, "")

	def run_fva_remove_dem(self, model_path):
		model = MetabolicModel(CobraMetabolicModel(model_path))
		errors = model.fva(update_flux=True)
		if errors != []:
			return (model, errors[0])
		else:
			model.find_dem()
			model.remove_dem()
			return (model, "")

	def save_model(self, output_path, model):
		if output_path != "":
			try:
				model.save_model(output_path)
				return (True, output_path)
			except Exception as error:

				return (False, str(error))
		return (False, '')

	def save_spreadsheet(self, output_path, spreadsheet):
		if output_path != "":
			try:
				spreadsheet.spreadsheet_save_file(output_path)
				return (True, output_path)
			except Exception as error:
				return (False, str(error))
		return (False, '')

	def read_model(self, model_path):
		try:
			model = MetabolicModel(CobraMetabolicModel(model_path))
			model_id = model.id()
			reactions = len(model.reactions())
			metabolites = len(model.metabolites())
			genes = len(model.genes())
			return (True, None, model, model_id, reactions, metabolites, genes)
		except Exception as error:
			return (False, str(error), None, None, None, None, None)

	def print_something(self):
		pass