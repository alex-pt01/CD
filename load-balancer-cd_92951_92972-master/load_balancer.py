# coding: utf-8

import socket
import select
import signal
import logging
import argparse
import time

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Load Balancer')


# used to stop the infinity loop
done = False


# implements a graceful shutdown
def graceful_shutdown(signalNumber, frame):  
    logger.debug('Graceful Shutdown...')
    global done
    done = True


# n to 1 policy
class N2One: # 5 (17)
    def __init__(self, servers):
        print("\nN2One initialized")
        for server in servers:
            print(server)
        self.servers = servers  

    def select_server(self):
        print("\nRequested a new server")
        return self.servers[0]

    def update(self, *arg):
        pass


# round robin policy
class RoundRobin: # 20 (5)
    def __init__(self, servers):
        self.servers = servers
        self.indice= -1

    def select_server(self):
        self.indice=  self.indice + 1 #incremento de 1
        if self.indice == len(self.servers): #volta ao inicio
            self.indice=0
        
        return self.servers[self.indice]

    def update(self, *arg):
        pass


# least connections policy
class LeastConnections: # 20 (5) a considerar número de conexões total
    def __init__(self, servers):
        print("\nLeastConnections initialized")
        self.servers = servers
        self.connections = {} # Dictionary with pairs (socket, counter)
        for server in servers:
            self.connections[server] = 0

    def select_server(self):
        # Find the server with least connections and return it
        print("\nRequested a new server")
        min = 99999
        server = None
        for s, c in self.connections.items():
            if c<min:
                server = s
                min = c
        self.connections[server] += 1
        return server

    def update(self, *arg):
        pass

class LeastActiveConnections:
    def __init__(self, servers):
        print("\nLeastConnections initialized")
        self.servers = servers
        self.connections = {} # Dictionary with pairs (socket, counter)
       
        for server in servers:
            self.connections[server] = 0

    def select_server(self):
        # Find the server with least connections and return it
        print("\nRequested a new server")
        server = min(self.connections, key=self.connections.get)
        self.connections[server] += 1
        return server

    def update(self, *arg):
        self.connections[args['server']] -= 1
        
# least response time
class LeastResponseTime:
    def __init__(self, servers):
        print("\nLeastResponseTime initialized")
        self.servers = servers

    def select_server(self):
        print("\nRequested a new server")
        print(f"Current time (in seconds) is {time.time()}")
        return self.servers[0]

    def update(self, *arg):
        pass


class SocketMapper:
    def __init__(self, policy):
        self.policy = policy
        self.map = {}

    def add(self, client_sock, upstream_server):
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect(upstream_server)
        logger.debug("Proxying to %s %s", *upstream_server)
        self.map[client_sock] =  upstream_sock
       
        self.connections[client_sock] =()



    def delete(self, sock):
        try:
            self.map.pop(sock)
            sock.close() 
        except KeyError:
            pass

    def get_sock(self, sock):
        for c, u in self.map.items():
            if u == sock:
                return c
            if c == sock:
                return u
        return None
    
    def get_upstream_sock(self, sock):
        for c, u in self.map.items():
            if c == sock:
                return u
        return None

    def get_all_socks(self):
        """ Flatten all sockets into a list"""
        return list(sum(self.map.items(), ())) 


def main(addr, servers):
    # register handler for interruption 
    # it stops the infinite loop gracefully
    signal.signal(signal.SIGINT, graceful_shutdown)

    policy = LeastConnections(servers)
    mapper = SocketMapper(policy)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.setblocking(False)
        sock.bind(addr)
        sock.listen()
        logger.debug("Listening on %s %s", *addr)
        while not done:
            readable, writable, exceptional = select.select([sock]+mapper.get_all_socks(), [], [], 1)
            if readable is not None:
                for s in readable:
                    if s == sock:
                        client, addr = sock.accept()
                        logger.debug("Accepted connection %s %s", *addr)
                        client.setblocking(False)
                        mapper.add(client, policy.select_server())
                    if mapper.get_sock(s):
                        print()
                        logger.debug("%s | Before receiving data", s.getpeername())
                        data = s.recv(4096)
                        logger.debug("%s | Received data", s.getpeername())
                        if len(data) == 0: # No messages in socket, we can close down the socket
                            mapper.delete(s)
                            # Pedido terminou (chamar update)
                        else:
                            logger.debug("%s | Sending", s.getpeername())
                            mapper.get_sock(s).send(data)
                            logger.debug("%s | Sent", s.getpeername())
    except Exception as err:
        logger.error(err)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pi HTTP server')
    parser.add_argument('-p', dest='port', type=int, help='load balancer port', default=8080)
    parser.add_argument('-s', dest='servers', nargs='+', type=int, help='list of servers ports')
    args = parser.parse_args()
    
    servers = []
    for p in args.servers:
        servers.append(('localhost', p))
    
    main(('127.0.0.1', args.port), servers)
