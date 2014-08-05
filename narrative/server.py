import multiprocessing, sys
import socket, pickle
import narrative

manager = multiprocessing.Manager()
 
def handle(connection, address, events, pairs):
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("process-%r" % (address,))
    try:
        logger.debug("Connected %r at %r", connection, address)
        data = connection.recv(1024)
        logger.debug("Received data %r", data)
        # Parse data
        score = None
        data = data[1:].split(data[0])
        # Handle appropriate method
        if (data[0] == 'pmi'):
            nb = narrative.NarrativeBank(typed=True)
            nb.events = events
            nb.pairs = pairs
            if len(data) == 3:
                score = nb.pmi(data[1], data[2])
            elif len(data) == 4:
                score = nb.pmi(data[1], data[2], data[3])

        if(score):
            connection.sendall(str(score))
            logger.debug("Sent data %r", str(score))
        else:
            connection.sendall('NaN')
            logger.debug("Sent data 'NaN'")
        
    except:
        logger.exception("Problem handling request")
    finally:
        logger.debug("Closing socket")
        connection.close()
 
class Server(object):
    def __init__(self, hostname, port):
        import logging
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port
        self.load()

    def load(self):
        # Load data from serialized file
        f = open(sys.argv[1], 'r')
        data = pickle.load(f)
        self.events = manager.dict(data[0])
        self.pairs = manager.dict(data[1])
        f.close()
 
    def start(self):
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)
 
        while True:
            conn, address = self.socket.accept()
            self.logger.debug("Got connection")
            process = multiprocessing.Process(target=handle, args=(conn, address, self.events, self.pairs))
            process.daemon = True
            process.start()
            self.logger.debug("Started process %r", process)
 
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    server = Server("0.0.0.0", 8989)
    try:
        logging.info("Listening")
        server.start()
    except:
        logging.exception("Unexpected exception")
    finally:
        logging.info("Shutting down")
        for process in multiprocessing.active_children():
            logging.info("Shutting down process %r", process)
            process.terminate()
            process.join()
    logging.info("All done")