import sys, os

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QMessageBox, QMainWindow, QApplication, QWidget, QPushButton, \
	QFileDialog, QPlainTextEdit, QLabel, QHBoxLayout, QAction, QSizePolicy, QSpacerItem, QTextBrowser, QDialog,  QTextBrowser, QComboBox
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import pyqtSignal, Qt, QByteArray, pyqtSignal, QThread, QRect, QSize
from libsbml import _libsbml
import threading


sys.path.append('../core')
sys.path.append('..//core')

from Facade import Facade

WIDTH = 480
HEIGHT = 320

TASK_READ_MODEL = "READ_MODEL"
TASK_SAVE_DEM = "SAVE_DEM"
TASK_SAVE_FVA = "SAVE_FVA"
TASK_SAVE_FVA_DEM = "SAVE_FVA_DEM"
TASK_SPREADSHEET = "SPREADSHEET"
TASK_SAVE_SPREADSHEET = "SAVE_SPREADSHEET"
TASK_SAVE_MODEL = "TASK_SAVE_MODEL"

EVENT_READ_COMPLETE = "READ_COMPLETE"
EVENT_LOG = "LOG"
EVENT_SAVE_MODEL_TO_FILE = "SAVE_MODEL_TO_FILE"
EVENT_SAVE_SPREADSHEET = "SAVE_SPREADSHEET"
EVENT_SAVE_SPREADSHEET_DONE = "SAVE_SPREADSHEET_DONE"
EVENT_SAVE_SPREADSHEET_FILE_DONE = "SAVE_SPREADSHEET_FILE_DONE"
EVENT_CANCEL = "CANCEL"
EVENT_RETRY_INITIAL = "RETRY_INITIAL"
EVENT_ERROR_RUNNING = "ERROR_RUNNING"
EVENT_STOP = "EVENT_STOP"
EVENT_SAVE_FILE_FINISH = "EVENT_SAVE_FILE_FINISH"
EVENT_WORK_FINISH = "EVENT_WORK_FINISH"
EVENT_WORK_TASK = "EVENT_WORK_TASK"
EVENT_SET_OBJECTIVE = "EVENT_SET_OBJECTIVE"

# Some Windows errors make the app to restart. Avoided temporarely with the 'RUNNING' flag.
RUNNING = False


def _append_run_path():
	if getattr(sys, 'frozen', False):
		pathlist = []

		# If the application is run as a bundle, the pyInstaller bootloader
		# extends the sys module by a flag frozen=True and sets the app
		# path into variable _MEIPASS'.
		pathlist.append(sys._MEIPASS)

		# the application exe path
		_main_app_path = os.path.dirname(sys.executable)
		pathlist.append(_main_app_path)

		# append to system path enviroment
		os.environ["PATH"] += os.pathsep + os.pathsep.join(pathlist)


_append_run_path()


class Model:
	app = None
	model_path = None
	signal = None
	facade = None

	objective = None

	def read_file(self):
		(fname, AllFiles) = QFileDialog.getOpenFileName(self.app, 'Open model file')
		self.model_path = fname
		return fname

	def save_model_to_file(self):
		(name, All) = QFileDialog.getSaveFileName(self.app, 'Save Model File')
		if name != "":
			log_msg = "Saving model to file... :" + name
			self.signal.emit({"event": EVENT_LOG, "log": log_msg})
			self.facade.save_model(name, True, self.notify_model_saved)

	def save_spreadsheet_to_file(self, notify_function):
		(name, All) = QFileDialog.getSaveFileName(self.app, 'Save Spreadsheet File')
		self.facade.save_spreadsheet(True, name, self.notify_saving_spreadsheet)
		#self.signal.emit({"event":EVENT_SAVE_SPREADSHEET_FILE_DONE})

	def get_initial_model(self):
		return (self.model_id, self.reactions, self.metabolites, self.genes)

