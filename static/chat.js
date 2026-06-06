const chatBox = document.getElementById("chat-box");
const typingIndicator = document.getElementById("typing");
const msgInput = document.getElementById("msg");

let isWaitingForBot = false;

function setMode(mode, btnElement) {
    if (!btnElement) return;
    
    fetch("/set_mode", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ mode })
    }).catch(err => console.error("Error setting mode profile:", err));

    document.querySelectorAll(".categories button").forEach(btn => btn.classList.remove("active"));
    btnElement.classList.add("active");
}

function formatRoleplayText(text) {
    if (!text) return "";
    return text.replace(/\*(.*?)\*/g, '<em class="roleplay-action">*$1*</em>');
}

function scrollToBottom() {
    setTimeout(() => {
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: 'smooth'
        });
    }, 50);
}

function addMessage(text, sender = "bot") {
    const messageContainer = document.createElement("div");
    messageContainer.classList.add("message", sender, "fade-in-bubble");

    const textBubble = document.createElement("div");
    textBubble.classList.add("bubble");
    textBubble.innerHTML = formatRoleplayText(text);

    if (sender === "bot") {
        const profileAvatar = document.createElement("img");
        profileAvatar.classList.add("avatar");
        profileAvatar.src = "/static/" + CHARACTER_IMAGE;
        profileAvatar.onload = scrollToBottom;
        messageContainer.appendChild(profileAvatar);
    }

    messageContainer.appendChild(textBubble);
    chatBox.appendChild(messageContainer);
    scrollToBottom();
}

function toggleTypingState(show) {
    isWaitingForBot = show;
    if (show) {
        typingIndicator.style.display = "flex";
        msgInput.setAttribute("disabled", "true");
        msgInput.placeholder = `${CHARACTER} is thinking...`;
        scrollToBottom();
    } else {
        typingIndicator.style.display = "none";
        msgInput.removeAttribute("disabled");
        msgInput.placeholder = "Type a message...";
        msgInput.focus();
    }
}

async function loadFirstMessage() {
    toggleTypingState(true);
    try {
        const response = await fetch("/first_message", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ character: CHARACTER })
        });
        const data = await response.json();
        toggleTypingState(false);
        addMessage(data.reply, "bot");
    } catch (err) {
        toggleTypingState(false);
        addMessage("Connection stalled. Let's restart our talk...", "bot");
    }
}

async function sendMsg() {
    if (isWaitingForBot) return;
    
    const currentMessageText = msgInput.value.trim();
    if (!currentMessageText) return;

    addMessage(currentMessageText, "me");
    msgInput.value = "";
    toggleTypingState(true);

    try {
        const response = await fetch("/chat_api", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: currentMessageText,
                character: CHARACTER
            })
        });
        const data = await response.json();
        toggleTypingState(false);
        addMessage(data.reply, "bot");
    } catch (error) {
        toggleTypingState(false);
        addMessage("*Frowns slightly, looking confused.* I lost our connection chain for a second. Can you resend that?", "bot");
    }
}

msgInput.addEventListener("keypress", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMsg();
    }
});

window.onload = loadFirstMessage;
