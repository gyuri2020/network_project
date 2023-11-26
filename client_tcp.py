from socket import *
import sys



def tcp_client(serverIP, serverPort):
    
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverIP, serverPort)) #only tcp, not udp

    while True:
        message = "hello"
        clientSocket.send(message.encode())
        modifiedMessage = clientSocket.recv(2048).decode()

        if modifiedMessage == "EXIT":
            break

    clientSocket.close()

tcp_client(sys.argv[1], int(sys.argv[2]))