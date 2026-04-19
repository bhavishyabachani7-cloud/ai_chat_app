const chatBox = document.getElementById("chat-box");
const typing = document.getElementById("typing");

// ---------------- MODE ---------------- //
function setMode(mode, btn) {

  fetch("/set_mode", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({mode})
  });

  document.querySelectorAll(".categories button")
    .forEach(b => b.classList.remove("active"));

  btn.classList.add("active");
}

// ---------------- MESSAGE UI ---------------- //
function addMessage(text, sender = "bot") {
  const div = document.createElement("div");
  div.classList.add("message", sender);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.innerText = text;

  const avatar = document.createElement("img");
  avatar.classList.add("avatar");

  // ✅ FIXED AVATAR SYSTEM
  if (sender === "bot") {
    avatar.src = "/static/" + CHARACTER_IMAGE;
  } else {
    avatar.src = "/static/user.png";
  }

  if (sender === "bot") {
    div.appendChild(avatar);
    div.appendChild(bubble);
  } else {
    div.appendChild(bubble);
  }

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ---------------- FIRST MESSAGE ---------------- //
async function loadFirstMessage() {

  typing.style.display = "block";

  const res = await fetch("/first_message", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({character: CHARACTER})
  });

  const data = await res.json();

  typing.style.display = "none";
  addMessage(data.reply, "bot");
}

// ---------------- SEND MESSAGE ---------------- //
async function sendMsg() {
  const input = document.getElementById("msg");
  const text = input.value.trim();

  if (!text) return;

  addMessage(text, "me");
  input.value = "";

  typing.style.display = "block";

  const res = await fetch("/chat_api", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      message: text,
      character: CHARACTER
    })
  });

  const data = await res.json();

  typing.style.display = "none";
  addMessage(data.reply, "bot");
}

// ENTER KEY
document.getElementById("msg").addEventListener("keypress", e => {
  if (e.key === "Enter") sendMsg();
});

// AUTO START
window.onload = loadFirstMessage;
