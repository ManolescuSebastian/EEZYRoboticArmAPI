# EEZYRoboticArmAPI

3D printed robotic arm that uses stepper motors and it's connected to a raspbarry pi 4 that sends the steps/instructions.

[![](http://img.youtube.com/vi/6QX1YFKg4C8/0.jpg)](http://www.youtube.com/watch?v=6QX1YFKg4C8 "Robotic Arm")

Endpoints:

### /api/stepper

This endpoint has the query params **move** and **value** that specifies the robotic arm direction and steps

move = up & value = //add steps number
move = down & value = //add steps number
move = forward & value = //add steps number
move = backward & value = //add steps number
move = base_right & value = //add steps number
move = base_left & value = //add steps number

```
{
  “movement”: “up”,
  “status”: 200
}
```

The steps above are only for the robotic arm movement.
For the claw we have different query params

move = claw & angle = //add any number between 1 and 9 


**Each query action is memorised so that we can replay it**
For this I had to implement a other actions

**move = clear_steps** - This query removes/clears all actions that were made until that point
```
{
  “data”: 0,
  “movement”: “clear_steps”,
  “status”: 200
}
```
**move = saved_steps** - This query displays the steps number (how many actions are memorised until that point)
```
{
  “data”: 65,
  “movement”: “saved_steps”,
  “status”: 200
}
```
**move = replay_steps** - Once this query is called it will replay all the steps that were memorised
```
{
  “data”: 65,
  “movement”: “replay_steps”,
  “status”: 200
}
```

