var send_command = function (msg) {
    if (websocket.readyState == WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: "command",
            value: msg
        }));
    }
};

var command_mode = function(enabled) {
    if (websocket.readyState == WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: "command-mode",
            value: enabled ? 'true' : 'false'
        }));
    }
};

var send_slider_data = function () {
    var audio = parseInt(document.getElementById("audio").value);
    var lights = parseInt(document.getElementById("lights").value);

    if (websocket.readyState == WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: "audio-volume",
            value: audio
        }));

        websocket.send(JSON.stringify({
            type: "light-intensity",
            value: 800 - lights
        }));
    }
};

document.getElementById("enter").onclick = function() {send_command("enter")};
document.getElementById("exit").onclick = function() {send_command("exit")};
document.getElementById("wake").onclick = function() {send_command("wake")};
document.getElementById("sleep").onclick = function() {send_command("sleep")};
document.getElementById("start-talking").onclick = function() {send_command("start-talking")};
document.getElementById("stop-talking").onclick = function() {send_command("stop-talking")};
document.getElementById("reset").onclick = function() {send_command("reset")};
document.getElementById("wave-gesture").onclick = function() {send_command("wave-gesture")};
document.getElementById("stop-gesture").onclick = function() {send_command("stop-gesture")};
// document.getElementById("fish-init").onclick = fish_init
document.getElementById("happy").onclick = function() {fish.happy()};
document.getElementById("sad").onclick = function() {fish.sad()};
document.getElementById("start").onclick = function() {command_mode(true)};
document.getElementById("stop").onclick = function() {command_mode(false)};

var slider_interval;
document.getElementById("enable").onclick = function() {
    slider_interval = setInterval(send_slider_data, 100);
};
document.getElementById("disable").onclick = function() {
    clearInterval(slider_interval);
};
