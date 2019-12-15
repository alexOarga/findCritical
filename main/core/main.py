from CobraMetabolicModel import CobraMetabolicModel
from MetabolicModel import MetabolicModel
from Spreadsheet import Spreadsheet



MODEL = "/home/alex/PycharmProjects/tfg/models/test_models/aureus.xml"

def main():
    # Init model
    cobra_model = MetabolicModel(CobraMetabolicModel(MODEL))
    cobra_model.spreadsheet_init()

    # Shows info
    cobra_model.print_model_info()
    cobra_model.spreadsheet_write_model_info("Model")
    cobra_model.spreadsheet_write_reactions("Reactions", ordered=True)
    cobra_model.spreadsheet_write_metabolites("Metabolites", ordered=True)

    ####### TAREA 1.1 #######
    # Find dead end metabolites of the net
    print("Searching Dead End Metabolites")
    cobra_model.find_dem()

    # Save dem found
    cobra_model.spreadsheet_write_dem("1.1 DEM", ordered=True)

    ####### TAREA 2.1 #######
    # Find chokepoint reactions
    print("Searching Chokepoint reactions")
    cobra_model.find_chokepoints()

    # Save chokepoint reactions
    cobra_model.spreadsheet_write_chokepoints("2.1 Chokepoint", ordered=True)

    ####### TAREA 1.2 #######
    # Delete dem and clean net
    print("Removing Dead End Metabolites")
    cobra_model.remove_dem()

    # Save new net info
    cobra_model.spreadsheet_write_model_info("1.2 Model")

    ####### TAREA 2.2 #######
    # Find chokepoints on the new net
    print("Searching Chokepoint reactions on the new network")
    cobra_model.find_chokepoints()

    # Save chokepoints found
    cobra_model.spreadsheet_write_chokepoints("2.2 Chokepoint", ordered=True)

    ####### TAREA 3 #######
    # Load original model
    print("Running Flux Variability Analysis and updating the bounds")
    cobra_model.read_model(MODEL)

    # Change reaction bounds with the ones obtained with F.V.A.
    cobra_model.fva(update_flux=True)

    # Save F.V.A. result
    cobra_model.spreadsheet_write_fva("3 FVA", ordered=True)
    cobra_model.spreadsheet_write_reactions("3 Reactions", ordered=True)

    print("Searching Dead End Metabolites")
    cobra_model.find_dem()

    # Save DEM
    cobra_model.spreadsheet_write_dem("3 DEM", ordered=True)

    print("Searching Chokepoints")
    cobra_model.find_chokepoints()

    # Save chokepoints
    cobra_model.spreadsheet_write_chokepoints("3 Chokepoint", ordered=True)

    ####### TAREA 4 #######
    print("Searching essential genes reactions")
    cobra_model.find_essential_genes_reactions()

    # Save essential genes
    cobra_model.spreadsheet_write_essential_genes("4 Essential genes")

    # Save chokeponint and essential genes reactions
    cobra_model.spreadsheet_write_reactions("4 Reactions", ordered=True, tag_chokepoints=True, tag_essential_genes=True)

    path = "main.xls"
    print("Saving results to file: ", path)
    cobra_model.spreadsheet_save_file(path)

def test():
    cobra_model = MetabolicModel(CobraMetabolicModel(MODEL))
    cobra_model.print_dem()
    cobra_model.print_chokepoints()
    cobra_model.print_model_info()
    cobra_model.print_metabolites()
    cobra_model.print_reactions()
    cobra_model.print_genes()
    cobra_model.print_essential_genes()
    cobra_model.print_essential_genes_reactions()
    cobra_model.print_essential_reactions()


test()
