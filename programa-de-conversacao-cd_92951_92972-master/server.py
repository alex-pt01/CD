# Echo server program
import socket
import json
import selectors

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 5000            # Arbitrary non-privileged port (low number ports are usually reserved for “well known” services (HTTP, SNMP etc). If you’re playing around, use a nice high number (4 digits))

sel = selectors.DefaultSelector()
socks_list = {}

def accept(sock, mask):
    conn, addr = sock.accept() #Accept socket
    print(f'#New connection with {addr}. Currently there are {len(socks_list)} active clients.')
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)


def read(conn, mask):
    n = conn.recv(2)
    nbytes = int.from_bytes(n, byteorder='big')
    data = conn.recv(nbytes)
    if data:
        dataPython = json.loads(data.decode()) #Convert JSON string (data.decode) to Python (dictionary)
        
        if dataPython['op']=='register': #Register new user
            print(f"#Registered user {dataPython['user']}, from {conn.getpeername()}")
            #Notify user that it was sucessfully registered, and give him info about the active users
            msg = {
                'op': 'registerSucess',
                'users' : list(socks_list.values()),
            }
            socks_list[conn] = dataPython['user'].strip() #Add user to the sockets dictionary
            msgStr = json.dumps(msg).encode('utf8')
            conn.send(len(msgStr).to_bytes(2, byteorder='big'))
            conn.send(msgStr)
            #Notify other users that a new user connected to the server
           
            msg = {
                'op': 'newUser',
                'user' : socks_list[conn],
                'users' : list(socks_list.values()),
            }
            msgStr = json.dumps(msg).encode('utf8')
            for socket in socks_list:
                if socket != conn:
                    socket.send(len(msgStr).to_bytes(2, byteorder='big'))
                    socket.send(msgStr)
        
        elif dataPython['op']=='msg': #Receive message
            if conn in socks_list: #If user is registered, output data, and send it to all the other users
                dataPython['user'] = socks_list[conn]
                print(f"{socks_list[conn]} ({conn.getpeername()}) at {dataPython['timestamp']}: {dataPython['data']}")
                msgStr = json.dumps(dataPython).encode('utf8')
                for socket in socks_list:
                    if socket != conn:
                        socket.send(len(msgStr).to_bytes(2, byteorder='big'))
                        socket.send(msgStr)
            else:
                print(f"Received a message from an unregistered client ({conn.getpeername()}) at {dataPython['timestamp']}: {dataPython['data']}")

        elif dataPython['op']=='deregister': #Close socket
            print(f"#Closing connection with {socks_list[conn]} {conn.getpeername()}")
            #Notify other sockets that one has gone
            msg = {
                'op': 'exitUser',
                'user' : socks_list[conn],
                'users' : [],
            }
            socks_list.pop(conn)
            msg['users'] = list(socks_list.values())
            msgStr = json.dumps(msg).encode('utf8')
            for socket in socks_list:
                socket.send(len(msgStr).to_bytes(2, byteorder='big'))
                socket.send(msgStr)
            sel.unregister(conn)
            conn.close()

        else:
            print("Invalid data!")
            print(data)









with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print("MESSAGE SERVER")
    s.bind((HOST, PORT)) #Bind the socket to a public host
    s.listen(1) #Become a server socket
    sel.register(s, selectors.EVENT_READ, accept)
    print("#Server active, waiting for new connections...")
    while True:
        events = sel.select() #Blocks process until event occurs
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask) #accept(socket, mask)