#####################################################

	def set_task(self, task):
		self.task = task

	def set_signal(self, signal):
		self.signal = signal


	def notify_read_complete(self, result_ok, error_msg, model_id, reactions, metabolites, genes, reactions_list, args1=None, args2=None, result=False, error=None):
		self.model_id = model_id
		self.reactions = reactions
		self.metabolites = metabolites
		self.genes = genes
		self.reactions_list = reactions_list
		if result_ok:
			self.signal.emit({"event": EVENT_READ_COMPLETE, "result": True, "errors": []})
		else:
			self.signal.emit({"event": EVENT_READ_COMPLETE, "result": False, "errors": [error_msg]})


	def notify_log(self, msg, arg1=None, arg2=None, ended=False, result=False, error=None):
		if not ended:
			self.signal.emit({"event": EVENT_LOG, "log": msg})
		else:
			self.signal.emit({"event": EVENT_SAVE_SPREADSHEET_DONE, "log": msg})


	def notify_saving_spreadsheet(self, msg, arg1=None, arg2=None, ended=False, result=False, error=None):
		self.signal.emit({"event":  EVENT_SAVE_SPREADSHEET_FILE_DONE, "success": result, "result": error})

	def notify_model_saved(self, msg,  arg1=None, arg2=None, ended=False, result=False, error=None):
		self.signal.emit({"event":  EVENT_SAVE_FILE_FINISH, "success": result, "result":error})

	def notify_work_model_done(self, msg, arg1=None, arg2=None, ended=False, result=False, error=None):
		self.signal.emit({"event": EVENT_WORK_FINISH, "success": result, "result": error})

	def generic_log_issue(self):
		self.signal.emit({"event": EVENT_LOG, "log": "Please report any issue to: https://github.com/alexOarga/findCritical/issues"})

	def run(self, task):
		try:

			objective = self.objective				
			if self.objective is not None:
				objective = self.reactions_list[self.objective - 1]

			if task == TASK_READ_MODEL:
				(result_ok, erorr) = self.read_model(self.model_path, False, self.notify_read_complete)
			elif task == TASK_SAVE_DEM:
				self.generic_log_issue()
				self.log("Searching and removing dead-end metabolites... Please wait.")
				self.facade.find_and_remove_dem(True, None, self.notify_work_model_done, self.model_path)
			elif task == TASK_SAVE_FVA:
				self.generic_log_issue()
				self.log("Updating model with Flux Variability Analysis... Please wait.")
				self.facade.run_fva(True, None, self.notify_work_model_done, self.model_path, objective=objective)
			elif task == TASK_SAVE_FVA_DEM:
				self.generic_log_issue()
				self.log("Updating model with Flux Variability Analysis, finding and removing dead-end metabolites... Please wait.")
				self.facade.run_fva_remove_dem(True, None, self.notify_work_model_done, self.model_path, objective=objective)
			elif task == TASK_SPREADSHEET:
				self.generic_log_issue()
				self.facade.generate_spreadsheet(True, self.model_path, self.notify_log, args1=None, args2=None, output_path=None, objective=objective)
			elif task == TASK_SAVE_SPREADSHEET:
				self.save_spreadsheet_to_file(self.notify_saving_spreadsheet)
			elif task == TASK_SAVE_MODEL:
				self.save_model_to_file()

		except Exception as error:
			# THread stopped
			# TODO: REMOVE THIS
			print("DEBUG: REMOVE THIS RAISE IN run_GUI.py")
			raise error

	def find_and_remove_dem(self):
		log_msg = "Searching Dead End Metabolites...\n"
		self.signal.emit({"event": EVENT_LOG, "log": log_msg})
		self.facade.find_dem()
		log_msg = "Removing Dead End Metabolites...\n"
		self.signal.emit({"event": EVENT_LOG, "log": log_msg})
		self.facade.remove_dem()

	def read_model(self, model_path, verboselog=False, notify_function=None):
		if verboselog:
			log_msg = "Reading model: " + self.model_path + "\n"
			self.signal.emit({"event": EVENT_LOG, "log": log_msg})
		(result, error) = self.facade.read_model(True, model_path, notify_function)
		return (result, error)

	def run_fva(self):
		self.signal.emit(
			{"event": EVENT_LOG, "log": "Running Flux Variability Analysis... This may take a while...\n"})
		errors = self.facade.run_fva()
		if errors != []:
			self.signal.emit({"event": EVENT_ERROR_RUNNING, "errors": errors[0]})

	def log(self, msg):
		self.signal.emit({"event": EVENT_LOG, "log": msg})


######################################################


	def run_task(self, signal_model, task):
		#self.thread1 = ThreadWithExc(signal_model, self.model_path)
		self.run(task)

	def stop(self):
		self.facade.stop()

	def __init__(self, app, singal):
		self.app = app
		self.signal = singal
		self.facade = Facade()


