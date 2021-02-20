# coding: utf-8

import logging
from DHT_Client import DHT_Client

# configure the log with DEBUG level
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')

def main():
    client = DHT_Client(('localhost', 5000))
    # Node 770

    # add object to DHT (this key is in first node -> local search)
    # Stored at Node 770
    # Normal path: 770
    client.put('1', [0, 1, 2])
    # retrieve from DHT (this key is in first node -> local search)
    print(client.get('1'))

    # add object to DHT (this key is not on the first node -> remote search)
    # Stored at Node 959
    # Normal path: 770 > 959
    client.put('2', ('xpto'))
    # retrieve from DHT (this key is not on the first node -> remote search)
    print(client.get('2'))

    # add object to DHT (this key is not on the first node -> remote search)
    # Stored at node ???
    client.put('3', ('a', 'b', 'c', 'd'))
    # retrieve from DHT (this key is not on the first node -> remote search)
    print(client.get('3'))


if __name__ == '__main__':
    main()
