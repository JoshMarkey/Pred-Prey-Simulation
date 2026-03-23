import random

class EnvironmentManager:
    def __init__(self, mode='red_queen'):
        self.mode = mode
        self.timer = 0
        self.nextShock = 20  # seconds until next disruption

    #Update to be called inside the main loop
    def update(self, dt, world):
        if self.mode != 'court_jester':
            return  # Do nothing unless this is Court Jester mode
        

        self.timer += dt
        if self.timer > self.nextShock:
            self.timer = 0
            self.nextShock = 30
            self.applyShock(world)
        
    #Apply all the instability factors
    def applyShock(self, world):
        print("[Court Jester] Environmental disruption applied!")
        for predator in world.predators:
            if random.uniform(0,1) > 0.5:
                predator.energy -= 1000
            else:
                predator.rayLength = predator.baseRayLength * 0.5
                predator.rayRecoveryTimer = 0

        for prey in world.prey:
            if random.uniform(0,1) > 0.5:
                prey.isEaten = True
            else:
                prey.rayLength = prey.baseRayLength * 0.5
                prey.rayRecoveryTimer = 0
