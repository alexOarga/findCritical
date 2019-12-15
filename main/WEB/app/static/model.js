(function (window) {
	'use strict';

	/**
	 * Creates a new Model instance and hooks up the storage.
	 *
	 * @constructor
	 * @param {object} storage A reference to the client side storage class
	 */
	function Model() {
		this.varr = 0;
	}

	/**
	 * Creates a new todo model
	 *
	 * @param {string} [title] The title of the task
	 * @param {function} [callback] The callback to fire after the model is created
	 */
	Model.prototype.uploadFile = async function () {		
		var f = $(this);
		var formData = new FormData(document.getElementById("ajax-upload"));
		formData.append("dato", "valor");
			//formData.append(f.attr("name"), $(this)[0].files[0]);
		const result = await $.ajax({
		 url: "http://127.0.0.1:8000/app/upload/",
			type: "post",
			dataType: "html",
			data: formData,
			cache: false,
			contentType: false,
	 		processData: false,
			success: function (data) {
		  		//alert("SUCCESS upload");
			},
			error: function (xhr,errmsg,err) {
				alert(xhr.status + ": " + xhr.responseText + ": " + err);
			}
	  	});
		return false;
	};


	Model.prototype.runWork = async function (task) {
		const data2 = new FormData();
		data2.append('task', task);
		const result = await $.ajax({
		 	url: "http://127.0.0.1:8000/app/work/",
			type: "post",
			dataType: "html",
			data: data2, 
			cache: false,
			contentType: false,
	 		processData: false,
			success: function (data) {
		  		//alert("success work send");
			},
			error: function (xhr,errmsg,err) {
				alert(xhr.status + ": " + xhr.responseText + ": " + err);
			}
	  	});
		return result;
	};


	Model.prototype.cancelUpload = async function () {		
		const result = await $.ajax({
		 	url: "http://127.0.0.1:8000/app/cancel/",
			type: "get",
			dataType: "html",
			cache: false,
			contentType: false,
	 		processData: false,
			success: function (data) {
		  		//alert(data);
			},
			error: function (xhr,errmsg,err) {
				alert(xhr.status + ": " + xhr.responseText + ": " + err);
			}
	  	});
		return result;
	};

	// not-used
	Model.prototype.download = async function () {		
		const result = await $.ajax({
		 	url: "http://127.0.0.1:8000/app/download_file/",
			type: "post",
			dataType: "html",
			cache: false,
			contentType: false,
	 		processData: false,
			success: function (data) {
		  		//alert(data);
				console.log("FILE OK!");
			},
			error: function (xhr,errmsg,err) {
				alert(xhr.status + ": " + xhr.responseText + ": " + err);
				return "error";
			}
	  	});
		return result;
	};


	Model.prototype.sendChannel = async function (arg) {		
			//formData.append(f.attr("name"), $(this)[0].files[0]);
			console.log("model sending: " + arg);
			const data2 = new FormData();
			data2.append('channel', arg)
			const result = await $.ajax({
			 url: "http://127.0.0.1:8000/app/set_channel/",
				type: "post",
				dataType: "html",
				data: data2, 
				cache: false,
				contentType: false,
		 		processData: false,
				success: function (data) {
			  		//alert("SUCCESS channel sent");
				},
				error: function (xhr,errmsg,err) {
					alert(xhr.status + ": " + xhr.responseText + ": " + err);
				}
		  	});
			return result;
		};

	Model.prototype.listenChannel = async function (dispatch_socket){

			let promise = new Promise((resolve, reject) => {
				console.log("Model listen");
				dispatch_socket.onmessage = function(message) {
					console.log("Model got message: " + message.data);
					var data = JSON.parse(message.data)
					console.log(data);
					if(typeof data["channel"] !== 'undefined'){
						resolve(data)
					}else{
						resolve(data);
					}
					if(data["result"]=="log"){
						resolve(data);
					}
				};
			});

			
			const result = await promise.then((message) => {
				return message;
			});

			console.log("resultado:" + result);
			return result;
	}
	

	// Export to window
	window.app = window.app || {};
	window.app.Model = Model;
})(window);
