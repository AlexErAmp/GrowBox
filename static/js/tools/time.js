window.onload = function() {
  function formatDisplayTime(time) {
    var hours = time.getHours();
    var minutes = time.getMinutes();
    var day = time.getDate();
    var month = time.getMonth() + 1;
    var year = time.getFullYear();

    if (hours < 10) {
      hours = '0' + hours;
    }

    if (minutes < 10) {
      minutes = '0' + minutes;
    }

    if (day < 10) {
      day = '0' + day;
    }

    if (month < 10) {
      month = '0' + month;
    }
    return [hours, minutes].join(':') + '&ensp;' + [day, month, year].join('.');
  }

  function tickTimer() {
    document.getElementById('clock').innerHTML = formatDisplayTime(new Date());
  }
  tickTimer();
  window.setInterval(tickTimer, 1000);
};
