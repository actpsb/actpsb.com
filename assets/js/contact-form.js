// Optional enhancement for the contact form. Without JavaScript the form posts natively to
// contact-submit.php and the server renders the result. This script never reports success on its own:
// it shows what the server returned, and a network failure leaves submission status unconfirmed.
(function (root) {
  var MIN_MESSAGE = 10;
  var MAX_MESSAGE = 5000;
  var CATEGORIES = ["NSX Nominated Adviser", "IPO & Capital Markets", "Corporate Advisory", "Mergers & Acquisitions", "General Enquiry"];
  var KNOWN_STATES = ["accepted", "invalid", "failed", "rejected", "rate_limited", "unavailable"];
  var UNCONFIRMED = "We could not confirm your submission. Please contact us using the published email or telephone number before resubmitting.";

  function len(v) { return Array.from(v).length; }

  // Mirrors the server rules (Validator.php) so obvious mistakes are caught before anything is sent.
  // The server still validates everything; this is a convenience, not a security control.
  function validate(v) {
    var e = {};
    var name = (v.name || "").trim();
    var email = (v.email || "").trim();
    var message = (v.message || "").replace(/\r\n?/g, "\n").trim();
    if (!name) e.name = "Enter your name.";
    else if (len(name) > 100) e.name = "Use no more than 100 characters.";
    if (!email) e.email = "Enter your email address.";
    else if (email.length > 254 || !/^[A-Za-z0-9.!#$%&'*+\/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/.test(email)) e.email = "Enter a valid email address.";
    if ((v.organisation || "").trim().length > 150) e.organisation = "Use no more than 150 characters.";
    if (CATEGORIES.indexOf((v.category || "").trim()) === -1) e.category = "Select a nature of enquiry from the list.";
    if (len(message) < MIN_MESSAGE) e.message = "Enter a message of at least " + MIN_MESSAGE + " characters.";
    else if (len(message) > MAX_MESSAGE) e.message = "Use no more than " + MAX_MESSAGE + " characters.";
    return e;
  }

  // Turns whatever came back into a truthful outcome. Success requires HTTP 200 and a JSON body with
  // status "accepted". Anything that cannot be read as a server answer is never shown as success, and is
  // only called "not sent" when the HTTP status proves the request was refused before processing
  // (4xx or 503); other statuses (2xx/3xx without a valid answer, 500, 502, 504...) are unconfirmed.
  // networkError covers offline, timeout and abort, where the outcome is unknown.
  function interpret(httpStatus, bodyText, networkError) {
    if (networkError) return { state: "unconfirmed", message: UNCONFIRMED, errors: null, reference: null };
    var d = null;
    try { d = JSON.parse(bodyText); } catch (err) { d = null; }
    if (d && typeof d === "object" && !Array.isArray(d) && typeof d.status === "string") {
      var okStatus = httpStatus === 200;
      if (d.status === "accepted") {
        if (okStatus && typeof d.message === "string") return { state: "accepted", message: d.message, errors: null, reference: d.reference };
        return { state: "unconfirmed", message: UNCONFIRMED, errors: null, reference: null };
      }
      if (KNOWN_STATES.indexOf(d.status) !== -1 && !okStatus) {
        var fallback = d.status === "invalid" ? "Your message was not sent. Please correct the problems listed below." : "Your message was not sent.";
        var errs = d.errors && typeof d.errors === "object" ? d.errors : null;
        // A server "failed" is the mail-sending stage: it may or may not have reached the mail server, so it stays unconfirmed in the UI.
        return { state: d.status, message: typeof d.message === "string" && d.message ? d.message : fallback, errors: errs, reference: typeof d.reference === "string" ? d.reference : null };
      }
    }
    if ((httpStatus >= 400 && httpStatus < 500) || httpStatus === 503) {
      return { state: "rejected", message: "Your message was not sent: the site could not accept the enquiry right now (HTTP " + httpStatus + "). Please use the published email or telephone number.", errors: null, reference: null };
    }
    return { state: "unconfirmed", message: UNCONFIRMED, errors: null, reference: null };
  }

  var api = { validate: validate, interpret: interpret, CATEGORIES: CATEGORIES };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.ActpContactForm = api;
  if (typeof document === "undefined") return;

  var status = document.getElementById("form-status");
  var notice = document.getElementById("form-availability");
  var tpl = document.getElementById("enquiry-form-template");
  if (!status || !window.fetch || !window.FormData) return;
  var form = document.querySelector("form.contact-form");

  if (!form) {
    if (!notice || !tpl || !tpl.content) return;
    notice.replaceWith(tpl.content.cloneNode(true));
    form = document.querySelector("form.contact-form");
  }
  if (form) enhance();

  function enhance() {
    var button = form.querySelector("button[type=submit]");
    var FIELDS = ["name", "email", "organisation", "category", "message"];
    var submitting = false;
    var buttonContent = button.innerHTML;

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
      if (submitting) return;
      clearErrors();
      var fd = new FormData(form);
      var values = {};
      FIELDS.forEach(function (k) { var x = fd.get(k); values[k] = typeof x === "string" ? x : ""; });
      var local = validate(values);
      if (Object.keys(local).length) {
        show("invalid", "Your message was not sent. Please correct the problems listed below.", local, null);
        return;
      }
      submitting = true;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      form.setAttribute("aria-busy", "true");
      button.textContent = "Sending...";
      var controller = window.AbortController ? new AbortController() : null;
      var timeout = window.setTimeout(function () { if (controller) controller.abort(); }, 20000);
      // One attempt only. There is deliberately no automatic retry: after an uncertain outcome a retry could duplicate an enquiry.
      fetch(form.getAttribute("action"), {
        method: "POST",
        body: fd,
        headers: { Accept: "application/json" },
        credentials: "same-origin",
        signal: controller ? controller.signal : undefined
      }).then(function (res) {
        return res.text().then(function (t) { return interpret(res.status, t, false); }, function () { return interpret(res.status, "", true); });
      }, function () {
        return interpret(0, "", true);
      }).then(function (r) {
        if (r.state === "accepted") form.reset();
        show(r.state, r.message, r.errors, r.reference);
      }).then(function () {
        window.clearTimeout(timeout);
        submitting = false;
        button.disabled = false;
        button.removeAttribute("aria-busy");
        form.removeAttribute("aria-busy");
        button.innerHTML = buttonContent;
      });
    });
  }
})(typeof window !== "undefined" ? window : globalThis);
