import socket
 
def pmi(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", 8989))
    sock.sendall(data)
    result = sock.recv(1024)
    print result
    sock.close()
    return result