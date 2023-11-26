from socket import *
import threading
import sys


def handle_client(connectionSocket, addr):
    cnt = 0
    while True:

        message = connectionSocket.recv(2048).decode() # always use thread for multiple client
        modifiedMessage = message.upper()
        cnt += 1
        if cnt == 100: # for test
            modifiedMessage = "EXIT"
        connectionSocket.send(modifiedMessage.encode())
        if modifiedMessage == "EXIT":
            break
    connectionSocket.close()
    return 

def tcp_server(serverIP, serverPort):

    serverSocket = socket(AF_INET, SOCK_STREAM) #TCP
    serverSocket.bind((serverIP, serverPort))
    serverSocket.listen(1)
    print("The server is ready to receive")

    while True:
        connectionSocket, addr = serverSocket.accept()
        #I want to use thread here
        thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
        thread.start()
        

tcp_server(sys.argv[1], int(sys.argv[2]))


    