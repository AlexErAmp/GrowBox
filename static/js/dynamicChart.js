Chart.defaults.global.responsive = false;
var tempData = {
  labels : [],
  datasets : [{
    label : "Temperature",
    fill : true,
    backgroundColor: "rgba(75,192,192,0.4)",
    borderColor: "rgba(75,192,192,1)",
    borderCapStyle: 'butt',
    borderDash: [],
    borderDashOffset: 0.0,
    borderJoinStyle: 'miter',
    pointBorderColor: "rgba(75,192,192,1)",
    pointBackgroundColor: "#fff",
    pointBorderWidth: 1,
    pointHoverRadius: 5,
    pointHoverBackgroundColor: "rgba(75,192,192,1)",
    pointHoverBorderColor: "rgba(220,220,220,1)",
    pointHoverBorderWidth: 2,
    pointRadius: 1,
    pointHitRadius: 10,
    data : [],
    spanGaps: false
  }]
};

function callback(weatherData, status) {
  if (status == "success") {
    var tempCanv = document.getElementById("canvas").getContext("2d");
    var time = (new Date()).getSeconds();
    if (tempChart.data.labels.length < 10) {

      tempChart.data.labels.push(time);
      tempChart.data.datasets[0].data.push(Math.random()*25);
    }
    else {
      tempChart.data.labels.push(time);
      tempChart.data.labels.shift();
      tempChart.data.datasets[0].data.push(Math.random()*25);
      tempChart.data.datasets[0].data.shift();
    }
  window.tempChart.update();
  }
  setTimeout(getReading, 1000);
}

function getReading() {
  $.get('/tempmeas', callback);
}

function getTime() {
  var time = setInterval(function(){
          var date = new Date();
          var time = date.toLocaleTimeString();
          return time;
        }, 1000);
  return time;
}



window.onload = function() {
  var tempCanv = document.getElementById('canvas').getContext('2d');
  window.tempChart = new Chart(tempCanv, {
          type: 'line',
          data: tempData
  });
}
