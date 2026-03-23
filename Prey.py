import math
import pygame
import neat
import random
from Entity import *

class Prey(Entity):
    def __init__(self, position, genome, net, config, windowSize):
        super().__init__(position, radius=8, windowSize=windowSize)

        self.color = (0, 255, 0)
        self.genome = genome
        self.config = config
        self.net = net

        self.maxSpeed = 75
        #Speed was never implimented - could be added in the future as another output
        self.speed = 0

        self.timeAlive = 0
        self.lastReproduceTime = 0
        self.reproduceCooldown = random.uniform(5, 10)

        self.isEaten = False
        self.max_turn_rate = 4

        self.baseRayLength = 200
        self.rayLength = self.baseRayLength
        self.rayRecoveryTimer = 0
        self.rayCount = 36

    #Sense function will gather all inputs for ANN
    #Runs all the ray collisions
    def sense(self, predators):
        rays = []

        #nearby_preds = get_nearby_entities(predators, self.position, cell_size)

        for i in range(self.rayCount):
            angle = self.angle + i * (2 * math.pi / self.rayCount)
            dx = math.cos(angle)
            dy = math.sin(angle)

            closest_hit = self.rayLength
            ray_origin = self.position

            for pred in predators:
                cx, cy = pred.position
                ox, oy = ray_origin
                fx = dx
                fy = dy

                # Vector from origin to circle center
                dx_c = cx - ox
                dy_c = cy - oy

                # Project vector onto ray direction
                t = dx_c * fx + dy_c * fy
                if t < 0:
                    continue  # Behind ray

                closest_point_x = ox + fx * t
                closest_point_y = oy + fy * t

                dist_to_center = math.hypot(cx - closest_point_x, cy - closest_point_y)
                if dist_to_center < self.radius:
                    hit_dist = math.hypot(closest_point_x - ox, closest_point_y - oy)
                    if hit_dist < closest_hit:
                        closest_hit = hit_dist

            rays.append(closest_hit / self.rayLength)

        return rays
    

    #Update function to be called every timestep
    #Controls feedforward net, movement
    #Return true if able to reproduce
    def update(self, predators, dt, predator_grid=None):
        if self.genome:
            self.genome.fitness += dt

        self.timeAlive += dt

        if self.rayLength < self.baseRayLength:
            self.rayRecoveryTimer += dt
            if self.rayRecoveryTimer >= 5.0:  # Wait 5 seconds, then restore
                self.rayLength = self.baseRayLength
                self.rayRecoveryTimer = 0

        inputs = self.sense(predators)  # fallback if not using grid

        if self.net:
            output = self.net.activate(inputs)
            turn = (output[0] - 0.5) * self.max_turn_rate  # output in [-0.5, 0.5] scaled
            self.angle += turn * dt
            self.speed = 1 * self.maxSpeed

        self.move(dt)

        if self.timeAlive - self.lastReproduceTime >= self.reproduceCooldown:
            self.lastReproduceTime = self.timeAlive
            return True  # reproduced

        return False
    
    #Draw rays if in debug mode
    def drawRays(self, screen, predators):
        for i in range(self.rayCount):
            angle = self.angle + i * (2 * math.pi / self.rayCount)
            dx = math.cos(angle)
            dy = math.sin(angle)
            ray_dir = (dx, dy)

            hit = None
            for pred in predators:
                hit_ratio = self.rayCircleIntersect(
                    self.position,
                    ray_dir,
                    pred.position,
                    pred.radius,
                    self.rayLength
                )
                if hit_ratio is not None:
                    distance = hit_ratio * self.rayLength
                    hit_x = self.position[0] + ray_dir[0] * distance
                    hit_y = self.position[1] + ray_dir[1] * distance
                    hit = (hit_x, hit_y)
                    break

            if hit:
                pygame.draw.line(screen, (255, 0, 0), self.position, hit, 1)
            else:
                end_x = self.position[0] + ray_dir[0] * self.rayLength
                end_y = self.position[1] + ray_dir[1] * self.rayLength
                pygame.draw.line(screen, (100, 100, 255), self.position, (end_x, end_y), 1)



    

