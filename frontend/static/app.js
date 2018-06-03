let execute = function(event) {
    event.preventDefault();

    let url = $("#input input[type='text']").val();
    console.log('Trying ' + url);
    $("#output").text("Analysis in progress...");
    let endpoint = '/api/v0?url=' + url + '&top=3';
    jQuery.ajax(endpoint, {success: function(json) {
	// on success
	let message = "This is about ";

	for (let index in json) {
	    index = parseInt(index);
	    let item = json[index];
	    let name = item['name'];
	    if (index === 0 && index === json.length - 1) {
		// first and last
		message += name + "!";
	    } else if (index === json.length - 1)  {
		// last
		message += " and " + name +  "!";
	    } else if (index == 0) {
		// first
		message += name;
	    } else {
		// other
		message += ", " + name;
	    }

	    $("#output").text(message)
	}

    }});
}

$("#input form").bind('submit', execute);
