#from dataclasses import dataclass

class MotorStep:
    def __init__(self, step_name : str, value : int):
        self.step_name = step_name
        self.value = value