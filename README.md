# EEZYRoboticArmAPI

3D printed robotic arm that uses stepper motors and it's connected to a raspberry pi 4 that sends the steps/instructions.</br>

**Youtube video:** </br>
[![](http://img.youtube.com/vi/6QX1YFKg4C8/0.jpg)](http://www.youtube.com/watch?v=6QX1YFKg4C8 "Robotic Arm")

## Raspberry pi project API

Endpoints:

### /api/stepper

This endpoint has the query params **move** and **value** that specifies the robotic arm direction and steps

**move = up & value =** //add steps number </br>
**move = down & value =** //add steps number </br>
**move = forward & value =** //add steps number </br>
**move = backward & value =** //add steps number </br>
**move = base_right & value =** //add steps number </br>
**move = base_left & value =** //add steps number </br></br>
Response:
```
{
  “movement”: “up”,
  “status”: 200
}
```

The steps above are only for the robotic arm movement.
For the claw we have different query params

**move = claw & angle** = //add any number between 1 and 9 
</br></br>
Response:
```
{
  “movement”: “claw movement”,
  “status”: 200
}
```

**Each query action is memorised so that we can replay it**
For this I had to implement a other actions

**move = clear_steps** - This query removes/clears all actions that were made until that point
</br></br>
Response:
```
{
  “data”: 0,
  “movement”: “clear_steps”,
  “status”: 200
}
```
**move = saved_steps** - This query displays the steps number (how many actions are memorised until that point)
</br></br>
Response:
```
{
  “data”: 65,
  “movement”: “saved_steps”,
  “status”: 200
}
```
**move = replay_steps** - Once this query is called it will replay all the steps that were memorised
</br></br>
Response:
```
{
  “data”: 65,
  “movement”: “replay_steps”,
  “status”: 200
}
```
</br>

### Hardware connection between Raspberry PI and ULN2003 Driver Board

Raspberry pi | ULN2003 Driver Board (1) Up/ Down
------------ | -------------
GPIO21 | IN1
GPIO20 | IN2
GPIO16 | IN3
GPIO12 | IN4
GND | GND
5V | 5V

</br>

Raspberry pi | ULN2003 Driver Board (2) - Forward / Backward
------------ | -------------
GPIO26 | IN1
GPIO19 | IN2
GPIO13 | IN3
GPIO06 | IN4
GND | GND
5V | 5V

</br>

Raspberry pi | ULN2003 Driver Board (3) - Base left/right
------------ | -------------
GPIO05 | IN1
GPIO22 | IN2
GPIO27 | IN3
GPIO18 | IN4
GND | GND
5V | 5V

</br></br>
    Copyright 2019

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

