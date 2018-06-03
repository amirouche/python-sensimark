let graphing = function(json) {
  let width = $(window).width() - 100;
  let html = $('<canvas id="myChart" width="' + width + '" height="800"></canvas>');
  var ctx = html[0].getContext("2d");

  var data = [];

  for (let category of json) {
    for (let subcategory of category.children) {
      let item = {
        name: subcategory.name + ' (' + category.name + ')',
        prediction: subcategory.prediction,
      }
      data.push(item);
    }
  }

  data = data.sort(function(a, b) { return a.prediction < b.prediction });

  $('#graph').append(html);

  var myChart = new Chart(ctx, {
    type: 'horizontalBar',
    data: {
      labels: data.map(item => item.name),
      datasets: [{
        label: 'Category',
        data: data.map(item => item.prediction),
        backgroundColor: 'rgba(132, 99, 255, 0.4)'
      }]
    }
  });
};

let execute = function(event) {
  event.preventDefault();

  let url = $("#input input[type='text']").val();

  console.log('Trying ' + url);

  $("#output").text("Analysis in progress...");
  $("#graph").text("Graphing in progress...");

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
    let endpoint = '/api/v0?url=' + url + '&all=1';

    jQuery.ajax(endpoint, {success: graphing})

  }});
};

$("#input form").bind('submit', execute);
