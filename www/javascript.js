//
// 
//

var messageContainer = document.getElementById("messages");

function WebSocketTest() {
    var messageContainer = document.getElementById("messages");
    if ("WebSocket" in window) {
        messageContainer.innerHTML = "WebSocket is supported by your Browser!";
        var ws = new WebSocket("ws://localhost:8888/ws?Id=123456789");

        ws.onopen = function() {
            ws.send("Message to send");
        };

        ws.onmessage = actOnData;

        ws.onclose = function() { 
            messageContainer.innerHTML = "Connection is closed...";
        };

    } else {
        messageContainer.innerHTML = "WebSocket NOT supported by your Browser!";
    }
}

function actOnData(evt) {
    var received_msg = evt.data;
    var messageContainer = document.getElementById("messages");
    var world = JSON.parse(received_msg); 

    messageContainer.innerHTML = received_msg;

    var sonarWidth = document.getElementById("sonars").style.width 
    document.getElementById("sonar1").style.width = (100*(world.sonar[0]/300)).toString()+"%";
    document.getElementById("sonar2").style.width = (100*(world.sonar[1]/300)).toString()+"%";
    document.getElementById("sonar3").style.width = (100*(world.sonar[2]/300)).toString()+"%";
    document.getElementById("sonar4").style.width = (100*(world.sonar[3]/300)).toString()+"%";

    if (world.bump[0])  { document.getElementById("lbump").style.backgroundColor = "red"; }
                  else  { document.getElementById("lbump").style.backgroundColor = "green"; }
    if (world.bump[1])  { document.getElementById("rbump").style.backgroundColor = "red"; }
                   else { document.getElementById("rbump").style.backgroundColor = "green"; }
    if (world.cliff[0]) { document.getElementById("lcliff").style.backgroundColor = "red"; }
                   else { document.getElementById("lcliff").style.backgroundColor = "green"; }
    if (world.cliff[1]) { document.getElementById("rcliff").style.backgroundColor = "red"; }
                   else { document.getElementById("rcliff").style.backgroundColor = "green"; }
    
    irCamera(world.camera);

};

function irCamera(ir) { // ir = [ [x,y,w],null,null,null ] 
    var icanvas = document.getElementById("ircamera");
    var width = icanvas.width;
    var height = icanvas.height;

    var icontext = icanvas.getContext("2d");
    icontext.strokeStyle = "white";
    icontext.fillStyle = "red";
    
    icontext.clearRect(0, 0, width, height);
    icontext.beginPath();
    for (var i=0; i<4; i++) {
        if (ir[i]) {
            var x = (ir[i][0]/1024)*width;
            var y = (ir[i][1]/768)*height;
            var w = ir[i][2];
            console.log(i);
            icontext.strokeRect(x-2*w,y-2*w, 2*2*w,2*2*w);
//            icontext.lineWidth = 2;
//            icontext.moveTo(x,0);
//            icontext.drawTo(x,height);
//            icontext.moveTo(0,y);
//            icontext.drawTo(width,y);
            }
        }
//    icontext.stroke();
    };

function getMousePos(canvas, e) {
    var rect = canvas.getBoundingClientRect();
    return { x: e.clientX-rect.left, y: e.clientY-rect.top};
    }

function joyMouseDown(e) {
    var pos = getMousePos(joyCanvas, e);

    joyDraw();
    joyContext.strokeStyle = "white";
    joyContext.fillStyle = "red";
    joyContext.beginPath();
    joyContext.arc(pos.x, pos.y, 10, 0.0, Math.PI*2);
    joyContext.fill();
    console.log('you clicked');
    }

function joyDraw() {
    var x = joyCanvas.width;
    var y = joyCanvas.height;
    var w = 40;

    joyContext.strokeStyle = "white";
    joyContext.fillStyle = "blue";
    joyContext.moveTo(x/2, y/2);    
    joyContext.arc(x/2, y/2, 100, 0.0, Math.PI*2);
    joyContext.strokeRect(x/2-2*w,y/2-2*w, 2*2*w,2*2*w);
    console.log('draw joystick');
    }

var joyCanvas = document.getElementById("joystick");
var joyContext = joyCanvas.getContext("2d");

joyDraw();
joyCanvas.addEventListener('mousedown', joyMouseDown);



