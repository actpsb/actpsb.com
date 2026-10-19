// Optional enhancement for the contact form. Without JavaScript the form posts natively to
// contact-submit.php and the server renders the result. This script never reports success on its own:
// it shows what the server returned, and a network failure is shown as "not sent".
(function () {
  var status = document.getElementById("form-status");
  var notice = document.getElementById("form-availability");
  var tpl = document.getElementById("enquiry-form-template");
  if (!status || !window.fetch || !window.FormData) return;
  var form = document.querySelector("form.contact-form");

  // Fail closed: the form is revealed only when the server's preflight says its configuration is
  // valid. Any failure, timeout or unexpected response leaves the unavailable notice in place.
  // The preflight never contacts the mail server and sends no visitor data.
  if (!form) {
    if (!notice || !tpl || !tpl.content) return;
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = window.setTimeout(function () { if (ctl) ctl.abort(); }, 8000);
    fetch("contact-submit.php?preflight=1", { headers: { Accept: "application/json" }, credentials: "same-origin", cache: "no-store", signal: ctl ? ctl.signal : undefined })
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (d) {
        window.clearTimeout(timer);
        if (!d || d.available !== true) return;
        notice.replaceWith(tpl.content.cloneNode(true));
        form = document.querySelector("form.contact-form");
        if (form) enhance();
      })
      .catch(function () { window.clearTimeout(timer); });
    return;
  }
  enhance();

  function enhance() {
  var button = form.querySelector("button[type=submit]");
  var FIELDS = ["name", "email", "organisation", "message"];

  function clearErrors() {
    FIELDS.forEach(function (k) {
      var input = document.getElementById("field-" + k);
      var old = document.getElementById("error-" + k);
      if (old) old.remove();
      if (input) {
        input.removeAttribute("aria-invalid");
        var d = (input.getAttribute("aria-describedby") || "").split(" ").filter(function (id) { return id && id !== "error-" + k; });
        if (d.length) input.setAttribute("aria-describedby", d.join(" ")); else input.removeAttribute("aria-describedby");
        input.parentNode.classList.remove("field--invalid");
      }
    });
  }

  function show(state, message, errors, reference) {
    status.textContent = "";
    status.className = "form-status form-status--" + state;
    status.setAttribute("role", state === "accepted" ? "status" : "alert");
    var p = document.createElement("p");
    p.textContent = message;
    status.appendChild(p);
    var keys = errors ? Object.keys(errors).filter(function (k) { return FIELDS.indexOf(k) !== -1; }) : [];
    if (keys.length) {
      var ul = document.createElement("ul");
      keys.forEach(function (k) {
        var label = form.querySelector('label[for="field-' + k + '"]');
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#field-" + k;
        a.textContent = (label ? label.textContent : k) + ": " + errors[k];
        li.appendChild(a);
        ul.appendChild(li);
        var input = document.getElementById("field-" + k);
        if (input) {
          var err = document.createElement("p");
          err.className = "field__error";
          err.id = "error-" + k;
          err.textContent = errors[k];
          input.parentNode.insertBefore(err, input);
          input.setAttribute("aria-invalid", "true");
          input.setAttribute("aria-describedby", ("error-" + k + " " + (input.getAttribute("aria-describedby") || "")).trim());
          input.parentNode.classList.add("field--invalid");
        }
      });
      status.appendChild(ul);
    }
    if (reference && state !== "accepted") {
      var r = document.createElement("p");
      r.className = "form-status__ref";
      r.textContent = "Reference: " + reference;
      status.appendChild(r);
    }
    status.focus();
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors();
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    fetch(form.getAttribute("action"), {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" },
      credentials: "same-origin"
    }).then(function (res) {
      return res.json().then(function (data) { return { ok: res.ok, data: data }; });
    }).then(function (r) {
      var d = r.data || {};
      if (r.ok && d.status === "accepted") {
        form.reset();
        show("accepted", d.message, null, d.reference);
      } else {
        show(d.status || "failed", d.message || "Your message was not sent.", d.errors, d.reference);
      }
    }).catch(function () {
      show("failed", "Your message was not sent because the site could not be reached or returned an unexpected response. Nothing has been delivered. Please try again later.", null, null);
    }).then(function () {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    });
  });
  }
})();
