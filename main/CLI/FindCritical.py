import sys
import time
from argparse import ArgumentParser

sys.path.append("../core")

from Facade import Facade

TASK_SPREADSHEET = "TASK_SPREADSHEET"
TASK_SAVE_WITHOUT_DEM = "TASK_SAVE_WITHOUT_DEM"
TASK_SAVE_WITH_FVA = "TASK_SAVE_WITH_FVA"
TASK_SAVE_WITH_FVA_DEM = "TASK_SAVE_WITH_FVA_DEM"

def verbose_f(text, args1=False, args2=False):
	if args1:
		print(text)

def run(model_path, output_path, task, verbose):
	try:
		if task == TASK_SPREADSHEET:
			facade = Facade()
			error = facade.generate_spreadsheet(False, model_path, verbose_f, args1=verbose, args2=None, output_path=None)
			if error == "":	
				(result_ok, text) = facade.save_spreadsheet(False, output_path, verbose_f)
				if result_ok:
					print("File succesfully saved at: " + text)
				else:
					print("Error, something went wrong: " + text)
			else:
				print("Error, something went wrong: " + error)
		elif task == TASK_SAVE_WITHOUT_DEM:
			facade = Facade()
			facade.find_and_remove_dem(False, output_path, verbose_f, model_path, args1=verbose, args2=None)
			print("File succesfully saved at: " + output_path)
		elif task == TASK_SAVE_WITH_FVA:
			facade = Facade()
			error = facade.run_fva(False, output_path, verbose_f, model_path, args1=verbose, args2=None)
			if error != "":
				print("Error, something went wrong: " + error)
			else:
				(result_ok, text) = facade.save_model(output_path, False, verbose_f)
				if result_ok:
					print("File succesfully saved at: " + text)
				else:
					print("Error, something went wrong: " + text)
		elif task == TASK_SAVE_WITH_FVA_DEM:
			facade = Facade()
			error = facade.run_fva_remove_dem(False, output_path, verbose_f, model_path, args1=verbose, args2=None)
			if error != "":
				print("Error, something went wrong: " + error)
			else:
				(result_ok, text) = facade.save_model(output_path, False, verbose_f)
				if result_ok:
					print("File succesfully saved at: " + text)
				else:
					print("Error, something went wrong: " + text)

	except Exception as error:
		print("Error: Something went wrong:")
		print(str(error))
		print("########## REMOVE raise ON CLI/Main.py")
		raise error


def __check_model_file(input):
	if input[-4:] != ".xml" and input[-5:] != ".json" and input[-4:] != ".yml" and input[-4:] != ".mat":
		return False
	else:
		return True

def read_input():
	input_file = ""
	output = ""
	verbose = False
	parser = ArgumentParser(description="")
	parser.add_argument("-v", "--verbose", help="Print feedback while running.", action="store_true")
	parser.add_argument("-i", dest="inputfile", required=True,
						help="Input metabolic model. Allowed file formats: .xml .json .yml .mat", metavar="<input file>")
	parser.add_argument("-o", dest="outputfile",
						help="Output spreadsheet file with results. Allowed file formats: .xls .ods", metavar="<output file>")
	parser.add_argument("-swD", dest="modelwodem",
						help="Save output model without Dead End Metabolites. Allowed file formats: .xml .json .yml .mat", metavar="<output file>")
	parser.add_argument("-sF", dest="modelfva",
						help="Save output model with reactions bounds updated with Flux Variability Analysis. Allowed file formats: .xml .json .yml .mat",
						metavar="<output file>")
	parser.add_argument("-swDF", dest="modelfvawodem",
						help="Save output model with reactions bounds updated with Flux Variability Analysis and without Dead End Metabolites. Allowed file formats: .xml .json .yml .mat",
						metavar="<output file>")
	args = parser.parse_args()
	input_file = args.inputfile
	output = args.outputfile
	modelwodem = args.modelwodem
	modelfva = args.modelfva
	modelfvawodem = args.modelfvawodem

	if output is not None and not __check_model_file(input_file):
		print("Model file must be either .xml .json .yml .mat")
		print("run Main.py -h for further information.")
		exit(1)

	if (modelwodem is not None and not __check_model_file(modelwodem)) or \
		(modelfva is not None and not __check_model_file(modelfva)) or \
		(modelfvawodem is not None and not __check_model_file(modelfvawodem)):
		print("Output model file must be either .xml .json .yml .mat")
		print("run Main.py -h for further information.")
		exit(1)

	if args.outputfile is not None:
		if output[-4:] != ".xls" and output[-4:] != ".ods":
			print("Output file must be .xls or .ods")
			exit(1)

	if output is None and modelwodem is None and modelfva is None and modelfvawodem is None:
		print("Please select one operation to perform: ")
		print("[-o <output file>] [-swD <output file>] [-sF <output file>] [-swDF <output file>]")
		print("run Main.py -h for further information.")
		exit(1)

	return (input_file, output, modelwodem, modelfva, modelfvawodem, args.verbose)


def main():
	# CHeck input
	(input_file, output, modelwodem, modelfva, modelfvawodem, verbose) = read_input()
	print(input_file, output, modelwodem, modelfva, modelfvawodem, verbose)
	if output is not None:
		run(input_file, output, TASK_SPREADSHEET, verbose)
	if modelwodem is not None:
		run(input_file, modelwodem, TASK_SAVE_WITHOUT_DEM, verbose)
	if modelfva is not None:
		run(input_file, modelfva, TASK_SAVE_WITH_FVA, verbose)
	if modelfvawodem is not None:
		run(input_file, modelfvawodem, TASK_SAVE_WITH_FVA_DEM, verbose)


if __name__ == "__main__":
	main()



