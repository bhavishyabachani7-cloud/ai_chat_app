// ---------------- ELEMENTS ----------------
const box = document.getElementById("chat-box");
const input = document.getElementById("msg");
const typing = document.getElementById("typing");

// ---------------- ADD MESSAGE ----------------
function addMessage(text, sender) {

    const div = document.createElement("div");
    div.className = "message " + sender;

    // BOT AVATAR
    if (sender === "bot") {
        const img = document.createElement("img");
        img.src = document.querySelector(".chat-header img").src;
        img.className = "avatar";
        div.appendChild(img);
    }

    // MESSAGE BUBBLE
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerText = text;

    div.appendChild(bubble);
    box.appendChild(div);

    // AUTO SCROLL
    box.scrollTop = box.scrollHeight;
}

// ---------------- SEND MESSAGE ----------------
function sendMsg() {

    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "me");
    input.value = "";

    showTyping();

    fetch("/chat_api", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            message: msg,
            character: CHARACTER
        })
    })
    .then(res => res.json())
    .then(data => {

        const delay = Math.min(1500, msg.length * 40);

        setTimeout(() => {
            hideTyping();
            addMessage(data.reply, "bot");
        }, delay);

    })
    .catch(() => {
        hideTyping();
        addMessage("Something went wrong 😅", "bot");
    });
}

// ---------------- ENTER KEY ----------------
input.addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendMsg();
    }
});

// ---------------- TYPING CONTROL ----------------
function showTyping() {
    typing.style.display = "block";
    box.scrollTop = box.scrollHeight;
}

function hideTyping() {
    typing.style.display = "none";
}

// ---------------- CATEGORY SYSTEM ----------------
function setMode(mode, el) {

    fetch("/set_mode", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({mode: mode})
    });

    document.querySelectorAll(".categories button")
        .forEach(btn => btn.classList.remove("active"));

    if (el) el.classList.add("active");
}

// ---------------- AUTO FIRST MESSAGE ----------------
window.onload = function () {

    showTyping();

    fetch("/chat_api", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            message: "start",
            character: CHARACTER
        })
    })
    .then(res => res.json())
    .then(data => {

        setTimeout(() => {
            hideTyping();
            addMessage(data.reply, "bot");
        }, 800);

    })
    .catch(() => {
        hideTyping();
        addMessage("Hey… looks like something broke 😅", "bot");
    });
};
