import stepper_motion

class MotorActions:
    
    def replay_steps(stepsList:list):
        for step in stepsList:
            if(step.step_name == "up"):
                print("step pressed UP, value: ", step.value)
                stepper_motion.move_up(step.value)
                
            elif(step.step_name == "down"):
                print("step pressed DOWN, value: ", step.value)
                stepper_motion.move_down(step.value)
        
            elif(step.step_name == "right"):
                print("step pressed RIGHT, value: ", step.value)
                stepper_motion.move_backwards(step.value)
            
            elif(step.step_name == "left"):
                print("step pressed LEFT, value: ", step.value)
                stepper_motion.move_forward(step.value)
                
            elif(step.step_name == "base_clockwise"):
                print("step pressed BASE_CLOCKWISE, value: ", step.value)
                stepper_motion.rotate_base_clockwise(step.value)
                
            elif(step.step_name == "base_counter"):
                print("step pressed BASE_COUNTER, value: ", step.value)
                stepper_motion.rotate_base_counter_clockwise(step.value)
                
            elif(step.step_name == "claw"):
                print("claw ", step.value)
                stepper_motion.setAngle(step.value)