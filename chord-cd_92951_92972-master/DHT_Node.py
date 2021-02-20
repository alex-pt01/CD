# coding: utf-8

import socket
import threading
import logging
import pickle
from utils import dht_hash, contains_predecessor, contains_successor
# <DHT>
from DHT_Index import DHT_Index
# </DHT>


class DHT_Node(threading.Thread):
    """ DHT Node Agent. """
    def __init__(self, address, dht_address=None, timeout=3):
        """ Constructor

        --- Arguments
            address: self's address
            dht_address: address of a node in the DHT
            timeout: impacts how often stabilize algorithm is carried out
        """
        
        print("Initializing...")
        threading.Thread.__init__(self)
        self.id = dht_hash(address.__str__())
        self.addr = address #My address
        self.dht_address = dht_address  #Address of the initial Node

        if dht_address is None:
            self.inside_dht = True
            #I'm my own successor
            self.successor_id = self.id
            self.successor_addr = address
            self.predecessor_id = None
            self.predecessor_addr = None
        else:
            self.inside_dht = False
            self.successor_id = None
            self.successor_addr = None
            self.predecessor_id = None
            self.predecessor_addr = None
        self.keystore = {}  # Where all data is stored
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.logger = logging.getLogger("Node {}".format(self.id))

        # <DHT>
        self.fingerTable = []
        self.fingerTable.append(DHT_Index(self.predecessor_id, self.predecessor_id, self.predecessor_addr))
        for i in range (1,11):
            self.fingerTable.append(DHT_Index(self.id+2**(i-1)))
        self.logger.debug('Initialized fingerTable...')
        for ind in self.fingerTable:
            self.logger.debug('\t%s', ind)
        # </DHT>

    # <DHT>
    def FT_getSuccessor(self, key, answerId=None, answerAddr=None):
        """ Obtains the node's successor
        Knowing that key is stored at node with id>=key

        --- Arguments
        key                     int     The key looking for successor
        answerAddr              
        --- Returns
        nodeid                  int     The id of the sucessor node 
        address                 addres  The successor address
        """
        if key==self.id:
            # If key is the same as self id, self is the key successor
            return self.id, self.addr
        elif self.successor_id and self.predecessor_id:
            if key>self.id and key<=self.successor_id:
                # If key is greater that self id but smaller or equal to sucessor id, self's sucessor is key's successor
                return self.successor_id, self.successor_addr
            elif self.id>self.successor_id and self.id>self.predecessor_id and key>self.id and key<=self.successor_id:
                # Last node before zero
                # If key is greater that self and the node's id is greater than its successor's and predecessor's ids, all the keys greater that node's id must be stored at sucessor
                # This condition means that there is no other node between the node id and zero 
                return self.successor_id, self.successor_addr
            elif self.id<self.successor_id and self.id<self.predecessor_id and key>self.id:
                # First node after zero
                return self.id, self.addr
            elif answerAddr!=None:
                # Forward request to closest preceding nome
                closestPrecidingAddr = None
                closestPrecidingAddr = self.FT_closest_preceding_node(key)
                if closestPrecidingAddr:
                    msg = {'method': 'FTGETSUCESSOR', 'args': {'key':key, 'answerid':answerId, 'answeraddr': answerAddr}}
                    self.send(closestPrecidingAddr, msg)
        return None, None
        
    #function that gets the closest preciding node
    #returns its' id
    def FT_closest_preceding_node(self, key): 
        """ Gets closest preceding node based on FT for a given key

        --- Arguments
        key                 int         The key 
        --- Returns
        address             address     The node's address
        """
        print(f"# Getting closest preciding node for key {key}")
        if not isinstance(key, int):
            key = int(key)
        for f in self.fingerTable[::-1]: #Iterate in reverse order (from greater to smaller id)
            if f!=None and f.nodeid!=None and key>self.id and f.nodeid>self.id and f.nodeid<=key:
                return f.address
            elif f!=None and f.nodeid!=None and key<self.id and f.nodeid<self.id and f.nodeid>=key:
                return f.address
        if key>self.id:
            return self.successor_addr
        return None
    
    # </DHT>

    def send(self, address, msg):
        """ Send msg to address. """
        payload = pickle.dumps(msg)
        print("###Send ", msg, "to", address)
        if address:
            self.socket.sendto(payload, address)

    def recv(self):
        """ Retrieve msg payload and from address."""
        try:
            payload, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None

        if len(payload) == 0:
            return None, addr
        return payload, addr

    def node_join(self, args):
        """ Process JOIN_REQ message.

        Parameters:
            args (dict): addr and id of the node trying to join
        """

        self.logger.debug('Node join: %s', args)
        addr = args['addr']
        identification = args['id']
        if self.id == self.successor_id: #I'm the only node in the DHT
            self.successor_id = identification
            self.successor_addr = addr
            args = {'successor_id': self.id, 'successor_addr': self.addr}
            self.send(addr, {'method': 'JOIN_REP', 'args': args})
        elif contains_successor(self.id, self.successor_id, identification):
            args = {'successor_id': self.successor_id, 'successor_addr': self.successor_addr}
            self.successor_id = identification
            self.successor_addr = addr
            self.send(addr, {'method': 'JOIN_REP', 'args': args})
        else:
            self.logger.debug('Find Successor(%d)', args['id'])
            self.send(self.successor_addr, {'method': 'JOIN_REQ', 'args':args})
        self.logger.info(self)

    def notify(self, args):
        """ Process NOTIFY message.
            Updates predecessor pointers.

        Parameters:
            args (dict): id and addr of the predecessor node
        """

        self.logger.debug('Notify: %s', args)
        if self.predecessor_id is None or contains_predecessor(self.id, self.predecessor_id, args['predecessor_id']):
            self.predecessor_id = args['predecessor_id']
            self.predecessor_addr = args['predecessor_addr']
        self.logger.info(self)

    def stabilize(self, from_id, addr):
        """ Process STABILIZE protocol.
            Updates all successor pointers.

        Parameters:
            from_id: id of the predecessor of node with address addr
            addr: address of the node sending stabilize message
        """

        self.logger.debug('Stabilize: %s %s', from_id, addr)
        if from_id is not None and contains_successor(self.id, self.successor_id, from_id):
            # Update our successor
            self.successor_id = from_id
            self.successor_addr = addr

        # notify successor of our existence, so it can update its predecessor record
        args = {'predecessor_id': self.id, 'predecessor_addr': self.addr}
        self.send(self.successor_addr, {'method': 'NOTIFY', 'args':args})

        # <DHT>
        self.fingerTable[0].key = self.predecessor_id
        self.fingerTable[0].nodeid = self.predecessor_id
        self.fingerTable[0].address = self.predecessor_addr
        for i in range(1, 11): #range(1,11) = 1, 2, ..., 10
            succid, succaddr = self.FT_getSuccessor(self.fingerTable[i].key, self.id, self.addr)
            if succid and succaddr:
                self.fingerTable[i].nodeid = succid
                self.fingerTable[i].address = succaddr
        # Give feedback
        self.logger.debug('Updated fingerTable...')
        for ind in self.fingerTable:
            self.logger.debug('\t%s', ind)
        # Save finger table to file
        with open("ft/"+self.id.__str__()+".txt", "w") as f:
            for ind in self.fingerTable:
                f.write(f"{ind}\n")
        # </DHT>

    def put(self, key, value, address):
        """ Store value in DHT.

            Parameters:
            key: key of the data
            value: data to be stored
            address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug('Put: %s %s', key, key_hash)
        if contains_successor(self.id, self.successor_id, key_hash):
            self.keystore[key] = value
            self.send(address, {'method': 'ACK'})
        else:
            # send to DHT
            # Remote search implementation start
            msg = {'method': 'PUT', 'args':{'key':key, 'value': value, 'clientAddr': address}}
            self.send(self.FT_closest_preceding_node(key_hash), msg)
            print(f"# It is {self.FT_closest_preceding_node(key_hash)}")
            #self.send(self.FT_closest_preceding_node(key), msg) TODO Error because returns NULL
            # Remote search implementation end

    def get(self, key, address):
        """ Retrieve value from DHT.

            Parameters:
            key: key of the data
            address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug('Get: %s %s', key, key_hash)
        if contains_successor(self.id, self.successor_id, key_hash):
            value = self.keystore[key]
            self.send(address, {'method': 'ACK', 'args': value})
        else:
            # send to DHT
            # Remote search implementation start
            msg = {'method': 'GET', 'args': {'key': key, 'clientAddr': address}}
            self.send(self.successor_addr, msg)
            #print(f"# It is {self.FT_closest_preceding_node(key_hash)}")
            #self.send(self.FT_closest_preceding_node(key), msg) TODO Error because returns NULL
            # Remote search implementation end

    def run(self):
        self.socket.bind(self.addr)

        # Loop untiln joining the DHT
        while not self.inside_dht:
            join_msg = {'method': 'JOIN_REQ', 'args': {'addr':self.addr, 'id':self.id}}
            self.send(self.dht_address, join_msg)
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.debug('O: %s', output)
                if output['method'] == 'JOIN_REP':
                    args = output['args']
                    self.successor_id = args['successor_id']
                    self.successor_addr = args['successor_addr']
                    self.inside_dht = True
                    self.logger.info(self)

        done = False
        while not done:
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.info('O: %s', output)
                if output['method'] == 'JOIN_REQ':
                    self.node_join(output['args'])
                elif output['method'] == 'NOTIFY':
                    self.notify(output['args'])
                elif output['method'] == 'PUT':
                    # Remote search implementation start
                    if 'clientAddr' in output['args']:
                        self.put(output['args']['key'], output['args']['value'], output['args']['clientAddr'])
                    else:
                        self.put(output['args']['key'], output['args']['value'], addr)
                    # Remote search implementation end
                elif output['method'] == 'GET':
                    # Remote search implementation start
                    if 'clientAddr' in output['args']:
                        self.get(output['args']['key'], output['args']['clientAddr'])
                    else:
                        self.get(output['args']['key'], addr)
                    # Remote search implementation end
                elif output['method'] == 'PREDECESSOR':
                    # Reply with predecessor id
                    self.send(addr, {'method': 'STABILIZE', 'args': self.predecessor_id})
                elif output['method'] == 'STABILIZE':
                    # Initiate stabilize protocol
                    self.stabilize(output['args'], addr)
                elif output['method'] == 'FTGETSUCESSOR':
                    self.logger.debug("\tFTGETSUCESSOR received from %d (%s) for key %d", output['args']['answerid'], output['args']['answeraddr'], output['args']['key'])
                    succid, succaddr = self.FT_getSuccessor(output['args']['key'], output['args']['answerid'], output['args']['answeraddr'])
                    if succid and succaddr:
                        msg = {'method': 'FTFOUNDSUCESSOR', 'args': {'key': output['args']['key'],'nodeid':succid, 'nodeaddr': succaddr}}
                        self.send(output['args']['answeraddr'], msg)
                elif output['method'] == 'FTFOUNDSUCESSOR':
                    self.logger.debug("\tFTFOUNDSUCESSOR received for %d: %d (%s)", output['args']['key'], output['args']['nodeid'], output['args']['nodeaddr'])
                    for f in self.fingerTable:
                        if f.key.__str__()==output['args']['key'].__str__():
                            f.nodeid = output['args']['nodeid']
                            f.address = output['args']['nodeaddr']
            else: #timeout occurred, lets run the stabilize algorithm
                # Ask successor for predecessor, to start the stabilize process
                self.send(self.successor_addr, {'method': 'PREDECESSOR'})

    def __str__(self):
        return 'Node ID: {}; Address: {}; DHT: {}; Successor: {}; Predecessor: {}'\
            .format(self.id, self.addr, self.inside_dht, self.successor_id, self.predecessor_id)

    def __repr__(self):
        return self.__str__()