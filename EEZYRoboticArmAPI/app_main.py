from time import sleep
from flask import Flask, request, render_template
from flask_restful import Resource, Api
from stepper_motion_api import StepperMotionAPI

app = Flask(__name__)
api = Api(app)

stepperApi = StepperMotionAPI

#default web page
@app.route('/')
def index():
    return render_template('/index.html')

#API requests mapping
api.add_resource(stepperApi, '/api/stepper')
                        
if __name__ == '__main__':
    app.run(debug=True, port=5050, host='192.168.1.69',threaded=True)
