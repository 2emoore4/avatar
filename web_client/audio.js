// set up websocket connection to python server
var connection_active = false;
var websocket = new WebSocket("ws://localhost:8080");

var server_update_frequency = 100;

// set flag upon successful connection
websocket.onopen = function() {
    connection_active = true;
};

// read from volume data and send useful stats to server
var update_server = function () {
    if (connection_active) {
        // send most recently recorded volume
        websocket.send(JSON.stringify({
            type: "audio-volume",
            value: timespectrum[timespectrum.length - 1]
        }));
    }
};

// set up speech recognition
var recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = "en";

recognition.onresult = function (event) {
    for (var i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
            document.getElementById("text").innerText += " " + event.results[i][0].transcript;
        }
    }
};

document.getElementById("start_speech").onclick = function() {
    recognition.start();
};

document.getElementById("stop_speech").onclick = function() {
    recognition.stop();
};

// error callback for getUserMedia function
var errorlog = function(e) {
    console.log("Rejected.", e);
};

window.AudioContext = window.AudioContext ||
                      window.webkitAudioContext;

var context = new AudioContext();

navigator.getUserMedia = navigator.getUserMedia ||
                         navigator.webkitGetUserMedia ||
                         navigator.mozGetUserMedia ||
                         navigator.msGetUserMedia;

// set up input node, analyser node, frequency array, AND STARTS INTERVAL TIMER
var input, filter, analyser, audio_interval, analysis_interval, freqdomain;
navigator.getUserMedia({audio: true}, function(stream) {
    input = context.createMediaStreamSource(stream);
    filter = context.createBiquadFilter();
    analyser = context.createAnalyser();
    analyser.smoothingTimeConstant = 0.3;
    analyser.fftSize = 1024;
    input.connect(filter);
    filter.connect(analyser);

    freqdomain = new Float32Array(analyser.frequencyBinCount);
}, errorlog);

document.getElementById("start_audio").onclick = function() {
    audio_interval = setInterval(update, 10);
    analysis_interval = setInterval(analysetimedomain, 1000.0 / server_update_frequency);
};

document.getElementById("stop_audio").onclick = function() {
    clearInterval(audio_interval);
    clearInterval(analysis_interval);
};

// using fft output, calculate 'volume' of audio
var getvolume = function(freqs) {
    var sum = 0;

    for (i = 0; i < freqs.length; i++) {
        sum += freqs[i];
    }

    return sum / freqs.length;
};

// populate array with 0's
var timespectrum = Array.apply(null, new Array(200)).map(Number.prototype.valueOf, -160);
// shift oldest volume out of array, push new volume to end of array
var doarraystuff = function() {
    analyser.getFloatFrequencyData(freqdomain);
    var volume = getvolume(freqdomain);

    timespectrum.shift();
    timespectrum.push(volume);
};

// calculates important stats from volume array
var max, min, avg, peaks;
var analysetimedomain = function() {
    var sum = 0;
    min = Number.MAX_VALUE;
    max = -Number.MAX_VALUE;
    peaks = 0;

    for (i = 0; i < timespectrum.length; i++) {
        sum += timespectrum[i];

        if (timespectrum[i] < min) {
            min = timespectrum[i];
        }

        if (timespectrum[i] > max) {
            max = timespectrum[i];
        }
    }

    avg = sum / timespectrum.length;

    for (i = 0; i < timespectrum.length; i++) {
        if (timespectrum[i] > (max - min) * 0.9 + min) {
            peaks++;
        }
    }

    document.getElementById("avg").innerText = avg;
    document.getElementById("max").innerText = max;
    document.getElementById("min").innerText = min;
    document.getElementById("peaks").innerText = peaks;

    update_server();
};

// linear interpolation
var lerp = function(input, inrange0, inrange1, outrange0, outrange1) {
    return outrange0 + (outrange1 - outrange0) * ((input - inrange0) / (inrange1 - inrange0));
};

// canvas drawing happens here
var canvas = document.getElementById("canvas").getContext("2d");
var update = function() {
    doarraystuff();

    canvas.clearRect(0, 0, 1512, 130);
    canvas.fillStyle = "#000000";

    for (i = 0; i < 200; i++) {
        var rect = lerp(timespectrum[i], min, max, 0, -130);
        canvas.fillRect(i * 5, 130, 4, rect);
    }

    for (i = 0; i < 512; i++) {
        var rect = -freqdomain[i] - 70;
        canvas.fillRect(1000 + i, rect, 1, 1);
    }
};
