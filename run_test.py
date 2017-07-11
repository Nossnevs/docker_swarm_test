import random
import signal
import argparse
import docker
import sys
from datetime import datetime
from time import sleep

from docker.types.services import Resources


class DockerTest:

    def __init__(self, args):
        self.d = docker.from_env()
        self.pairs = args.pairs
        self.nodes = args.node_names
        self.quiet_time = args.quiet_time
        self.network = args.network

    def run(self):
        try:
            for i in range(0, self.pairs):
                node1 = random.choice(self.nodes)
                node2 = random.choice(self.nodes)
                self.__create_test(i, 'b', 'a', node1)
                sleep(1)
                self.__create_test(i, 'a', 'b', node2)
            server_list = self.d.services.list()
            test_a_services = [s for s in server_list if s.name.startswith('test_a')]
            test_b_services = [s for s in server_list if s.name.startswith('test_b')]
            while True:
                sleep(self.quiet_time)
                print('Moving services around')
                self.__pause_services(test_a_services)
                sleep(10)
                self.__move_services(test_b_services)
                sleep(5)
                self.__move_services(test_a_services)
        except Exception as e:
            clean_up()
            raise e

    def __move_services(self, services):
        for s in services:
            s.reload()
            node = random.choice(self.nodes)
            print('Moved ' + s.name + ' to ' + node)
            self.__update_test(s, node)

    def __pause_services(self, services):
        for s in services:
            s.reload()
            print('Pausing node ' + s.name)
            self.__update_test(s, replicas=0)

    def __create_test(self, i, test, receiver, node_name):
        test_kwargs = {
            'name': 'test_' + test + '_' + str(i),
            'image': 'nossnevs/docker_test_' + test + ':latest',
            'env': {'RECEIVER': 'test_' + receiver + '_' + str(i)},
            'resources': Resources(mem_limit=512 * 1000 * 1000, mem_reservation=100 * 1000 * 1000),
            'networks': [self.network],
            'mode': {'Replicated': {'Replicas': 1}},
            'constraints': ['node.hostname==' + node_name]
        }
        print('Creating service test_' + test + str(i))
        self.d.services.create(**test_kwargs)

    def __update_test(self, s, node_name=None, replicas=1):
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
            'networks': [self.network],
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


def handler(signum, frame):
    sleep(2)
    clean_up()
    sleep(5)
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler)
    parser = argparse.ArgumentParser(
        description='This script trying to reproduce the bug in https://github.com/moby/moby/issues/32195'
    )
    parser.add_argument('pairs', metavar='pairs', type=int, help='Number of test pairs')
    parser.add_argument('quiet_time', metavar='quiet_time', type=int, help='The time between moving services')
    parser.add_argument('network', metavar='network', help='The network to be used.')
    parser.add_argument('node_names', metavar='node_name', nargs='+', help='The nodes to be used in the test')
    parsed_args = parser.parse_args()
    docker_test = DockerTest(parsed_args)
    docker_test.run()
