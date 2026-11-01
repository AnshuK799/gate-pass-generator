const API_BASE = window.VISITOR_API_BASE || "http://localhost:8000";
const emailForm = document.querySelector("#email-form");
const visitorForm = document.querySelector("#visitor-form");
const successPanel = document.querySelector("#success-panel");
const notice = document.querySelector("#notice");
const progress = document.querySelector("#progress-fill");
const title = document.querySelector("#form-title");
const step = document.querySelector("#step-label");
let verifiedEmail = "";

document.querySelector("#year").textContent = new Date().getFullYear();

function setPage(pageName) {
  const page = document.querySelector(`[data-page-section="${pageName}"]`);
  if (!page) return;
  document.querySelectorAll("[data-page-section]").forEach(section => {
    const active = section === page;
    section.hidden = !active;
    section.classList.toggle("active", active);
  });
  document.querySelectorAll(".nav-link").forEach(link => {
    const active = link.dataset.page === pageName;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelector("#main-nav").classList.remove("open");
  document.querySelector("#menu-toggle").setAttribute("aria-expanded", "false");
  document.querySelector("#menu-toggle").setAttribute("aria-label", "Open navigation");
  history.replaceState(null, "", `#${pageName}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

const startingPage = window.location.hash.slice(1);
setPage(["home", "about", "developer"].includes(startingPage) ? startingPage : "home");

document.querySelectorAll("[data-page], [data-page-link]").forEach(control => {
  control.addEventListener("click", event => {
    const pageName = control.dataset.page || control.dataset.pageLink;
    if (pageName) {
      event.preventDefault();
      setPage(pageName);
    }
    if (control.hasAttribute("data-scroll-checkin")) {
      window.setTimeout(() => document.querySelector("#checkin").scrollIntoView({ behavior: "smooth", block: "center" }), 80);
    }
  });
});

document.querySelector("#menu-toggle").addEventListener("click", event => {
  const menu = document.querySelector("#main-nav");
  const open = menu.classList.toggle("open");
  event.currentTarget.setAttribute("aria-expanded", String(open));
  event.currentTarget.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
});

function showNotice(message, type = "error") {
  notice.textContent = message;
  notice.className = `notice ${type}`;
  notice.hidden = false;
}

function clearNotice() {
  notice.hidden = true;
  notice.textContent = "";
}

async function post(path, data) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  } catch {
    throw new Error("We couldn’t reach the visitor service. Please try again in a moment.");
  }
  let result = {};
  try { result = await response.json(); } catch { /* handled with a helpful fallback below */ }
  if (!response.ok) throw new Error(result.message || "Something went wrong. Please check your details and try again.");
  return result;
}

function loading(button, busy, label) {
  button.disabled = busy;
  button.querySelector("span:first-child").textContent = busy ? label : button.dataset.label;
}

for (const button of document.querySelectorAll(".primary-button")) button.dataset.label = button.querySelector("span:first-child").textContent;

emailForm.addEventListener("submit", async event => {
  event.preventDefault();
  clearNotice();
  if (!emailForm.reportValidity()) return;
  const email = document.querySelector("#email").value.trim();
  const button = emailForm.querySelector("button");
  loading(button, true, "Sending code…");
  try {
    const result = await post("/generate_otp", { email });
    verifiedEmail = email;
    document.querySelector("#email-display").textContent = email;
    emailForm.hidden = true;
    visitorForm.hidden = false;
    progress.style.width = "100%";
    title.textContent = "A few details for your visit";
    step.innerHTML = "STEP 02 <i>/ 02</i>";
    document.querySelector("#otp").focus();
    showNotice(result.development_otp
      ? `Local development code: ${result.development_otp}. Enter it below to continue.`
      : "Your verification code is on its way. Check your inbox to continue.", "success");
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading(button, false);
  }
});

visitorForm.addEventListener("submit", async event => {
  event.preventDefault();
  clearNotice();
  if (!visitorForm.reportValidity()) return;
  const button = visitorForm.querySelector("button[type=submit]");
  const data = Object.fromEntries(new FormData(visitorForm).entries());
  data.email = verifiedEmail;
  data.name = data.name.trim();
  data.address = data.address.trim();
  data.otp = data.otp.trim();
  loading(button, true, "Completing check-in…");
  try {
    const result = await post("/submit_visitor", data);
    visitorForm.hidden = true;
    document.querySelector(".card-heading").hidden = true;
    document.querySelector(".progress-track").hidden = true;
    successPanel.hidden = false;
    if (result.qr_code) {
      document.querySelector("#qr-image").src = `data:image/svg+xml;base64,${result.qr_code}`;
      document.querySelector("#qr-container").hidden = false;
    }
    if (result.visitor_pass_pdf) {
      const download = document.querySelector("#download-pass");
      const safeName = data.name.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase();
      download.href = `data:application/pdf;base64,${result.visitor_pass_pdf}`;
      download.download = `DYPIU-Visitor-Pass-${safeName || "visitor"}.pdf`;
      download.hidden = false;
    }
  } catch (error) {
    showNotice(error.message);
  } finally {
    loading(button, false);
  }
});

document.querySelector("#back-button").addEventListener("click", () => {
  clearNotice();
  visitorForm.hidden = true;
  emailForm.hidden = false;
  progress.style.width = "50%";
  title.textContent = "Let’s get you checked in";
  step.innerHTML = "STEP 01 <i>/ 02</i>";
  document.querySelector("#email").focus();
});

document.querySelector("#new-visit").addEventListener("click", () => {
  visitorForm.reset();
  emailForm.reset();
  verifiedEmail = "";
  successPanel.hidden = true;
  document.querySelector("#qr-container").hidden = true;
  document.querySelector("#qr-image").removeAttribute("src");
  const download = document.querySelector("#download-pass");
  download.hidden = true;
  download.removeAttribute("href");
  document.querySelector(".card-heading").hidden = false;
  document.querySelector(".progress-track").hidden = false;
  visitorForm.hidden = true;
  emailForm.hidden = false;
  progress.style.width = "50%";
  title.textContent = "Let’s get you checked in";
  step.innerHTML = "STEP 01 <i>/ 02</i>";
  clearNotice();
  window.scrollTo({ top: 0, behavior: "smooth" });
});
