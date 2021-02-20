# Aula Prática 1
11 de fevereiro de 2020

## Sockets
[Documentação](https://docs.python.org/3/howto/sockets.html)

### Servidor

*socket()*

        Criar socket indicando família e protocolo
    
*bind()*

        Definir endereço local de socket
    
*listen()*

        Definir fila de espera de ligações
    
*accept()*

        Esperar por ligação, criar nova socket qnd há ligação
    
### Cliente

*socket()*

        Ver def anterior
    
*connect()*

        Estabelece ligação
    
*read()*
*sendall()*

        Enviar e receber dados
        
## JSON
[Documentação](https://docs.python.org/3/library/json.html)

Objeto em JSOn ẽ dicionário em Python e array em JSON é array em Python

import json

*dumps()*

        Converte python data para JSON string
        
*loads()*

        Converter JSON string para python data
        
        
## Selectors
[Documentação](https://docs.python.org/3/library/selectors.html)

*sel.register(sock, selectors.EVENT_READ, accept)*

        Quando acontecer um evento de leitura na socket *sock*, executar a função *accept*
        
*events = sel.select()*

        Bloqueia o processo até que ocorra um evento
        
*for key, mask in events:*

        key.data é a função definida como terceiro parâmetro no register
        key.fileobj é a socket

## Protocolos de comunicação

### UDP
Mais inseguro, perda de pacotes, não garante a ordem (envia AB e recebe BA), não há ligação contínua
Usa mesma socket para endereços distintos

### TCP
Seguro, orientado à mensagem e não há ligação, ligação contínua entre clientes e servidor (bidirecionais - stream), não há perda de pacotes

## Notas

Servidor tem de ter lista para guardar todos os utilizadores registados. Para cada utilizador registado tem associado uma socket.

Podem ser enviados três tipos de mensagens JSON

        {'op':'register', 'user':''}
        {'op':'msg', 'data':''}
        {'op':'clearregister'}
        
Selector n é só no servidor! Clientes tmb podem precisar, porque cliente vai enviar e receber mensagens. Definimos assim um selector associado por um lado à socket e por outro ao terminal (teclado).

Pode acontecer quando a socket vai ler as mensagens ser lida mais do que uma, pelo que é importante definir um **delimitador**, garantindo que todas as mensagens terminam com *\r\n*.

Podemos em alternativa definir um **cabeçalho**, onde codificamos em bytes o tamanho da mensagem a ler (este deve ter sempre o mesmo tamanho e deve ser sempre no mesmo formato).

## Objetivos

No código que temos só há uma socket, que quando associada a um cliente só fica disponível para outro quando o cliente se desligar.

Queremos ter uma socket em permanência no servidor só para receber novas ligações e ainda uma socket adicional por cada cliente ligado.

## Etapas de desenvolvimento

* Seletor no server
* Enviar e receber JSON (echo)
* Seletor no client
* Register e lista de users no server