class View:
	window = None
	actual_event = None

	def showErrorInitial(self, title, text, informative, event):
		msg = QMessageBox(self.window)
		msg.setIcon(QMessageBox.Information)
		msg.setText(text)
		msg.setInformativeText(informative)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Retry)
		#msg.buttonClicked.connect(self.retry_initial_load)
		horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout = msg.layout()
		layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
		msg.show()

	def showErrorSaveModel(self, title, text, informative, event):
		self.actual_event = event
		msg = QMessageBox(self.window)
		msg.setIcon(QMessageBox.Warning)
		msg.setText(text)
		msg.setInformativeText(informative)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
		msg.buttonClicked.connect(self.retry_select_file_model)
		horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout = msg.layout()
		layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
		msg.show()

	def showErrorSaveSpreadsheet(self, title, text, informative, event):
		self.actual_event = event
		msg = QMessageBox(self.window)
		msg.setIcon(QMessageBox.Warning)
		msg.setText(text)
		msg.setInformativeText(informative)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
		msg.buttonClicked.connect(self.retry_select_file)
		horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout = msg.layout()
		layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
		msg.show()

	def showErrorRunning(self, title, text, informative, event):
		msg = QMessageBox(self.window)
		msg.setIcon(QMessageBox.Warning)
		msg.setText(text)
		msg.setInformativeText(informative)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.buttonClicked.connect(self.return_main)
		horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout = msg.layout()
		layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
		msg.show()

	def showSuccess(self, title, text, informative, event):
		msg = QMessageBox(self.window)
		msg.setIcon(QMessageBox.Information)
		msg.setText(text)
		msg.setInformativeText(informative)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.buttonClicked.connect(self.return_main)
		horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout = msg.layout()
		layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
		msg.show()

	def retry_select_file(self, button):
		if button.text() == "Retry":
			self.signal.emit({"event": EVENT_SAVE_SPREADSHEET_DONE})
		else:
			self.signal.emit({"event": EVENT_CANCEL})

	def retry_select_file_model(self, button):
		if button.text() == "Retry":
			self.signal.emit({"event": EVENT_WORK_FINISH, "success": True, "result": ""})
		else:
			self.signal.emit({"event": EVENT_CANCEL})

	def retry_initial_load(self):
		self.signal.emit({"event": EVENT_RETRY_INITIAL})

	def return_main(self):
		self.signal.emit({"event": EVENT_CANCEL})

	def show_initial_load(self):
		self.load_model.setGeometry(QRect((WIDTH / 2) - 70, (HEIGHT / 2) - 30, 140, 30))
		self.load_model.show()

	def hide_initial_load(self):
		self.load_model.hide()

	def show_loading_model(self, path):
		# Show text
		self.text_loading = QLabel("<strong>Loading model: </strong>" + path, self.window)
		self.text_loading.setGeometry(QRect(30, 10, WIDTH - 60, HEIGHT / 4))
		self.text_loading.setWordWrap(True)
		self.text_loading.show()
		# Display gif
		SIZE_X = 150
		SIZE_Y = 150
		self.movie_screen = QLabel(self.window)
		self.movie_screen.resize(150, 150)
		self.movie = QMovie("loading.gif", QByteArray(), self.window)
		self.movie.setCacheMode(QMovie.CacheAll)
		self.movie.setSpeed(100)
		self.movie.setScaledSize(QSize(SIZE_X, SIZE_Y))
		self.movie_screen.setMovie(self.movie)
		self.movie_screen.setGeometry(QRect((WIDTH / 2) - (SIZE_X / 2), (HEIGHT / 4) , WIDTH / 2, HEIGHT / 2))
		self.movie_screen.show()
		self.movie.start()
		# Show cancel button
		self.cancel_read.move((WIDTH / 2) - 50, HEIGHT - 60)
		self.cancel_read.show()

	def hide_loading_model(self):
		self.movie.stop()
		self.text_loading.hide()
		self.movie_screen.hide()
		self.cancel_read.hide()

	def show_main(self, model_id, reactions, metabolites, genes):
		# self.text_loading = QLabel("hola")

		self.change_model.setGeometry(20,35, 120, 30)
		self.change_model.show()

		self.text_loading = QLabel("<strong>Uploaded Model info: </strong>" +
		                           "<br> &nbsp; &nbsp;&nbsp; Model id: " + model_id +
		                           "<br> Metabolites: " + str(metabolites) +
		                           "<br> &nbsp;&nbsp; Reactions: " + str(reactions)  +
		                           "<br> &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;  Genes: " + str(genes)
		                           , self.window)
		self.text_loading.setGeometry(QRect((WIDTH / 2) - 70, -10, WIDTH - 60, HEIGHT / 2))
		self.text_loading.setWordWrap(True)
		self.text_loading.show()

		self.win = QWidget(self.window)
		self.win.setGeometry(0, HEIGHT * 0.4, WIDTH, HEIGHT * 0.6)

		text_spread = QLabel()
		text_spread.setText(
			"Generate spreadsheet file with model data, dead-end metabolites, chokepoints reactions and if feasible essential genes and reactions")
		text_spread.setWordWrap(True)

		group1 = QGroupBox("Save results")
		vbox1 = QVBoxLayout()
		vbox1.addWidget(text_spread)
		vbox1.addWidget(self.button_spread)
		group1.setLayout(vbox1)

		group2 = QGroupBox("Save model file")
		vbox2 = QVBoxLayout()
		vbox2.addStretch()
		vbox2.addWidget(self.button_dem)
		vbox2.addWidget(self.button_fva)
		vbox2.addWidget(self.button_fva_dem)
		group2.setLayout(vbox2)

		grid = QHBoxLayout()
		grid.addWidget(group1)
		grid.addWidget(group2)

		self.win.setLayout(grid)

		self.button_dem.show()
		self.button_fva.show()
		self.button_fva_dem.show()
		self.button_spread.show()
		self.win.show()

	def hide_main(self):
		self.change_model.hide()
		self.text_loading.hide()
		self.button_dem.hide()
		self.button_fva.hide()
		self.button_fva_dem.hide()
		self.button_spread.hide()
		self.win.hide()

	def show_working_window(self, task):
		self.win = QWidget(self.window)
		self.win.setGeometry(0, 20, WIDTH, HEIGHT-20)

		vbox = QVBoxLayout()
		text = QLabel("<strong>Task: </strong> Null")
		if task == TASK_SAVE_DEM:
			text = QLabel("<strong>Task: </strong> Save model without Dead-End Metabolites")
		elif task == TASK_SAVE_FVA:
			text = QLabel(
				"<strong>Task: </strong> Save model with reaction bounds updated with Flux Variability Analysis")
		elif task == TASK_SAVE_FVA_DEM:
			text = QLabel(
				"<strong>Task: </strong> Save model with reaction bounds updated with Flux Variability Analysis and with Dead-End Metabolites removed")
		elif task == TASK_SPREADSHEET:
			text = QLabel("<strong>Task: </strong> Generating spreadsheet with results")
		text.setWordWrap(True)
		vbox.addWidget(text)
		vbox.addStretch()
		self.log = QPlainTextEdit()
		self.log.resize(WIDTH * 0.9, HEIGHT * 0.8)
		self.log.setPlainText("")
		self.cancel_working.setText('Cancel')
		vbox.addWidget(self.log)
		vbox.addWidget(self.start_working)
		vbox.addWidget(self.cancel_working)

		self.show_start_button()

		self.win.setLayout(vbox)
		self.log.show()
		self.win.show()

	def show_working_window_objective(self, task, reactions_list):
		self.signal.emit({"event": EVENT_SET_OBJECTIVE, "result": None})

		self.win = QWidget(self.window)
		self.win.setGeometry(0, 20, WIDTH, HEIGHT-20)

		vbox = QVBoxLayout()
		text = QLabel("<strong>Task: </strong> Generating spreadsheet with results")
		text.setWordWrap(True)
		vbox.addWidget(text)
		vbox.addWidget(QLabel("<br>"))
		self.text2 = QLabel("Select objective function:")
		self.text2.setWordWrap(True)
		vbox.addWidget(self.text2)
		self.cb = QComboBox()
		self.cb.addItems(["Default"] + reactions_list)
		self.cb.currentIndexChanged.connect(self.selectionchange)
		vbox.addWidget(self.cb)
		vbox.addStretch()
		self.log = QPlainTextEdit()
		self.log.resize(WIDTH * 0.9, HEIGHT * 0.8)
		self.log.setPlainText("")
		self.log.hide()
		vbox.addWidget(self.log)
		vbox.addWidget(self.start_working)
		vbox.addWidget(self.cancel_working)
		self.show_start_button()
		self.win.setLayout(vbox)
		self.win.show()

	def hide_objective_show_log(self):
		self.text2.hide()
		self.cb.hide()
		self.log.show()

	def selectionchange(self, i):
		obj = i
		if obj == 0:
			obj = None
		self.signal.emit({"event": EVENT_SET_OBJECTIVE, "result": obj})

	def hide_working_window(self):
		self.log.hide()
		self.cancel_working.hide()
		self.start_working.hide()
		self.win.hide()

	def set_cancel_working_button_disabled(self):
		self.cancel_working.setText('Cancelling... Please wait')
		self.cancel_working.setEnabled(False)

	def set_cancel_read_button_disabled(self):
		self.cancel_read.setText("Cancelling... Please wait")
		self.cancel_read.setEnabled(False)

	def show_cancel_button(self):
		self.start_working.hide()
		self.cancel_working.show()

	def show_start_button(self):
		self.cancel_working.hide()
		self.start_working.show()

	def init_cancel_button(self):
		self.cancel_read.setEnabled(True)
		self.cancel_read.setText("Cancel")
		self.cancel_working.setEnabled(True)
		self.cancel_working.setText("Cancel")


	def log_working_window(self, msg):
		self.log.insertPlainText(msg + "\n")

	def __init__(self, window, signal):
		self.window = window
		self.signal = signal
		# Define buttons
		self.cancel_read = QPushButton('Cancel', self.window)
		self.load_model = QPushButton('Select SBML model', self.window)
		self.button_dem = QPushButton("Save model without Dead-End\n Metabolites (D.E.M.).")
		self.button_fva = QPushButton("Save model updated with Flux\n Variability Analysis (F.V.A.)")
		self.button_fva_dem = QPushButton("Save model updated with F.V.A. and\n without D.E.M.")
		self.button_spread = QPushButton("Save spreadsheet")
		self.cancel_working = QPushButton('Cancel')
		self.start_working = QPushButton('Start')
		self.change_model = QPushButton('<- Change model', self.window)

		# Hide buttons
		self.cancel_read.hide()
		self.load_model.hide()
		self.button_dem.hide()
		self.button_fva.hide()
		self.button_fva_dem.hide()
		self.button_spread.hide()
		self.cancel_working.hide()
		self.change_model.hide()
		self.start_working.hide()



