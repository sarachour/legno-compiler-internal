"""
This example produces networks that can remember a fixed-length sequence of bits. It is
intentionally very (overly?) simplistic just to show the usage of the NEAT library. However,
if you come up with a more interesting or impressive example, please submit a pull request!

This example also demonstrates the use of a custom activation function.
"""

from __future__ import division, print_function

import math
import os
import random
import neat
import visualize
import util
import anomaly
import json

DATAGEN = anomaly.NoiseRNNAnomaly(15,20)
def test_network(winner_net):
    datagen = DATAGEN
    num_correct = 0
    for test_no,(seq,clazz) in enumerate(datagen.generate_dataset()):
        winner_net.reset()
        error = 0
        for s in seq:
            output = winner_net.activate([s])
            error += datagen.error(clazz, output[0])

        avg_error = error/len(seq)
        threshold = 0.15
        print("TRIAL=%d CLASS=%d SCORE=%f" % (test_no,clazz,avg_error))
        num_correct += 1 if avg_error < threshold else 0

    print("{0} of {1} correct {2:.2f}%".format(num_correct,  \
                                               datagen.num_tests, \
                                               num_correct/datagen.num_tests))



def eval_genome(genome,config):
    net = neat.nn.RecurrentNetwork.create(genome, config)
    datagen = DATAGEN
    error = 0.0
    for seq,clazz in datagen.generate_dataset():
        net.reset()
        for s in seq:
            output = net.activate([s])
            error += datagen.error(clazz,output[0]) ** 2

    size = datagen.n*datagen.num_tests
    return 4.0 - 4.0 * (error / size)


def eval_genomes(genomes,config):
    datagen = DATAGEN
    for genome_id, genome in genomes:
        genome.fitness = eval_genome(genome,config)


def run():
    # Determine path to configuration file.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

    # Demonstration of saving a configuration back to a text file.
    config.save('test_save_config.txt')

    #activation_function = util.ActivationFunction.SINC
    activation_function = util.ActivationFunction.SINC
    def activation(x):
        return activation_function.to_python_func()(x)

    # Demonstration of how to add your own custom activation function.
    # This sinc function will be available if my_sinc_function is included in the
    # config file activation_options option under the DefaultGenome section.
    config.genome_config.add_activation('activation_func', \
                                        activation_function.to_python_func())

    pop = neat.Population(config)
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.StdOutReporter(True))

    generations = 1000
    #generations = 1000
    if 1:
        pe = neat.ParallelEvaluator(4, eval_genome)
        winner = pop.run(pe.evaluate, generations)
    else:
        winner = pop.run(eval_genomes, generations)


    # Log statistics.
    stats.save()

    # Show output of the most fit genome against a random input.
    print('\nBest genome:\n{!s}'.format(winner))
    print('\nOutput:')
    winner_net = neat.nn.RecurrentNetwork.create(winner, config)
    test_network(winner_net)

    node_names = {-1: 'input', -2: 'gate', 0: 'output'}
    visualize.draw_net(config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=False, view=False)

    obj = util.to_system(winner_net,activation_function)
    with open('model.json','w') as fh:
        st = json.dumps(obj,indent=4)
        fh.write(st)

if __name__ == '__main__':
    run()
