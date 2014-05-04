var websocket = null;
var uid = -1;

document.getElementById("connect").onclick = function() {
    init_socket();
};

function init_socket() {
    websocket = new WebSocket("ws://localhost:8080");

    websocket.onmessage = function(message) {
        m_obj = JSON.parse(message["data"]);

        if (m_obj["type"] == "assign_uid") {
            uid = m_obj["data"];
        }

        console.log(message);
    };

    websocket.onopen = function() {
        websocket.send(JSON.stringify({
            type: "request",
            message: "userid",
            uid: uid
        }));
    };
}