class Controller:
	signal_model = None

	def signal_receive(self, text):
		pass

	def clicked_read(self):
		path = self.model.read_file()
		if path != "":
			self.view.hide_initial_load()
			self.view.show_loading_model(path)
			self.model.run_task(self.signal_model, TASK_READ_MODEL)

	def clicked_cancel_read(self):
		self.view.set_cancel_working_button_disabled()
		self.event_signal({"event": EVENT_STOP})
		#self.model.stop()
		self.view.hide_loading_model()
		self.view.show_initial_load()
		self.view.init_cancel_button()

	def clicked_save_dem(self):
		self.task = TASK_SAVE_DEM
		self.work_task(self.task)

	def clicked_save_fva(self):
		self.task = TASK_SAVE_FVA
		self.work_task(self.task)

	def clicked_save_fva_dem(self):
		self.task = TASK_SAVE_FVA_DEM
		self.work_task(self.task)

	def clicked_save_spreadsheet(self):
		self.task = TASK_SPREADSHEET
		self.work_task(self.task)

	def clicked_cancel_working(self):
		self.view.set_cancel_working_button_disabled()
		self.model.stop()
		#if self.model.is_stopped():
		self.view.init_cancel_button()
		# Simulate event to avoid showing twice
		self.event_signal({"event": EVENT_CANCEL})

	def clicked_change_model(self):
		self.view.hide_main()
		self.view.show_initial_load()

	def clicked_start_working(self):
		self.view.show_cancel_button()
		if self.task == TASK_SPREADSHEET:
			self.view.hide_objective_show_log()
		if self.task == TASK_SAVE_FVA:
			self.view.hide_objective_show_log()
		if self.task == TASK_SAVE_FVA_DEM:
			self.view.hide_objective_show_log()		
		self.model.run_task(self.signal_model, self.task)

	def work_task(self, task):
		if task == TASK_SPREADSHEET:
			self.view.hide_main()
			self.view.show_working_window_objective(task, self.model.reactions_list)
		elif task == TASK_SAVE_FVA:
			self.view.hide_main()
			self.view.show_working_window_objective(task, self.model.reactions_list)	
		elif task == TASK_SAVE_FVA_DEM:
			self.view.hide_main()
			self.view.show_working_window_objective(task, self.model.reactions_list)	
		else:
			self.view.hide_main()
			self.view.show_working_window(task)

	def model_loaded(self, result_ok, event):
		self.view.hide_loading_model()
		if not result_ok:
			self.view.retry_initial_load()
			print(result_ok, event)
			self.view.showErrorInitial("Error", "Couldn't read model", event["errors"][0], event)
		else:
			(model_id, reactions, metabolites, genes) = self.model.get_initial_model()
			self.view.show_main(model_id, reactions, metabolites, genes)

	def event_signal(self, result):
		event = result["event"]

		if event == EVENT_LOG:
			self.view.log_working_window(result["log"])

		elif event == EVENT_RETRY_INITIAL:
			self.view.show_initial_load()

		elif event == EVENT_READ_COMPLETE:
			self.model_loaded(result["result"], result)

		elif event == EVENT_CANCEL:
			self.view.hide_working_window()
			(model_id, reactions, metabolites, genes) = self.model.get_initial_model()
			self.view.show_main(model_id, reactions, metabolites, genes)

		elif event == EVENT_SAVE_SPREADSHEET:
			self.model.set_task(TASK_SPREADSHEET)
			self.model.set_signal(self.signal_model)
			self.model.run(TASK_SPREADSHEET)

		elif event == EVENT_SAVE_SPREADSHEET_DONE:
			self.model.run(TASK_SAVE_SPREADSHEET)

		elif event == EVENT_SAVE_SPREADSHEET_FILE_DONE:
			success = result["success"]
			path = result["result"]
			if success:
				self.view.showSuccess("Success", "Success saving file", "File saved at: " + path, event)
			elif path != '':
				self.view.showErrorSaveSpreadsheet("Error", "Couldn't save file", path, result)

		elif event == EVENT_WORK_FINISH:
			success = result["success"]
			error = result["result"]
			if success:
				self.model.run(TASK_SAVE_MODEL)
			else:
				self.view.hide_working_window()
				self.view.showErrorRunning("Error", "Something went wrong", error, result)

		elif event == EVENT_SAVE_FILE_FINISH:
			success = result["success"]
			path = result["result"]
			if success:
				self.view.showSuccess("Success", "Success saving file", "File saved at: " + path, event)
			else:
				self.view.showErrorSaveModel("Error", "Couldn't save file", path, result)

		elif event == EVENT_ERROR_RUNNING:
			error = result["errors"]
			self.view.hide_working_window()
			self.view.showErrorRunning("Error", "Something went wrong", error, result)

		elif event == EVENT_STOP:
			self.model.stop()

		elif event == EVENT_SET_OBJECTIVE:
			self.model.objective = result["result"]



	def __init__(self, view, model, signal_model):
		self.view = view
		self.model = model
		self.signal_model = signal_model

		# self.signal.connect(self.signal_receive)
		# self.model.set_signal(self.signal)
		# self.model.run_task()

		self.signal_model.connect(self.event_signal)

		self.view.load_model.clicked.connect(self.clicked_read)
		self.view.cancel_read.clicked.connect(self.clicked_cancel_read)
		self.view.button_dem.clicked.connect(self.clicked_save_dem)
		self.view.button_fva.clicked.connect(self.clicked_save_fva)
		self.view.button_fva_dem.clicked.connect(self.clicked_save_fva_dem)
		self.view.button_spread.clicked.connect(self.clicked_save_spreadsheet)
		self.view.cancel_working.clicked.connect(self.clicked_cancel_working)
		self.view.change_model.clicked.connect(self.clicked_change_model)
		self.view.start_working.clicked.connect(self.clicked_start_working)

		# Init execution
		self.view.show_initial_load()


