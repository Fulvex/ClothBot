const A_BUTTON = 0;
const B_BUTTON = 1;
const X_BUTTON = 2;
const Y_BUTTON = 3;
const LEFT_BUMPER = 4;
const RIGHT_BUMPER = 5;
const LEFT_TRIGGER = 6;
const RIGHT_TRIGGER = 7;
const DEAD_ZONE = 0.12;
const JOYSTICK_CHANGE_THRESHOLD = 0.02;

var leftX = 0;
var leftY = 0;
var rightX = 0;
var leftBumper = 0;
var rightBumper = 0;
var leftTrigger = 0;
var rightTrigger = 0;
var xButton = 0;
var yButton = 0;
var aButton = 0;
var bButton = 0;
var prevLeftX = 0;
var prevLeftY = 0;
var prevRightX = 0;
var prevLeftBumper = 0;
var prevRightBumper = 0;
var prevLeftTrigger = 0;
var prevRightTrigger = 0;
var prevXButton = 0;
var prevYButton = 0;
var prevAButton = 0;
var prevBButton = 0;

const socket = io();
function sendCommand(action, val) {
    socket.emit('robot_command', { command: action, val: val });
}

let connectedGamepadIndex = null;

var webController = false;

window.addEventListener("gamepadconnected", (event) => {
  console.log("Gamepad connected:", event.gamepad.id);
  connectedGamepadIndex = event.gamepad.index;
  startGameLoop();
});

window.addEventListener("gamepaddisconnected", (event) => {
  console.log("Gamepad disconnected");
  connectedGamepadIndex = null;
});

function startGameLoop() {
  if (connectedGamepadIndex === null) return;
  if (!webController) {
    document.getElementById('webControllerStatus').innerText = 'Disconnected';
    document.getElementById('webControllerStatus').style.color = 'red';
    return;
  }
  document.getElementById('webControllerStatus').innerText = 'Connected';
  document.getElementById('webControllerStatus').style.color = 'lime';


  // 1. Get the latest snapshot of all connected gamepads
  const gamepads = navigator.getGamepads();
  const gp = gamepads[connectedGamepadIndex];

  if (gp) {
    // 2. Read the inputs
    handleButtons(gp.buttons);
    handleAxes(gp.axes);
  }

  // 3. Continue the loop on the next animation frame
  requestAnimationFrame(startGameLoop);
}

function handleButtons(buttons) {
  prevXButton = xButton;
  xButton = buttons[X_BUTTON].value;
  if (xButton && !prevXButton) {
    sendCommand('STOP', 0)
  }
  // Analog triggers show pressure from 0.0 to 1.0
  const rightTriggerValue = buttons[RIGHT_TRIGGER].value;
}

function handleAxes(axes) {
  prevLeftX = leftX;
  prevLeftY = leftY;
  prevRightX = rightX;

  leftX = axes[0];
  leftY = axes[1];
  rightX = axes[2];

  if (Math.abs(leftX) < DEAD_ZONE) leftX = 0;
  if (Math.abs(leftY) < DEAD_ZONE) leftY = 0;
  if (Math.abs(rightX) < DEAD_ZONE) rightX = 0;

  let deltaX = leftX - prevLeftX;
  let deltaY = leftY - prevLeftY;
  let deltaRightX = rightX - prevRightX;

  if (Math.abs(deltaX) < JOYSTICK_CHANGE_THRESHOLD) deltaX = 0;
  if (Math.abs(deltaY) < JOYSTICK_CHANGE_THRESHOLD) deltaY = 0;
  if (Math.abs(deltaRightX) < JOYSTICK_CHANGE_THRESHOLD) deltaRightX = 0;

  if (deltaX !== 0 || deltaY !== 0 || deltaRightX !== 0) {
    sendCommand('GAMEPAD',String(leftX) + "," + String(-leftY) + "," + String(rightX))
  }
}


socket.on('connect', function() {
    document.getElementById('status').innerText = 'Connected';
    document.getElementById('status').style.color = 'lime';
});

socket.on('disconnect', function() {
    document.getElementById('status').innerText = 'Disconnected';
    document.getElementById('status').style.color = 'red';
});


socket.on('video_frame', function(data) {
    document.getElementById('videoStream').src = 'data:image/jpeg;base64,' + data.image;
});

const telemetryDiv = document.getElementById("telemetry");
const telemetryElements = {};

socket.on('telemetry_update', function(data) {
    for (const [label, value] of Object.entries(data)) {
        if (!telemetryElements[label]) {
            const p = document.createElement("p");

            const strong = document.createElement("strong");
            strong.textContent = label + ": ";

            const span = document.createElement("span");

            p.appendChild(strong);
            p.appendChild(span);

            telemetryDiv.appendChild(p);

            telemetryElements[label] = span;
        }
        if (label == "Controller Mode") {
          webController = value == "WEB_CONTROLLER";
        }
        telemetryElements[label].textContent = value;
    }
});
