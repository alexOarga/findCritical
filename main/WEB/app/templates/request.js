$( document ).ready(function() {
	$("#ajax-upload").on("submit", function(e){
		e.preventDefault();
		var f = $(this);
		var formData = new FormData(document.getElementById("ajax-upload"));
        formData.append("dato", "valor");
            //formData.append(f.attr("name"), $(this)[0].files[0]);

		$.ajax({
         url: "http://127.0.0.1:8000/back/upload/",
            type: "post",
            dataType: "html",
            data: formData,
            cache: false,
            contentType: false,
     		processData: false,
        	success: function (data) {
          		alert("SUCCESS");
        	},
			error: function (xhr,errmsg,err) {
        		alert(xhr.status + ": " + xhr.responseText + ": " + err);
    		}
      	});
		return false;
	});
});