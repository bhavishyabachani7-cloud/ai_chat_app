// Inside sendMsg async function, replace the fetch block:
const response = await fetch("/chat_stream", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ message: currentMessageText, character: CHARACTER })
});

if (!response.ok) {
    textBubble.innerHTML = "*sighs* Something went wrong...";
    return;
}

const reader = response.body.getReader();
const decoder = new TextDecoder();
let globalResponseText = "";

while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

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
