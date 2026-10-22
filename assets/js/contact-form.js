// Optional enhancement for the contact form. Without JavaScript the form posts natively to
// contact-submit.php and the server renders the result. This script never reports success on its own:
// it shows what the server returned, and a network failure leaves submission status unconfirmed.
(function () {
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
      submitting = true;
      clearErrors();
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      form.setAttribute("aria-busy", "true");
      button.textContent = "Sending...";
      var controller = window.AbortController ? new AbortController() : null;
      var timeout = window.setTimeout(function () { if (controller) controller.abort(); }, 20000);
      fetch(form.getAttribute("action"), {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
        credentials: "same-origin",
        signal: controller ? controller.signal : undefined
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
        show("failed", "We could not confirm your submission. Please contact us using the published email or telephone number before resubmitting.", null, null);
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
})();
