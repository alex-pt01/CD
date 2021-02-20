class DHT_Index():

    # Constructor
    def __init__(self, key, nodeid=None, address=None):
        self.key = key
        self.nodeid = nodeid
        self.address = address

    def __str__(self):
        return f"(Index for key {self.key}: nodeid {self.nodeid} with address {self.address})"