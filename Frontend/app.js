const alertBox = document.querySelector("#alert");
const visitorForm = document.querySelector("#visitor-form");
const otpForm = document.querySelector("#otp-form");
const passPanel = document.querySelector("#pass-panel");
let visitorEmail = "";

function showMessage(message, isError = false) {
  alertBox.textContent = message;
  alertBox.classList.toggle("error", isError);
  alertBox.hidden = false;
}

function clearMessage() {
  alertBox.hidden = true;
  alertBox.textContent = "";
  alertBox.classList.remove("error");
}

async function api(path, options = {}) {
  const response = await fetch(`/api/${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    throw new Error(typeof detail === "string" ? detail : "Something went wrong. Please try again.");
  }
  return payload;
}

function setStep(step) {
  document.querySelector("#step-count").textContent = String(step).padStart(2, "0");
  document.querySelector("#progress-bar").style.width = `${step * 33.333}%`;
}

function setLoading(button, loading, text) {
  button.disabled = loading;
  if (loading) {
    button.dataset.original = button.innerHTML;
    button.querySelector("span").textContent = text;
  } else if (button.dataset.original) {
    button.innerHTML = button.dataset.original;
    delete button.dataset.original;
  }
}

visitorForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();
  const button = visitorForm.querySelector("button[type=submit]");
  setLoading(button, true, "Sending your code…");
  const data = Object.fromEntries(new FormData(visitorForm).entries());
  try {
    const result = await api("submit_form", { method: "POST", body: JSON.stringify(data) });
    visitorEmail = result.email;
    document.querySelector("#otp-email").textContent = visitorEmail;
    visitorForm.hidden = true;
    otpForm.hidden = false;
    otpForm.elements.otp.focus();
    setStep(2);
    if (result.development_otp) {
      showMessage(`Local development code: ${result.development_otp}. In production, this code is sent by email.`);
    } else {
      showMessage(result.message);
    }
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    setLoading(button, false);
  }
});

otpForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();
  const button = otpForm.querySelector("button[type=submit]");
  setLoading(button, true, "Verifying…");
  try {
    const result = await api("verify_otp", {
      method: "POST",
      body: JSON.stringify({ email: visitorEmail, otp: otpForm.elements.otp.value.trim() }),
    });
    document.querySelector("#pass-qr").src = result.qr_code;
    document.querySelector("#pass-visitor").textContent = result.visitor.name;
    document.querySelector("#pass-purpose").textContent = result.visitor.purpose;
    document.querySelector("#pass-expiry").textContent = new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium", timeStyle: "short",
    }).format(new Date(result.expires_at));
    otpForm.hidden = true;
    passPanel.hidden = false;
    setStep(3);
    showMessage(result.message);
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    setLoading(button, false);
  }
});

document.querySelector("#back-to-details").addEventListener("click", () => {
  clearMessage();
  otpForm.hidden = true;
  visitorForm.hidden = false;
  setStep(1);
});

document.querySelector("#new-visit").addEventListener("click", () => {
  visitorForm.reset();
  otpForm.reset();
  visitorEmail = "";
  passPanel.hidden = true;
  visitorForm.hidden = false;
  clearMessage();
  setStep(1);
  document.querySelector("#home").scrollIntoView({ behavior: "smooth" });
});

document.querySelector("#gate-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type=submit]");
  const resultBox = document.querySelector("#gate-result");
  resultBox.hidden = true;
  setLoading(button, true, "Checking…");
  try {
    const result = await api("validate_pass", {
      method: "POST",
      body: JSON.stringify({ token: form.elements.token.value.trim() }),
    });
    resultBox.textContent = result.valid
      ? `Entry approved for ${result.visitor} · ${result.purpose}`
      : result.message;
    resultBox.classList.toggle("invalid", !result.valid);
    resultBox.hidden = false;
    if (result.valid) form.reset();
  } catch (error) {
    resultBox.textContent = error.message;
    resultBox.classList.add("invalid");
    resultBox.hidden = false;
  } finally {
    setLoading(button, false);
  }
});

async function loadAnalytics() {
  try {
    const stats = await api("analyse_visitors");
    document.querySelector("#metric-total").textContent = stats.total_visitors;
    document.querySelector("#metric-verified").textContent = stats.verified_visitors;
    document.querySelector("#metric-passes").textContent = stats.passes_issued;
  } catch {
    // Keep the dashboard tidy when the API is unavailable; the form reports request errors inline.
  }
}

loadAnalytics();
