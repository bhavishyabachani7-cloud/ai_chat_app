let idleTimer;
let lastAction = Date.now();

function startIdle(){
    clearTimeout(idleTimer);

    idleTimer = setTimeout(()=>{
        if(Date.now() - lastAction > 14000){
            fetch("/idle/"+character)
            .then(res=>res.json())
            .then(data=>{
                add("bot", data.reply);
            });
        }
    },15000);
}

function send(){
    lastAction = Date.now();
    clearTimeout(idleTimer);

    let input = document.getElementById("msg");
    let msg = input.value.trim();
    let lang = document.getElementById("lang").value;

    if(!msg) return;

    add("me", msg);
    input.value = "";

    document.getElementById("typing").style.display = "block";

    fetch("/chat_api", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            message:msg,
            character:character,
            language:lang
        })
    })
    .then(res=>res.json())
    .then(data=>{
        setTimeout(()=>{
            document.getElementById("typing").style.display="none";
            add("bot", data.reply);
            startIdle();
        },800 + Math.random()*1000);
    });
}

function add(type,text){
    let box=document.getElementById("chat-box");
    let div=document.createElement("div");
    div.className=type;
    div.innerText=text;
    box.appendChild(div);
    box.scrollTop=box.scrollHeight;
}