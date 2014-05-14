var send_command = function (msg) {
    if (websocket.readyState == WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: "command",
            value: msg
        }));
    }
};

document.getElementById("enter").onclick = function() {send_command("enter")};
document.getElementById("exit").onclick = function() {send_command("exit")};
document.getElementById("wake").onclick = function() {send_command("wake")};
document.getElementById("sleep").onclick = function() {send_command("sleep")};
document.getElementById("start-talking").onclick = function() {send_command("start-talking")};
document.getElementById("stop-talking").onclick = function() {send_command("stop-talking")};
