const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const auditBox = document.getElementById("audit-box");
const auditContent = document.getElementById("audit-content");

let awaitingConfirmation = false;

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.innerHTML = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function addConfirmButton() {
  const div = document.createElement("div");
  div.className = "msg agent";
  const btn = document.createElement("button");
  btn.textContent = "✅ Confirm & Book";
  btn.className = "confirm";
  btn.onclick = confirmBooking;
  div.appendChild(btn);
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function confirmBooking() {
  addMessage("Confirmed, please book it.", "user");
  const res = await fetch("/api/confirm", { method: "POST" });
  const data = await res.json();
  addMessage(data.reply, "agent");
  awaitingConfirmation = false;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user");
  input.value = "";

  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  addMessage(data.reply, "agent");

  if (data.audit_trail) {
    auditBox.style.display = "block";
    auditContent.textContent = data.audit_trail.join("\n");
  }

  if (data.awaiting_confirmation) {
    addConfirmButton();
  }
});
