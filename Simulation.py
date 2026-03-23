import pygame
from World import *
import neat
from pathlib import Path

#Main class for running the simulation
class Simulation:
    def __init__(self, width, height, numPredators=10, numPrey=20, mode="red_queen", fileName = ""):
        self.width = width
        self.height = height
        self.numPredators = numPredators
        self.numPrey = numPrey
        self.drawDebug = True
        self.fileName = fileName

        #Pygame is used for visuals
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Predator vs Prey Simulation")
        self.clock = pygame.time.Clock()


        # Resolve to the folder this file lives in
        BASE_DIR = Path(__file__).resolve().parent

        predator_cfg = BASE_DIR / "config" / "predator_neat.config"
        prey_cfg      = BASE_DIR / "config" / "prey_neat.config"

        # Load NEAT configurations
        self.predatorConfig = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            str(predator_cfg)   # neat.Config wants a string
        )

        self.preyConfig = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            str(prey_cfg)
        )

        # World setup
        self.world = World(self.width, self.height, self.predatorConfig, self.preyConfig, mode, self.fileName)
        self.world.initialize(self.numPredators, self.numPrey)

        self.running = True


    #Entry function for main loop
    def run(self):
        self.running = True
        frame = 0

        while self.running:
            self.__handleEvents()
            #0.016s is for 60fps. Delta time was used to keep everything grounded when creating data
            #Time steps probably make more sense, but at the time, I wasnt expecting the sim to run so poorly
            dt = 0.016

            if not self.world.update(dt, self.drawDebug):
                self.running = False

            self.world.draw(self.screen)
            pygame.display.flip()

        self.world.complexityGraph.save()
        self.world.populationGraph.save()
        self.world.PredatorFitnessGraph.save()

    #Handle pygame events such as quitting
    def __handleEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                #Save all graphs upon exit
                self.world.populationGraph.save()
                self.world.complexityGraph.save()
                self.world.PredatorFitnessGraph.save()
                self.running = False
            elif event.type == pygame.KEYDOWN:
                #Emable debug mode - draw rays
                if event.key == pygame.K_SPACE:
                    self.drawDebug = not self.drawDebug
