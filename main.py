from Simulation import *

if __name__ == "__main__":
    #Change mode to court_jester for the random environmental shocks
    sim = Simulation(width=1300, height=1000, numPredators=20, numPrey=100, mode="red_queen", fileName="Test")
    sim.run()
