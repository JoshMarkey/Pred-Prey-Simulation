from Predator import *
from Prey import *
import random
import copy
from concurrent.futures import ThreadPoolExecutor
from EnviromentManager import *
from LiveGraph import *

#Controller for the world
#Contains all the agents
class World:
    def __init__(self, width, height, predatorConfig, preyConfig, mode, fileName):
        self.fileName = fileName
        self.width = width
        self.height = height
        self.predators = []
        self.prey = []
        self.predatorConfig = predatorConfig
        self.preyConfig = preyConfig
        self.nextPreyId = 1000
        self.nextPredatorId = 1000
        self.maxPreds = 250
        self.maxPrey = 250
        self.environmentManager = EnvironmentManager(mode=mode)
        self.timeCounter = 0

        #Lots of data gathering. Each graph needs to be defined and have lines added
        #This graph class was very helpful, although can slightly clutter the constructor
        self.populationGraph = LiveGraph("Population Count", xlabel="Time (seconds)", ylabel="Population", fileName=fileName)
        self.populationGraph.add_line("Prey", colour="green")
        self.populationGraph.add_line("Pred", colour="red")

        self.complexityGraph = LiveGraph(title="Agent Network Complexity", xlabel="Time", ylabel="Avg Complexity",fileName=fileName)
        self.complexityGraph.add_line("Predator Complexity", colour='red')
        self.complexityGraph.add_line("Prey Complexity", colour='green')

        # Add rolling derivative lines
        self.complexityGraph.add_rolling_derivative("Prey Complexity", "Prey Complexity Delta", window=10)
        self.complexityGraph.add_rolling_derivative("Predator Complexity", "Pred Complexity Delta", window=10, linestyle="--")

        self.PredatorFitnessGraph = LiveGraph(title="Predator Fitness", xlabel="Time", ylabel="Avg Fitness",fileName=fileName)
        self.PredatorFitnessGraph.add_rolling_average_line("Predator Fitness", colour='red')

        self.timeElapsed = 0
        self.lastPredPop = 0
        self.lastPreyPop = 0

    def initialize(self, numPredators, numPrey):
        # Predator population
        p_genomes = [self._create_genome(self.predatorConfig) for _ in range(numPredators)]
        for genome in p_genomes:
            net = neat.nn.FeedForwardNetwork.create(genome, self.predatorConfig)
            pos = (random.randint(0, self.width), random.randint(0, self.height))
            self.predators.append(Predator(pos, genome, net, self.predatorConfig, (self.width, self.height)))

        # Prey population
        prey_genomes = [self._create_genome(self.preyConfig) for _ in range(numPrey)]
        for genome in prey_genomes:
            net = neat.nn.FeedForwardNetwork.create(genome, self.preyConfig)
            pos = (random.randint(0, self.width), random.randint(0, self.height))
            self.prey.append(Prey(pos, genome, net, self.preyConfig, (self.width, self.height)))

        #Render the graphs on frame 0
        #They will be empty, but allows me to position the 3 windows for viewing
        #self.updateGraphs(True)

    #Create a new genome with random ID
    def _create_genome(self, config):
        gid = random.randint(1, 1_000_000)
        genome = neat.DefaultGenome(gid)
        genome.configure_new(config.genome_config)
        genome.fitness = 0.0
        return genome
    
    def calculate_avg_complexity(self, agent_list):
        if not agent_list:
            return 0
        total = 0
        for agent in agent_list:
            if agent.genome:
                nodes = len(agent.genome.nodes)
                connections = len(agent.genome.connections)
                total += nodes + connections
        return total / len(agent_list)

    #Update once per time step
    #Handles updating the agents, collisions and NEAT
    #Utalises multithreading. Set to 13 threads-my machine has a maximum of 16
    def update(self, dt, debugInfo):
        self.drawDebug = debugInfo
        newPredators = []
        newPrey = []
        self.timeElapsed += dt

        self.environmentManager.update(dt, self)

        ###################################################################################
        #   max_workers=x to change number of threads used
        ###################################################################################

        with ThreadPoolExecutor(max_workers=1) as executor:
            #Prey update
            prey_results = list(executor.map(lambda prey: prey.update(self.predators, dt), self.prey))
            newPrey = [self.createPreyFromParent(prey) for prey, reproduced in zip(self.prey, prey_results)
                    if reproduced and len(self.prey) < self.maxPrey]

            #Predator update
            pred_results = list(executor.map(lambda p: p.update(self.prey, dt), self.predators))
            newPredators = [self.createPredatorFromParent(pred) for pred, reproduced in zip(self.predators, pred_results)
                            if reproduced and len(self.predators) < self.maxPreds]

        #Update agent lists (after threading is complete)
        self.prey.extend(newPrey)
        self.predators = [p for p in self.predators if p.isAlive]
        self.predators.extend(newPredators)

        #Remove eaten prey
        self.prey = [prey for prey in self.prey if not prey.isEaten]

        

        if len(self.predators) == 0 or len(self.prey) == 0:
            return False
        
        #self.updateGraphs()
        return True



    def updateGraphs(self, updated = False):
        self.PredatorFitnessGraph.update()


        #Only update graphs if there is a change - saves on memory
        if len(self.prey) != self.lastPreyPop:
            self.lastPreyPop = len(self.prey)
            self.populationGraph.push("Prey", self.timeElapsed, self.lastPreyPop)
            prey_complexity = self.calculate_avg_complexity(self.prey)
            self.complexityGraph.push("Prey Complexity", self.timeElapsed, prey_complexity)
            updated = True

        if len(self.predators) != self.lastPredPop:
            self.lastPredPop = len(self.predators)
            self.populationGraph.push("Pred", self.timeElapsed, self.lastPredPop)
            pred_complexity = self.calculate_avg_complexity(self.predators)
            self.complexityGraph.push("Predator Complexity", self.timeElapsed, pred_complexity)
            
            updated = True

        if updated:
            self.populationGraph.update()
            self.complexityGraph.update()

    #Asexual reproduction for prey
    def createPreyFromParent(self, parent):
        genome = copy.deepcopy(parent.genome)
        genome.key = self.nextPreyId
        self.nextPreyId += 1
        genome.fitness = 0
        genome.mutate(parent.config.genome_config)
        net = neat.nn.FeedForwardNetwork.create(genome, parent.config)

        parent.reproduceCooldown = 5 + random.uniform(0, 5)

        return Prey(position=parent.position, net=net, genome=genome, config=parent.config, windowSize=(self.width, self.height))
    
    #Asexual reproduction for predators
    def createPredatorFromParent(self, parent):
        genome = copy.deepcopy(parent.genome)
        self.PredatorFitnessGraph.push_rolling("Predator Fitness", self.timeElapsed, genome.fitness)
        genome.key = self.nextPredatorId
        self.nextPredatorId += 1


        genome.mutate(parent.config.genome_config)
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, parent.config)

        return Predator(position=parent.position, net=net, genome=genome, config=parent.config, windowSize=(self.width, self.height))

    def draw(self, screen):
        screen.fill((30, 30, 30))  #Dark background

        #Draw entities
        for prey in self.prey:
            prey.draw(screen)
        for predator in self.predators:
            predator.draw(screen)

        #Draw rays if in debug mode
        if self.drawDebug:
            for i, prey in enumerate(self.prey):
                if i > 10:
                    break
                prey.drawRays(screen, self.predators)

            for i, pred in enumerate(self.predators):
                if i > 10:
                    break
                pred.drawRays(screen, self.prey)

        #Draw text
        font = pygame.font.SysFont(None, 24)
        text_surface = font.render(f'Prey: {len(self.prey)}  |  Predators: {len(self.predators)}', True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))

    