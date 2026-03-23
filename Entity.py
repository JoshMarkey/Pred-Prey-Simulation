import math
import pygame
import neat
import random

class Entity:

    def __init__(self, position, radius, windowSize):
        self.position = position
        self.radius = radius
        self.windowSizeX, self.windowSizeY = windowSize
        #Random starting angle
        self.angle = random.uniform(0, 2 * math.pi)


    def rayCircleIntersect(self, ray_origin, ray_dir, circle_pos, circle_radius, max_distance):
        # Vector from ray origin to circle center
        dx = circle_pos[0] - ray_origin[0]
        dy = circle_pos[1] - ray_origin[1]
        to_circle = (dx, dy)

        # Project to_circle vector onto the ray direction
        proj_length = dx * ray_dir[0] + dy * ray_dir[1]

        if proj_length < 0 or proj_length > max_distance:
            return None  # Outside ray range

        # Closest point on the ray to the circle center
        closest_x = ray_origin[0] + ray_dir[0] * proj_length
        closest_y = ray_origin[1] + ray_dir[1] * proj_length

        # Distance squared from closest point to circle center
        dist_sq = (circle_pos[0] - closest_x) ** 2 + (circle_pos[1] - closest_y) ** 2

        if dist_sq <= circle_radius ** 2:
            return proj_length / max_distance  # Normalised hit distance
        return None
    
    #Movement direction is based from angle
    #Same logic for both species, just different speeds
    def move(self, dt):
        dx = math.cos(self.angle) * self.speed * dt
        dy = math.sin(self.angle) * self.speed * dt
        newX = self.position[0] + dx
        newY = self.position[1] + dy

        bounced = False

        if newX < 0 or newX > self.windowSizeX:
            self.angle = math.pi - self.angle  # Reflect horizontally
            bounced = True
        if newY < 0 or newY > self.windowSizeY:
            self.angle = -self.angle  # Reflect vertically
            bounced = True

        if not bounced:
            self.position = (newX, newY)
    
    #Draw prey with a default circle
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.position[0]), int(self.position[1])), self.radius)