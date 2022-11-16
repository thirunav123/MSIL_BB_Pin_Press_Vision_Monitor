import time,socket
from _thread import *
host = '127.0.0.1'
port = 2004
print('Waiting for connection response')
def client_n(a):
    ClientMultiSocket = socket.socket()
    try:
        ClientMultiSocket.connect((host, port))
    except socket.error as e:
        print(str(e))
    res = ClientMultiSocket.recv(1024)
    count=0
    while True:
        #Input = input('Hey there: ')
        Input=str(a)+'n   '
        ClientMultiSocket.send(str.encode(Input))
        res = ClientMultiSocket.recv(1024)
        print(res.decode('utf-8'))
        count=count+1
        time.sleep(5)
    ClientMultiSocket.close()
a=0
for i in range(5):
    start_new_thread(client_n,(a,))
while True:
    time.sleep(9)