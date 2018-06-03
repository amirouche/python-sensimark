$("#input input[type='submit']").click(function() {
  let url = $("#input input[type='text']").val();
  let endpoint = 'http://0.0.0.0:8000/api/v0?url=' + url + '&top=3';
  jQuery.ajax(endpoint, {success: function(json) {
  }});
});

let json = [
  {"name": "Technology", "prediction": 46.738571215633584},
  {"name": "Health and medicine", "prediction": 46.62513306741829}
]

let message = "This is about ";

for (let index in json) {
  let item = json[index];
  let name = item['name'];
  if (index === 0 && index === json.length -1) {
    // first and last
    message += name + "!";
  } else if (index === (json.length - 1))  {
    // last
    message += "and " + name +  "!";
  } else if (index == 0) {
    // first
    message += name + " ";
  } else {
    // other
    message += ", " + name;
  }

  $("#output").text(message)
}
