let character;
let lang = "auto";
let idleTimer;

function addMessage(text,type){
    let box = document.getElementById("chat-box");

    let div = document.createElement("div");
    div.className = "msg " + type;

    if(text.includes("🔒")){
        div.classList.add("lock");
    }

    div.innerText = text;

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function typing(){
    let box = document.getElementById("chat-box");
    let t = document.createElement("div");
    t.id="typing";
    t.className="msg bot";
    t.innerText="typing...";
    box.appendChild(t);
}

function removeTyping(){
    let t=document.getElementById("typing");
    if(t) t.remove();
}

async function send(){
    let input=document.getElementById("msg");
    let text=input.value.trim();
    if(!text) return;

    addMessage(text,"me");
    input.value="";

    typing();

    let res=await fetch("/chat_api",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            message:text,
            character:character,
            language:lang
        })
    });

    let data=await res.json();

    setTimeout(()=>{
        removeTyping();
        addMessage(data.reply,"bot");
        speak(data.reply);

        if(Math.random()>0.7){
            fetch("/image/"+character)
            .then(res=>res.json())
            .then(d=>{
                let img=document.createElement("img");
                img.src=d.img;
                img.style.maxWidth="200px";
                document.getElementById("chat-box").appendChild(img);
            });
        }

        startIdle();
    },800+Math.random()*1000);
}

function startIdle(){
    clearTimeout(idleTimer);
    idleTimer=setTimeout(async()=>{
        let res=await fetch("/idle/"+character);
        let data=await res.json();
        addMessage(data.reply,"bot");
    },15000);
}

function startVoice(){
    let rec=new webkitSpeechRecognition();
    rec.lang="en-IN";
    rec.onresult=function(e){
        document.getElementById("msg").value=e.results[0][0].transcript;
    };
    rec.start();
}

function speak(text){
    let speech=new SpeechSynthesisUtterance(text);
    speech.rate=1;
    speech.pitch=1.2;
    speechSynthesis.speak(speech);
}

window.onload=()=>{
    character=document.body.dataset.name;

    setTimeout(()=>{
        addMessage("Hey… you came back 😏","bot");
    },800);

    startIdle();
};
