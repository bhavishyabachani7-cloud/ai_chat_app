const chatBox = document.getElementById("chat-box");
const typingIndicator = document.getElementById("typing");
const msgInput = document.getElementById("msg");

let isWaitingForBot = false;

function setMode(mode, btnElement) {
    if (!btnElement || !CHARACTER) return;
    
    fetch("/set_mode", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ mode: mode, character: CHARACTER })
    }).catch(err => console.error("Mode error:", err));

    document.querySelectorAll(".categories button").forEach(btn => btn.classList.remove("active"));
    btnElement.classList.add("active");
}

function formatRoleplayText(text) {
    if (!text) return "";
    return text.replace(/\*(.*?)\*/g, '<em class="roleplay-action">*$1*</em>');
}

function scrollToBottom() {
    if(chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMsg(initialRun = false) {
    if (isWaitingForBot) return;
    
    let currentMessageText = initialRun ? "start" : msgInput.value.trim();
    if (!currentMessageText && !initialRun) return;

    if (!initialRun) {
        addClientMessage(currentMessageText);
        msgInput.value = "";
    }

    isWaitingForBot = true;
    if(typingIndicator) typingIndicator.style.display = "flex";
    msgInput.setAttribute("disabled", "true");
    msgInput.placeholder = `${CHARACTER} is typing...`;
    scrollToBottom();

    const messageContainer = document.createElement("div");
    messageContainer.classList.add("message", "bot");
    const profileAvatar = document.createElement("img");
    profileAvatar.classList.add("avatar");
    profileAvatar.src = "/static/" + CHARACTER_IMAGE;
    messageContainer.appendChild(profileAvatar);

    const textBubble = document.createElement("div");
    textBubble.classList.add("bubble");
    messageContainer.appendChild(textBubble);
    chatBox.appendChild(messageContainer);

    try {
        const response = await fetch("/chat_stream", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ message: currentMessageText, character: CHARACTER })
        });

        if(typingIndicator) typingIndicator.style.display = "none";

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let globalResponseText = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n");

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    let dataStr = line.slice(6).trim();
                    if (dataStr === "[DONE]") break;
                    if (dataStr.startsWith("{")) {
                        try {
                            const parsed = JSON.parse(dataStr);
                            if (parsed.token) {
                                globalResponseText += parsed.token;
                                textBubble.innerHTML = formatRoleplayText(globalResponseText);
                                scrollToBottom();
                            }
                        } catch(e) {}
                    }
                }
            }
        }
    } catch (error) {
        console.error(error);
        if(typingIndicator) typingIndicator.style.display = "none";
        textBubble.innerHTML = "*Connection issue... try again*";
    }

    isWaitingForBot = false;
    msgInput.removeAttribute("disabled");
    msgInput.placeholder = "Type an action or reply here...";
    msgInput.focus();
    scrollToBottom();
}

function addClientMessage(text) {
    const messageContainer = document.createElement("div");
    messageContainer.classList.add("message", "me");
    const textBubble = document.createElement("div");
    textBubble.classList.add("bubble");
    textBubble.innerHTML = formatRoleplayText(text);
    messageContainer.appendChild(textBubble);
    chatBox.appendChild(messageContainer);
    scrollToBottom();
}

if(msgInput) {
    msgInput.addEventListener("keypress", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMsg(false);
        }
    });
}

window.addEventListener('DOMContentLoaded', () => { 
    sendMsg(true); 
});
