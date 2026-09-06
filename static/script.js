const startBtn = document.getElementById("start-btn");
const intro = document.getElementById("intro");
const appEl = document.getElementById("app");

startBtn.addEventListener("click", () => {
  intro.style.display = "none";
  appEl.style.display = "block";
});

const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const auditBox = document.getElementById("audit-box");
const auditContent = document.getElementById("audit-content");

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `msg ${sender}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function addLabCard(card) {
  const wrap = document.createElement("div");
  wrap.className = "lab-card";
  wrap.innerHTML = `
    <div class="lab-top">
      <div>
        <div class="lab-name">${card.name}</div>
        <div class="lab-area">${card.area} · ⭐ ${card.rating}</div>
      </div>
      <div class="lab-price">₹${card.price}</div>
    </div>
    <div class="lab-tests">${card.tests.join(", ")}</div>
    ${card.fallback_used ? '<div class="lab-note">Cheapest lab had no slots today — picked the next best option.</div>' : ""}
  `;
  const btn = document.createElement("button");
  btn.textContent = "Confirm & book";
  btn.className = "confirm";
  btn.onclick = confirmBooking;
  wrap.appendChild(btn);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

async function confirmBooking() {
  addMessage("Confirmed, please book it.", "user");
  const res = await fetch("/api/confirm", { method: "POST" });
  const data = await res.json();
  addMessage(data.reply, "agent");
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

  if (data.lab_card) {
    addLabCard(data.lab_card);
  } else {
    addMessage(data.reply, "agent");
  }

  if (data.audit_trail) {
    auditBox.style.display = "block";
    auditContent.textContent = data.audit_trail.join("\n");
  }
});
