# Echo client program
import socket
import json
import time
import sys
import fcntl
import os
import selectors

HOST = 'localhost'      # Address of the host running the server  
PORT = 5000             # The same port as used by the server

m_selector = selectors.DefaultSelector()
socks_list = []
'''
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    WARNING = '\033[93m'
'''

#funcao para processar os dados
def processInput(stdin):
    msg_raw = stdin.read().rstrip()
    if msg_raw in '\r\n':
        sys.exit(0)
    if(msg_raw.strip()=='exit()'): #Shut down the program
        print("#You are leaving the chat server... See you soon! ;)")
        msg = {
            'op': 'deregister',
        }
        msgStr = json.dumps(msg).encode('utf8')
        s.send(len(msgStr).to_bytes(2, byteorder='big'))
        s.send(msgStr)
        m_selector.unregister(sys.stdin)
        m_selector.unregister(s)
        s.close()
        sys.exit(0)
    msg = {
        'op': 'msg',
        'timestamp': time.strftime("%H:%M:%S"),
        'data' : msg_raw
    }
    msgStr = json.dumps(msg).encode('utf8')
    s.send(len(msgStr).to_bytes(2, byteorder='big'))
    s.send(msgStr)



#funcao que recebe os dados 
def receiveData(connection):
    n = connection.recv(2)
    nbytes = int.from_bytes(n, byteorder='big')
    data = connection.recv(nbytes) # receive the response
    if data:
        dataPython = json.loads(data.decode())
        
        if dataPython['op'] == 'msg': #Receive message, output it
            print(f"{dataPython['user']} ({dataPython['timestamp']}): {dataPython['data']}")
        
        elif dataPython['op'] == 'registerSucess':
            print("#You were sucessfully registered at the server! \n#Online Users:", end="")
            if len(dataPython['users']) == 0:
                print("\t...ups! you're alone", end="")
            else:
                for user in dataPython['users']:
                    print("\t"+user, end="")
            print()
            print("#You can type your messages now! Type 'exit()' to leave...")
        
        elif dataPython['op'] == 'newUser':
            print(f"#User '{dataPython['user']}' has just connected to the server! \n#The current active users are:", end="")
            if len(dataPython['users']) == 0:
                print("\t...ups! you're alone", end="")
            else:
                for user in dataPython['users']:
                    print("\t"+user, end="")
            print()

        elif dataPython['op'] == 'exitUser':
            print(f"#User '{dataPython['user']}' has just left the server! \n#The current active users are:", end="")
            if len(dataPython['users']) == 0:
                print("\t...ups! you're alone", end="")
            else:
                for user in dataPython['users']:
                    print("\t"+user, end="")
            print()
        
        
        else:
            print("#Unknown data type received!")
            print(data) 


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: #funcao que cria o socket
    s.connect((HOST, PORT)) #Connect to the web server

    print("MESSAGE CLIENT")
    username = input("What is your username? ").rstrip()

    msg = {'op':'register', 'user':username} #Python (dictionary)
    msgStr = json.dumps(msg).encode('utf8') #Encode string (convert to bytes) and send it
    s.send(len(msgStr).to_bytes(2, byteorder='big'))
    s.send(msgStr)

    # set sys.stdin non-blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    # Para processar a data
    m_selector.register(sys.stdin, selectors.EVENT_READ, processInput) 
    # Registar o socket
    m_selector.register(s, selectors.EVENT_READ, receiveData) # Receive data
    

    #Fica a ler mensagens
    while True:
        sys.stdout.write('')
        sys.stdout.flush()
        
        for k, mask in m_selector.select():
            callback = k.data
            callback(k.fileobj)