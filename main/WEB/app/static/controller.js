(function (window) {
	'use strict';

	/**
	 * Takes a model and view and acts as the controller between them
	 *
	 * @constructor
	 * @param {object} model The model instance
	 * @param {object} view The view instance
	 */
	function Controller(model, view, dispatch_socket) {
		var self = this;
		self.model = model;
		self.view = view;
		self.dispatch_socket = dispatch_socket;

		 self.listen_channel("channel");

		self.view.bind('ajaxUpload', function () {
			self.ajaxUpload();
		});

		self.view.bind('cancelUpload', function () {
			self.cancelUpload();
		});

		self.view.bind('retryUpload', function () {
			self.showUpload();
		});

		self.view.bind('changeModel', function () {
			self.showUpload();
		});
		self.view.bind('runSPREAD', function () {
			self.runWork("SPREAD");
		});
		self.view.bind('runDEM', function () {
			self.runWork("DEM");
		});
		self.view.bind('runFVA', function () {
			self.runWork("FVA");
		});
		self.view.bind('runFVADEM', function () {
			self.runWork("FVADEM");
		});
		self.view.bind('runOtherTask', function () {
			self.runOtherTask();
		});
		self.view.bind('download', function () {
			self.download();		
		});
		self.view.bind('cancelWork', function () {
			self.cancelWork();		
		});
		self.view.bind('retryWork', function () {
			self.retryWork();		
		});
	}

	
	/**
	 * An event to fire whenever you want to add an item. Simply pass in the event
	 * object and it'll handle the DOM insertion and saving of the new item.
	 */


	Controller.prototype.ajaxUpload = async function () {
		var self = this;
		self.listen_channel("result");
		self.view.render("setLoading");
		var aux = await self.model.uploadFile();
		self.view.render("setLoadingPage");
	};

	Controller.prototype.cancelUpload = async function () {
		var self = this;
		self.view.render("setCancelLoading");
		self.model.cancelUpload();
		self.view.render("setUpload");
		self.view.render("activeCancelLoading");
	};

	Controller.prototype.showUpload = async function () {
		var self = this;
		self.listen_channel("result");
		self.view.render("setUpload");
	};

	Controller.prototype.runWork = async function (task) {
		var self = this;
alert(task);
		self.view.render("desactiveCancelWork");
		if(task=="SPREAD"){
			self.view.render("setWorking", "<b>Task:</b> Generating spreadhseet file with results");
		}else if(task=="DEM"){
			self.view.render("setWorking", "<b>Task:</b> Generating model file without Dead End Metabolites");
		}else if(task=="FVA"){
			self.view.render("setWorking", "<b>Task:</b> Generating model file with flux updated with Flux Variability Analysis");
		}else if(task=="FVADEM"){
			self.view.render("setWorking", "<b>Task:</b> Generating model file with flux updated with Flux Variability Analysis without Dead End Metabolites");
		}	
		self.listen_log();
		const done = await self.model.runWork(task);
		self.view.render("activeCancelWork");	
	};


	Controller.prototype.runOtherTask = async function () {
		var self = this;
		self.view.render("setMainAfterTask", 'http://127.0.0.1:8000/app/download_file/');
	};


	Controller.prototype.download = async function () {
		// nothing here
	};

	Controller.prototype.cancelWork = async function () {
		var self = this;
		self.view.render("desactiveCancelWork");
		self.model.cancelUpload();
		self.view.render("setMainAfterTask");
		self.view.render("activeCancelWork");
	};

	Controller.prototype.retryWork = async function () {
		var self = this;
		self.view.render("setMainAfterTask");
	};

	Controller.prototype.listen_channel = async function (end_key) {
		var self = this;
		do{
			var data = await self.model.listenChannel(self.dispatch_socket);
			if(data["result"]=="readComplete"){
				if(data["message"] == "ok"){
					self.view.render("setMain", data);
				}else{
					self.view.render("setErrorRead", data["message"]);
				}
			}
			if(typeof data["channel"] !== 'undefined'){
				const result = await self.model.sendChannel(data["channel"]);
			}
		}while(typeof data[end_key] == 'undefined');
	};

	Controller.prototype.listen_log = async function () {
		var self = this;
		do{
			var data = await self.model.listenChannel(self.dispatch_socket);
			if(data["result"]=="log"){
				self.view.render("addLog", data["message"]);
			}
		}while(data["result"] != "workDone");
		if(data["message"] == "workDone"){
			self.view.render("setTaskDone");
		}else{
			self.view.render("setErrorWorking", data["message"]);
		}
	};

	

	// Export to window
	window.app = window.app || {};
	window.app.Controller = Controller;
})(window);
