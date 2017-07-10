import random
import signal
import argparse
import docker
import sys
from datetime import datetime
from time import sleep
from docker.types.services import Resources


def run(args):
    try:
        d = docker.from_env()
        pairs = args.pairs

        nodes = args.node_names

        network = args.network

        for i in range(0, pairs):
            node1 = random.choice(nodes)
            node2 = random.choice(nodes)
            create_test(d, i, 'b', 'a', node1, network)
            sleep(1)
            create_test(d, i, 'a', 'b', node2, network)
        test_a_services = [s for s in d.services.list() if s.name.startswith('test_a')]
        test_b_services = [s for s in d.services.list() if s.name.startswith('test_b')]
        while True:
            sleep(in_args.quiet_time)
            print('Moving services around')
            pause_services(test_a_services, network)
            sleep(10)
            move_services(test_b_services, nodes, network)
            sleep(5)
            move_services(test_a_services, nodes, network)
    except Exception as e:
        clean_up()
        raise e


def move_services(services, nodes, network):
    for s in services:
        s.reload()
        node = random.choice(nodes)
        print('Moved ' + s.name + ' to ' + node)
        update_test(s, network, node)


def pause_services(services, network):
    for s in services:
        s.reload()
        print('Pausing node ' + s.name)
        update_test(s, network, replicas=0)


def create_test(d, i, test, receiver, node_name, network):
    test_kwargs = {
        'name': 'test_' + test + '_' + str(i),
        'image': 'nossnevs/docker_test_' + test + ':latest',
        'env': {'RECEIVER': 'test_' + receiver + '_' + str(i)},
        'resources': Resources(mem_limit=512 * 1000 * 1000, mem_reservation=100 * 1000 * 1000),
        'networks': [network],
        'mode': {'Replicated': {'Replicas': 1}},
        'constraints': ['node.hostname==' + node_name]
    }
    print('Creating service test_' + test + str(i))
    d.services.create(**test_kwargs)


def update_test(s, network, node_name=None, replicas=1,):
    sname_parts = s.name.split('_')
    test = sname_parts[1]
    nr = sname_parts[2]
    receiver = 'test_a_' + nr
    if test == 'a':
        receiver = 'test_b_' + nr

    test_kwargs = {
        'name': s.name,
        'resources': Resources(mem_limit=512 * 1000 * 1000, mem_reservation=100 * 1000 * 1000),
        'env': {'RECEIVER': receiver, 'date': datetime.now()},
        'networks': [network],
        'mode': {'Replicated': {'Replicas': replicas}},
    }

    if node_name:
        test_kwargs['constraints'] = ['node.hostname==' + node_name]

    s.update(**test_kwargs)


def clean_up():
    d = docker.from_env()
    test_services = [s for s in d.services.list() if s.name.startswith('test_')]
    print('Start cleaning upp ' + str(len(test_services)) + ' services')
    for s in test_services:
        print('Removing ' + s.name)
        s.remove()


def handler():
    sleep(2)
    clean_up()
    sleep(5)
    sys.exit(0)


if __name__ == '__main__':
    # Set the signal handler and a 5-second alarm
    signal.signal(signal.SIGINT, handler)
    parser = argparse.ArgumentParser(
        description='This script trying to reproduce the bug in https://github.com/moby/moby/issues/32195'
    )
    parser.add_argument('pairs', metavar='pairs', type=int, help='Number of test pairs')
    parser.add_argument('quiet_time', metavar='quiet_time', type=int, help='The time between moving services')
    parser.add_argument('network', metavar='network', help='The network to be used.')
    parser.add_argument('node_names', metavar='node_name', nargs='+', help='The nodes to be used in the test')
    in_args = parser.parse_args()
    run(in_args)
