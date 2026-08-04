#include "commands.h"
#include <Arduino.h>

struct Motor {
  int driverPort;
  int pwmPort;
};

long startTime = millis();

void motorCommand(Motor motor, int value) {
  // Turn off
  if (value == 0) {
    digitalWrite(motor.driverPort, LOW);
    analogWrite(motor.pwmPort, 0);
    return;
  }
  // Negative flip motor direction
  if (value < 0) {
    digitalWrite(motor.driverPort, LOW);
    value = value * -1;
  } else {
    digitalWrite(motor.driverPort, HIGH);
  }
  analogWrite(motor.pwmPort, value);
  return;
}

const int FRONT_LEFT_DRIVER_PORT = 23;
const int FRONT_LEFT_PWM_PORT = 11;

const int FRONT_RIGHT_DRIVER_PORT = 22;
const int FRONT_RIGHT_PWM_PORT = 10;

const int BACK_LEFT_DRIVER_PORT = 24;
const int BACK_LEFT_PWM_PORT = 12;

const int BACK_RIGHT_DRIVER_PORT = 25;
const int BACK_RIGHT_PWM_PORT = 13;

Motor frontLeftMotor = {FRONT_LEFT_DRIVER_PORT, FRONT_LEFT_PWM_PORT};
Motor frontRightMotor = {FRONT_RIGHT_DRIVER_PORT, FRONT_RIGHT_PWM_PORT};
Motor backLeftMotor = {BACK_LEFT_DRIVER_PORT, BACK_LEFT_PWM_PORT};
Motor backRightMotor = {BACK_RIGHT_DRIVER_PORT, BACK_RIGHT_PWM_PORT};

void setup() {
  startTime = millis();
  Serial.begin(115200);

  pinMode(FRONT_LEFT_DRIVER_PORT, OUTPUT);
  pinMode(FRONT_LEFT_PWM_PORT, OUTPUT);

  pinMode(FRONT_RIGHT_DRIVER_PORT, OUTPUT);
  pinMode(FRONT_RIGHT_PWM_PORT, OUTPUT);

  pinMode(BACK_LEFT_DRIVER_PORT, OUTPUT);
  pinMode(BACK_LEFT_PWM_PORT, OUTPUT);

  pinMode(BACK_RIGHT_DRIVER_PORT, OUTPUT);
  pinMode(BACK_RIGHT_PWM_PORT, OUTPUT);

  motorCommand(frontLeftMotor, 0);
  motorCommand(frontRightMotor, 0);
  motorCommand(backRightMotor, 0);
  motorCommand(backLeftMotor, 0);
}

Motor getMotor(int id) {
  if (id == FrontLeftDrive) {
    return frontLeftMotor;
  }
  if (id == FrontRightDrive) {
    return frontRightMotor;
  }
  if (id == BackRightDrive) {
    return backRightMotor;
  }
  if (id == BackLeftDrive) {
    return backLeftMotor;
  }
  // No motor found oh noooo
  return {-1, -1};
}

void stop() {
  motorCommand(frontLeftMotor, 0);
  motorCommand(frontRightMotor, 0);
  motorCommand(backRightMotor, 0);
  motorCommand(backLeftMotor, 0);
}


const long STOP_TIMEOUT = 1500; // Stop after 1.5 seconds of no commands

void loop() {
  long elapsed = millis() - startTime;
  if (elapsed > STOP_TIMEOUT) {
    stop();
  }
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    Command cmd = parseCommand(message.c_str());
    if (cmd.id == Stop) {
      stop();
      return;
    }

    startTime = millis();
    if (cmd.id == Ping){
        return;
    }

    char type = deviceToType(cmd.id);
    if (type == MOTOR_TYPE) {
      Motor motor = getMotor(cmd.id);
      motorCommand(motor, cmd.value);
    }
  }
}
