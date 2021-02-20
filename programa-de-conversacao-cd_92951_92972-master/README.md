# cd-trabalho-1
Programa de Conversação - Cliente/Servidor

The server has a list (*socks_list*) where it saves all the active users.

## Operations implemented

* Register a new client (to the *socks_list*)

            Client JSON: {'op':'register', 'user':<String:username>}
            Server JSON (to the registered client): {'op': 'registerSucess', 'users' : <String:userList>}
            Server JSON (to the other clients - alredady registered): {'op': 'newUser', 'user' : <String:username>, 'users' : <String[]:userList>}

* Send a message

            Client JSON: msg = { 'op': 'msg', 'timestamp': <String:time>, 'data' : <String:message>}
            Server JSON (sent to all except the sender): { 'op': 'msg', 'timestamp': <String:time>, 'data' : <String:message>, 'user': <String:username>}

* A user exits the server

            Client JSON: {'op':'deregister'}
            Server JSON (to the other clients - still registered): {'op': 'exitUser', 'user' : <String:username>, 'users' : <String[]:userList>}

When a JSON is sent without a valid 'op' field, it is printed, with the alert that an invalid message was received! (Both in user and server)

## Support Material

[Sockets](https://docs.python.org/3/library/socket.html)

[JSON](https://docs.python.org/3/library/json.html)

[Selectors](https://docs.python.org/3/library/selectors.html)
