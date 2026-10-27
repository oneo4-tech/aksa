// Local clock for the AKSA OS shell. No data reads happen here.
const clock = document.getElementById("clock");
const tickerClock = document.getElementById("ticker-clock");

function render() {
  const now = new Date();
  if (clock) {
    clock.textContent = now.toLocaleTimeString([], { hour12: false });
  }
  if (tickerClock) {
    tickerClock.textContent = now.toISOString().slice(0, 19).replace("T", " ") + " UTC";
  }
}

render();
setInterval(render, 1000);