class App(QMainWindow):
	__model_path = None
	view = None
	signal_model = pyqtSignal(dict)
	RUNNING = False

	def show_about(self):
		about = QMessageBox.about(self, self.tr('About Application'),
		                        self.tr('Application developed by Alex Oarga.  <br> Escuela de Ingeniería y Arquitectura <br> Universidad de Zaragoza <br> <br> Email: alex718123@gmail.com <br> Github: alexOarga <br>'))

	def show_help(self):
		MSG = "<h3>Issues</h3> <br>" \
		      "Please report any issues to https://github.com/alexOarga/findCritical/issues <br> " \
		      "<br>" \
		      "<h3>Steps</h3> <br> " \
		      "<strong>Step 1:</strong> Click 'Select SBML model' and upload a valid SBML model. The file format must be xml, json, yml or mat. Wait until the application reads the input file. <br>" \
		      "<strong>Step 2:</strong> Once the read of the input file is done the application will show the model id, number of reactions, number of metabolites and number of genes. Below it will display the buttons with the avaible operations. <br>" \
		      "<strong>Step 3:</strong> Click one of the following operations: <br>" \
		      "<ul> " \
		      " <li>'Generate spreadsheet': Generates a spreadsheet file with information about the model, reactions, metabolites, genes, dead-end metabolites found, chokepoint reactions and if the models is feasible, essential reactions and essential genes data. If the model choosed is large this proccess may take a long time. Some models may cause this procedures to block the application.</li>" \
		      " <li>'Save model without dead-end metabolites': Removes the dead-end metabolitos of the model along with the associated reactions and produces a new model. </li>" \
		      " <li>'Save model updated with flux variaiblity analysis': Produces a new model with the reactions bounds updated with the values obteined running flux variability analysis on the model.</li>" \
		      " <li>'Save model updated with flux variaiblity analysis without dead-end metabolites': Produces a new model with the reactions bounds updated with the values obteined running flux variability analysis on the model. After updating the model with flux variaiblity analysis it removes the dead-end metabolites of the model.</li>" \
		      "</ul>" \
		      "<strong>Step 4:</strong> Click 'Start' <br>" \
		      "<strong>Step 5:</strong> Once the operation chosen before ends, a window will display in order to choose the destination file. If the operation was 'generate spreadsheet' the output file must be xls or ods. If the operation produces a new models the output file must be xml, json, yml or mat. <br>" \

		helpDialog = QDialog(self)  # Added
		helpDialog.setAttribute(Qt.WA_DeleteOnClose)  # Added
		browser = QTextBrowser()
		browser.append(MSG)
		layout = QVBoxLayout()
		layout.addWidget(browser)
		helpDialog.setLayout(layout)  # Added
		helpDialog.setWindowTitle("Test App - Help")  # Added for neatness
		helpDialog.show()  # Changed

	def __init__(self):
		super().__init__()

		self.RUNNING = True

		self.resize(WIDTH, HEIGHT)
		self.setWindowTitle('FindCritical')

		self.setFocusPolicy(Qt.StrongFocus)

		extractAction = QAction("Help", self)
		extractAction.setShortcut("Ctrl+H")
		extractAction.setStatusTip('Get Help')
		extractAction.triggered.connect(self.show_help)

		extractAction2 = QAction("About", self)
		extractAction2.setShortcut("Ctrl+A")
		extractAction2.setStatusTip('About')
		extractAction2.triggered.connect(self.show_about)

		self.statusBar()

		mainMenu = self.menuBar()
		fileMenu = mainMenu.addMenu('&Help')
		fileMenu.addAction(extractAction)
		fileMenu.addAction(extractAction2)

		self.initGUI()

	def initGUI(self):
		try:
			self.view = View(self, self.signal_model)
			self.model = Model(self, self.signal_model)
			self.controller = Controller(self.view, self.model, self.signal_model)

			self.show()
		except Exception as error:
			print("This error shouldn't had happened. Please report it at https://github.com/alexOarga/findCritical/issues")
			msg = QMessageBox(self)
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Fatal error just occurred. ")
			msg.setInformativeText("This error shouldn't had happened. Please report it at https://github.com/alexOarga/findCritical/issues")
			msg.setWindowTitle("Error")
			msg.setStandardButtons(QMessageBox.Ok)
			horizontalSpacer = QSpacerItem(500, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
			layout = msg.layout()
			layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())
			msg.show()


if __name__ == '__main__':
		# Some Windows errors make the app to restart. Avoided temporarely with the 'RUNNING' flag.
		if not RUNNING:
			RUNNING = True
			app = QApplication(sys.argv)
			ex = App()
			app.exec_()

