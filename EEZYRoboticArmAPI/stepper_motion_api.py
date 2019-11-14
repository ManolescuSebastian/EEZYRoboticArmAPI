import stepper_motion
from motor_actions import MotorActions

from flask import json
from flask import jsonify
from flask import Flask, request, render_template
from flask_restful import Resource, Api
from flask import Response
from motor_step import MotorStep
from typing import List

class StepperMotionAPI(Resource):
    
    stepsList = []  
    
    def __init__(self):
        stepper_motion.init_default_states()
       
    def get(self):
        arg = request.args['move']
        if(arg == "up"):
            value_param = request.args.get('value')
            stepper_motion.move_up(int(value_param))
            
            item = MotorStep(arg,int(value_param))
            self.stepsList.append(item)
            
            return jsonify(
                status = 200,
                movement = 'up')
            return response
        elif(arg == "down"):
            value_param : int = request.args.get('value')
            stepper_motion.move_down(int(value_param))
            
            item = MotorStep(arg,int(value_param))
            self.stepsList.append(item)
            
            return jsonify(
                status = 200,
                movement = 'down')
        elif(arg == "left"):
            value_param = request.args.get('value')
            stepper_motion.move_forward(int(value_param))
            
            item = MotorStep(arg,int(value_param))
            self.stepsList.append(item)
            
            return jsonify(
                status = 200,
                movement = 'forward')
        elif(arg == "right"):
            value_param = request.args.get('value')
            stepper_motion.move_backwards(int(value_param))
            
            item = MotorStep(arg,int(value_param))
            self.stepsList.append(item)

            return jsonify(
                status = 200,
                movement = 'backward')
        elif(arg == "base_clockwise"):
            value_param = request.args.get('value')
            stepper_motion.rotate_base_clockwise(int(value_param))
            
            item = MotorStep(arg,int(value_param))
            self.stepsList.append(item)
            
            return jsonify(
                status = 200,
                movement = 'base_right')
        elif(arg == "base_counter"):
            value_param = request.args.get('value')
            stepper_motion.rotate_base_counter_clockwise(int(value_param))
             
            item = MotorStep(arg,int(value_param))
            self.stepsList.append(item)
            
            return jsonify(
                status = 200,
                movement = 'base_left')
        elif(arg == "claw"):
            angleValue = request.args.get('angle')
            print ('Angle value: ' + request.args.get('angle'))
            stepper_motion.setAngle(angleValue)
            
            item = MotorStep(arg,int(angleValue))
            self.stepsList.append(item)
            
            return jsonify(
                status = 200,
                movement = 'claw movement')
        elif(arg == 'stop'):
            stepper_motion.stopMovement()
            return jsonify(
                status = 200,
                movement = 'stop')
        elif(arg == "saved_steps"):
            return jsonify(
                status = 200,
                data = len(self.stepsList),
                movement = 'saved_steps')
        elif(arg == "clear_steps"):
            self.stepsList.clear()
            return jsonify(
                status = 200,
                data = len(self.stepsList),
                movement = 'clear_steps')
        elif(arg == "replay_steps"):
            MotorActions.replay_steps(self.stepsList)
            return jsonify(
                status = 200,
                data = len(self.stepsList),
                movement = 'replay_steps')
        else:
            return jsonify(
                status = 400,
                movement = 'Error')

