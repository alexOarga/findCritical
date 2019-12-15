
(function (window) {
	'use strict';


	/**
	     * View that abstracts away the browser's DOM completely.
	     * It has two simple entry points:
	     *
	     *   - bind(eventName, handler)
	     *     Takes a todo application event and registers the handler
	     *   - render(command, parameterObject)
	     *     Renders the given command with the options
	     */
	function View() {
		// view componentes
		this.ajax_upload = $("#ajax-upload");
		this.sumbit = $("#sumbit");
		this.cancel_upload = $("#cancel-upload");
		this.retry_upload = $("#retry-upload");
		this.change_model = $("#change-model");
		this.bt_spread = $("#bt-spread");
		this.bt_dem = $("#bt-dem");
		this.bt_fva = $("#bt-fva");
		this.bt_fvadem = $("#bt-fvadem");
		this.cancel_work = $("#cancel-work");
		this.bt_run_other_task = $("#run-other-task");
		this.bt_download = $("#download");
		this.retry_work = $("#retry-work");

		this.error_text_read = $("#error-text-read");
		this.model_info = $("#model-info");
		this.task = $("#task");
		this.log_window = $("#log");
		this.error_text_work = $("#error-text-work");

		this.page_upload = $("#page-upload");
		this.page_error_loading = $("#error-loading");
		this.page_loading = $("#loading");
		this.page_main = $("#main");
		this.page_work = $("#work");
		this.page_done = $("#done");
		this.page_error_working = $("#error-working");

	}



	// View procedures
	View.prototype._setUpload = function (res) {
		this.sumbit.attr('value', 'Upload');
		this.sumbit.prop("disabled",false);
		this.page_loading.hide();
		this.page_error_loading.hide();
		this.page_main.hide();
		this.page_work.hide();
		this.page_upload.show();
	};

	View.prototype._setLoading = function (res) {
		this.sumbit.attr('value', 'Uploading...');
		this.sumbit.prop("disabled",true);
	};

	View.prototype._setLoadingPage = function (res) {
		this.page_upload.hide();
		this.model_info.attr('value', 'Cancelling...');
		this.page_loading.show();
	};

	// call after load
	View.prototype._setMain = function (res) {
		this.page_loading.hide();
		this.model_info.html("<b>Model:</b> " + res["model"] + "<br>" +
					"<b>Reactions:</b> " + res["reactions"] + "<br>" +
					"<b>Metabolites:</b> " + res["metabolites"] + "<br>" + 
					"<b>Genes:</b> " + res["genes"] + "<br>"
				    );	
		this.page_main.show();
		// The next line avoids some timing errors.
		// In some cases the server response is faster than the execution 
		//		of the browser code. This causes loading and main pages to
		//		show at the same time
		this.page_loading.hide();
	};

	// call after task
	View.prototype._setMainAfterTask = function (res) {
		this.page_done.hide();			// from work finished
		this.page_work.hide();			// from cancel work button
		this.page_error_working.hide(); // from error page
		this.page_main.show();
	}

	// call on task done
	View.prototype._setTaskDone = function (res) {
		this.bt_download.attr('href', res);
		this.page_work.hide();
		this.page_done.show();		
	}

	View.prototype._cancelLoading = function (res) {
		this.cancel_upload.attr('value', 'Cancelling...');
		this.cancel_upload.prop("disabled",true);
	};

	View.prototype._setErrorRead = function (res) {
		this.page_loading.hide();
		this.error_text_read.text(res);
		this.page_error_loading.show();
	};

	View.prototype._setWorking = function (res) {
		this.page_main.hide();
		this.task.html(res);
		this.log_window.html("Please wait... <br />");
		this.page_work.show();
	};

	View.prototype._setErrorWorking = function (res) {
		this.page_work.hide();
		this.error_text_work.text(res);
		this.page_error_working.show();
	}


	// Bind commands with their view precedures
	View.prototype.render = function (viewCmd, parameter) {
		var self = this;
		var viewCommands = {
			"setLoading": function () {
				self._setLoading(parameter);
			},
			"setLoadingPage": function () {
				self._setLoadingPage(parameter);
			},
			"setUpload": function () {
				self._setUpload(parameter);
			},
			"setMain": function () {
				self._setMain(parameter);
			},
			"setErrorRead": function () {
				self._setErrorRead(parameter);
			},
			"setCancelLoading": function () {
				self._cancelLoading(parameter);
			},
			"activeCancelLoading": function () {
				self.cancel_upload.prop("disabled",false);
			},
			"setWorking": function () {
				self._setWorking(parameter);
			},
			"setErrorWorking": function () {
				self._setErrorWorking(parameter);
			},
			"activeCancelWork": function () {
				self.cancel_work.prop("disabled",false);
			},
			"desactiveCancelWork": function () {
				self.cancel_work.prop("disabled",true);
			},
			"addLog": function () {
				self.log_window.append(parameter + "<br />");
			},
			"setMainAfterTask": function () {
				self._setMainAfterTask(parameter);
			},
			"setTaskDone": function () {
				self._setTaskDone(parameter);
			}
		};

		viewCommands[viewCmd]();
	};

	// Bind view actions to specific handlers
	View.prototype.bind = function (event, handler) {
		var self = this;
		if (event === 'ajaxUpload'){
			$("#ajax-upload").on("submit", function(e){
				e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'cancelUpload') {
			this.cancel_upload.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'retryUpload') {
			this.retry_upload.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'changeModel') {
			this.change_model.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'runSPREAD') {
			this.bt_spread.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'runDEM') {
			this.bt_dem.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'runFVA') {
			this.bt_fva.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'runFVADEM') {
			this.bt_fvadem.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'cancelWork') {
			this.cancel_work.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'retryWork') {
			this.retry_work.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		} else if (event === 'runOtherTask') {
			this.bt_run_other_task.click(function(e) {
			  	e.preventDefault();
				handler();
				return false;
			});
		}
	};

	// Export to window
	window.app = window.app || {};
	window.app.View = View;
}(window));
