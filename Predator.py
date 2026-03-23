from Entity import *

class Predator(Entity):
    def __init__(self, position, genome, net, config, windowSize):
        super().__init__(position, radius=9, windowSize=windowSize)

        self.color = (255, 0, 0)
        self.genome = genome
        self.config = config
        self.net = net

        self.maxSpeed = 60
        self.speed = 0
        self.energy = 60
        self.timeSinceLastReproduction = 0
        self.isAlive = True

        self.maxTurnRate = 4

        self.baseRayLength = 200
        self.rayLength = self.baseRayLength
        self.rayCount = 9
        self.rayRecoveryTimer = 0

    #Update function to be called every time step
    #Controls feedforward, movement, collision
    def update(self, preyList, dt):
        self.timeSinceLastReproduction += dt
        self.energy -= dt * 6  # Energy drain

        if self.energy <= 0:
            self.isAlive = False
            return False

        self.genome.fitness += dt  # Survival bonus


        if self.rayLength < self.baseRayLength:
            self.rayRecoveryTimer += dt
            if self.rayRecoveryTimer >= 5.0:  # Wait 5 seconds, then restore
                self.rayLength = self.baseRayLength
                self.rayRecoveryTimer = 0

        inputs = self.sense(preyList)

        if self.net:
            output = self.net.activate(inputs)
            turn = (output[0] - 0.5) * self.maxTurnRate  # output in [-0.5, 0.5] scaled
            self.speed = 1 * self.maxSpeed
            self.angle += turn * dt

        self.move(dt)

        #Check to see if currently colliding with prey
        for prey in preyList:
            if prey.isEaten:
                continue
            if self.collidesWith(prey):
                prey.isEaten = True
                self.energy = min(100, self.energy + 50)
                prey.alive = False

        #Reproduce if energy is high enough and cooldown over
        if self.can_reproduce():
            self.energy -= 40
            self.timeSinceLastReproduction = 0.0
            return True

        return False
    
    #Circle to circle collision for predator->prey
    def collidesWith(self, other):
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (self.radius + other.radius)
    
    #Identical logic to prey, move based on rotation and bounce off walls


    #Trigger all sensors -> rays
    def sense(self, preyList):
        rays = []
        cx, cy = self.position
        fov = math.pi / 2  # 90 degrees field of view
        angle_offset = -fov / 2
        angle_step = fov / (self.rayCount - 1) if self.rayCount > 1 else 0


        for i in range(self.rayCount):
            angle = self.angle + angle_offset + i * angle_step
            dx = math.cos(angle)
            dy = math.sin(angle)

            closest_dist = 1.0  # Default if nothing hit
            for prey in preyList:
                px, py = prey.position
                r = getattr(prey, 'radius', 5)

                fx = px - cx
                fy = py - cy
                t = fx * dx + fy * dy

                if t < 0:
                    continue

                closestX = cx + dx * t
                closestY = cy + dy * t

                dist_sq = (closestX - px)**2 + (closestY - py)**2

                if dist_sq <= r**2:
                    dist_to_circle = t - math.sqrt(r**2 - dist_sq)
                    norm_dist = min(dist_to_circle / self.rayLength, 1.0)
                    closest_dist = min(closest_dist, norm_dist)

            rays.append(closest_dist)

        return rays
    
    #Draw all the rays coming from the predator - this is only done when debug mode is enabled
    def drawRays(self, screen, preyList):
        cx, cy = self.position
        fov = math.pi / 2  # 90 degrees
        angle_offset = -fov / 2
        angle_step = fov / (self.rayCount - 1) if self.rayCount > 1 else 0

        for i in range(self.rayCount):
            angle = self.angle + angle_offset + i * angle_step
            dx = math.cos(angle)
            dy = math.sin(angle)
            direction = (dx, dy)

            closest_dist = self.rayLength
            for prey in preyList:
                result = self.rayCircleIntersect(self.position, direction, prey.position, prey.radius, self.rayLength)
                if result is not None:
                    hit_dist = result * self.rayLength
                    if hit_dist < closest_dist:
                        closest_dist = hit_dist

            end_x = int(cx + dx * closest_dist)
            end_y = int(cy + dy * closest_dist)

            color = (255, 150, 0) if closest_dist < self.rayLength else (150, 255, 150)
            pygame.draw.line(screen, color, (int(cx), int(cy)), (end_x, end_y), 1)

    def can_reproduce(self):
        return self.energy >= 100 and self.timeSinceLastReproduction > 4

    def reproduce(self):
        self.energy /= 2
        self.timeSinceLastReproduction = 0

    def is_dead(self):
        return self.energy <= 0