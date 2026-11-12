// Buyer checkout: counts down and polls the charge until the transfer lands.
// The page is fully rendered by the server; this only keeps it current.
// Served as a file, not inline, because Talisman's CSP blocks inline script.
(function () {
  'use strict';

  var root = document.getElementById('checkout');
  if (!root) return;

  var POLL_MS = 5000;
  var statusUrl = root.getAttribute('data-status-url');
  var returnUrl = root.getAttribute('data-return-url');
  var status = root.getAttribute('data-status');
  var deadline = Date.now() + Number(root.getAttribute('data-seconds')) * 1000;
  var countdown = document.getElementById('countdown');
  var timer = countdown ? countdown.parentNode : null;
  var pollTimer = null;
  var tickTimer = null;

  function show(state) {
    status = state;
    var states = root.querySelectorAll('[data-when]');
    for (var i = 0; i < states.length; i++) {
      states[i].hidden = states[i].getAttribute('data-when') !== state;
    }
    if (state !== 'pending') {
      clearInterval(tickTimer);
      clearTimeout(pollTimer);
    }
    if (state === 'paid' && returnUrl) {
      // Give the buyer a moment to see it worked, then go back to the shop.
      setTimeout(function () { window.location.assign(returnUrl); }, 4000);
    }
  }

  function tick() {
    var left = Math.max(0, Math.round((deadline - Date.now()) / 1000));
    if (countdown) {
      var m = Math.floor(left / 60);
      var s = left % 60;
      countdown.textContent = m + ':' + (s < 10 ? '0' : '') + s;
    }
    if (timer) timer.classList.toggle('low', left <= 120);
    if (left === 0) {
      clearInterval(tickTimer);
      // Ask once more: a transfer may have landed in the last seconds.
      poll(true);
    }
  }

  function poll(final) {
    clearTimeout(pollTimer);
    fetch(statusUrl, { headers: { Accept: 'application/json' }, cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (body) {
        var next = body && body.data && body.data.status;
        if (next && next !== status) show(next);
        else if (final) show('expired');
      })
      .catch(function () { /* network blip: try again on the next poll */ })
      .then(function () {
        if (status === 'pending' && !final) pollTimer = setTimeout(poll, POLL_MS);
      });
  }

  function copy(button) {
    var text = button.getAttribute('data-copy');
    var done = function () {
      var label = button.textContent;
      button.textContent = 'Copied';
      setTimeout(function () { button.textContent = label; }, 1500);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () {});
      return;
    }
    var field = document.createElement('textarea');
    field.value = text;
    field.setAttribute('readonly', '');
    field.className = 'offscreen';
    document.body.appendChild(field);
    field.select();
    try { document.execCommand('copy'); done(); } catch (e) { /* ignore */ }
    document.body.removeChild(field);
  }

  var buttons = root.querySelectorAll('.copy');
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener('click', function (e) { copy(e.currentTarget); });
  }

  // A backgrounded tab on a phone stops timers; catch up when it returns.
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && status === 'pending') { tick(); poll(false); }
  });

  if (status === 'pending') {
    tickTimer = setInterval(tick, 1000);
    tick();
    pollTimer = setTimeout(poll, POLL_MS);
  } else {
    show(status);
  }
})();
