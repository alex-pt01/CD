# CHORD (DHT)

This repository implement a simple version of the [CHORD](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)) algorithm.
The provided code already setups the ring network properly.
1. Supports Node Joins
2. Finds the correct successor for a node
3. Run Stabilize periodically to correct the network


## Running the example
Run in two different terminal:

DHT (setups a CHORD DHT):
```console
$ python3 DHT.py
```
example (put and get objects from the DHT):
```console
$ python3 example.py
```

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

---

# Changes made for practical assignment

Computer Science Bachelor
**Distributed Systems**
Teachers: Diogo Gomes (regent) and Nuno Lau

Alexandre Rodrigues, 92951
Gonçalo Matos, 92972

---



When this method can't find a successor among the node's finger table, it send a message to the closest preceding none, to check if it can find the successor in it's finger table, and so on until a node that has the answer is found.

```json
{
   'method': 'FTGETSUCESSOR', 
    'args': {
        'key':key, 
        'answerid':answerId,
        'answeraddr': answerAddr
    }
}
```

This one will answer to the original sender, which has written it's address at args/answer. 

```json
{
   'method': 'FTFOUNDSUCESSOR', 
    'args': {
        'key': key,
        'nodeid': nodeid, 
        'nodeaddr': nodeAdd
    }
}
```

