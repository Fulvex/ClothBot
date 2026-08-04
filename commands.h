
#ifndef COMMANDS_H
#define COMMANDS_H

#include "Arduino.h"

struct Command
{
    int id;
    int value;
};


Command parseCommand(const char* input)
{
    Command cmd;
    sscanf(input, "%d,%d",
           &cmd.id,
           &cmd.value);

    return cmd;
}

enum Device {
    Stop = -1,
    Ping = 0,
    FrontLeftDrive = 1,
    FrontRightDrive = 2,
    BackRightDrive = 3,
    BackLeftDrive = 4,
    Shoulder = 5,
    Elbow = 6,
    ClawDiffyRight = 7,
    ClawDiffyLeft = 8,
    Gripper = 9
};

const char MOTOR_TYPE = 'M';
const char STEPPER_TYPE = 'S';

char deviceToType(int id){
    switch(id){
        case FrontLeftDrive:
        case FrontRightDrive:
        case BackRightDrive:
        case BackLeftDrive:
            return MOTOR_TYPE;
        case Shoulder:
        case Elbow:
        case ClawDiffyLeft:
        case ClawDiffyRight:
        case Gripper:
            return STEPPER_TYPE;
        default:
            return 'N';
    }
}

#endif
