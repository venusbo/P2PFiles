import socket
import threading
import time
import os
import sys

# using socket library to retrieve host IP address
host = socket.gethostname()

## check input has the appropriate number of arguments (file destination, port number)
arg_requirement = 2
if len(sys.argv) != arg_requirement:
    print(f"Error: {arg_requirement} arguments required")
    sys.exit(1)

# storing second argument as port number
port = int(sys.argv[1])

## Declaring server-side data structures
## clients =  {(address): 'lasthearbeat', (address1): 'lastheartbeat'}
clients = {}

## files =  {'filename': (address), 'filename1': (address1)}
files = []

## active users = {(address): 'username',(address1): 'username1'}
activeUsers = {}

## activeUsernames = [user1, user2, user3]
activeUsernames = set()

## active users TCP = {()}
activeUsersTCP = {}

# function dec for main function
def main():
    
    ## opening, and parsing credentials.txt file into data structures
    creds = set()
    usernames = set()
    credentials = open('credentials.txt', 'r')
    Lines = credentials.readlines()
    for line in Lines:
        creds.add(line)
        usernames.add(line.split()[0])
        
    # print(creds)
    # print(usernames)
    ## creating timestamps with time library
    currentTime = time.strftime("%Y-%m-%d %H:%M:%S :", time.localtime())
    print(f"{currentTime} server is starting")
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))
    print(f"{currentTime} server is listening")
    
    # start thread 1 -> handleClient
    threading.Thread(target=handleClient, args=(server, usernames, creds,)).start()

# This function handles all incoming data and client commands/requests appropriate
def handleClient(server, usernames, creds):
    data, client_addr = server.recvfrom(1024)
    data = data.decode("utf-8")
    # print(f"{data}")

    # created formatted timestamp
    formatTime = time.strftime("%Y-%m-%d %H:%M:%S :", time.localtime())
    # print(f"{formatTime} new connection from: {client_addr}")
    
    ## ACCEPT AND DECODE ALL INCOMING PACKAGES
    while True:
        # set time of data recieval
        formatTime = time.strftime("%Y-%m-%d %H:%M:%S :", time.localtime())
        # recieve packet
        data, addr = server.recvfrom(1024)
        data = data.decode("utf-8")
        # print(f"Packet from client reads: {data}")
        
        # check current time
        currentTime = time.time()
        
        ## CHECK HEARTBEAT TIMEOUT
        clients_to_remove = []
        if clients:
            # logic for whether a user has not send a heartbeat in last 3 seconds
            for client, last_heartbeat in list(clients.items()):
                if currentTime - last_heartbeat > 3:
                    print(f"{formatTime} removed client {client} for inactivity")
                    # add users to an array to be removed
                    clients_to_remove.append(client)
            # if clients to remove array is non-empty, remove users from clients dictionary, activeUsernames set and activeUsers dictionary.
            if clients_to_remove:        
                for client in clients_to_remove:
                    del clients[client]
                    activeUsernames.remove(activeUsers[client])
                    del activeUsers[client]
        
        ## check current time for timeout
        currentTime = time.time()
        
        ## MANAGE HEARTBEAT
        if data == "HBT HBT" and addr in clients:
            clients[addr] = currentTime
            print(f"{formatTime} Recieved HBT from {activeUsers[addr]} ")
        
        ## AUTH REQUEST
        if data.split()[0] == "AUTH":
            username = data.split()[1]
            ## parse and interpret auth packet which includes authentication information and TCP socket info.
            parse_tcp_address = data.split()[4] + " " + data.split()[5]
            # print(f"parse_tcp_address: {parse_tcp_address}")
            tcp_server_address = eval(parse_tcp_address)
            # print(f"tcp server address: {tcp_server_address}")
            # print(data.split()[1])
            if username == "HBT":
                continue
            
            ## check if user's username in server credentials
            if username not in usernames:
                print(f"{formatTime} Sent ERR to {username}")
                data = "user not found"
                data = data.encode("utf-8")
                server.sendto(data, addr)
                continue
            
            ## if user's username in server credentials:
            ## check if the password matches server credentials
            ## if correct, add client info the respective data structures (client timestamp, username, tcp address)
            else:
                print(f"{formatTime} Received AUTH from {username}")
                data = data.split()[1] + " " + data.split()[2] + "\n"
                # print(f"{formatTime} password attempt: {data}")
                if data in creds and username not in activeUsernames:
    
                    print(f"{formatTime} Sent OK to {username}")
                    ## create successful login packet
                    data = "login successful"
                    currentTime = time.time()
                    clients[addr] = currentTime
                    activeUsers[addr] = username
                    activeUsernames.add(username)
                    activeUsersTCP[addr] = tcp_server_address
                    # print(f"clients:{clients}")
                    # print(f"activeUsers: {activeUsers}")
                    # print(f"tcp_server_address: {activeUsersTCP}")
                    data = data.encode("utf-8")
                    server.sendto(data, addr)
                    continue
        
                else:
                    print(f"{formatTime} Sent ERR to {username}")
                    data = "bad password"
                    data = data.encode("utf-8")
                    server.sendto(data, addr)
                    continue
        
        ## handle commands GET
        if data.split()[0] == "get":
            ## combine all files and usernames into a single packet and send to client
            data = "GET*" + str(data.split()[1]) + "*" + str(files) + "*" + str(activeUsers) + "*" + str(activeUsersTCP)
            # print(f"data: {data}")
            print(f"{formatTime} Recieved GET from {activeUsers[addr]}")
            data = data.encode("utf-8")
            server.sendto(data, addr)
            print(f"{formatTime} Sent OK to {activeUsers[addr]}")

        ## handle commands LPF
        if data.split()[0] == "lpf":
            ## combine all files and usernames into a single packet and send to client
            data = "LPF*" + str(files) + "*" + str(activeUsers)
            # print(f"data: {data}")
            print(f"{formatTime} Recieved LPF from {activeUsers[addr]}")
            data = data.encode("utf-8")
            server.sendto(data, addr)
            print(f"{formatTime} Sent OK to {activeUsers[addr]}")
        
        ## handle commands SCH
        if data.split()[0] == "sch":
            ## combine all files and usernames into a single packet and send to client
            data = "SCH*" + str(data.split()[1]) + "*" + str(files) + "*" + str(activeUsers)
            # print(f"data: {data}")
            print(f"{formatTime} Recieved SCH from {activeUsers[addr]}")
            data = data.encode("utf-8")
            server.sendto(data, addr)
            print(f"{formatTime} Sent OK to {activeUsers[addr]}")
            
        ## hande commands LAP
        if data.split()[0] == "lap":
            data = "LAP " + str(activeUsers)
            print(f"{formatTime} Recieved LAP from {activeUsers[addr]}")
            data = data.encode("utf-8")
            server.sendto(data, addr)
            print(f"{formatTime} Sent OK to {activeUsers[addr]}")
        
        ## handle commands PUB
        if data.split()[0] == "pub":
            # store file name in hashmap
            print(f"{formatTime} Recieved PUB from {activeUsers[addr]}")
            filePubQueryName = data.split()[1]
            
            # check if file has been uploaded by this user
            if filePubQueryName + " " + activeUsers[addr] in files:
                # return FAILED message to clients
                data = "PUB " + "DUP"
                data = data.encode("utf-8")
                server.sendto(data, addr)
                print(f'{formatTime} Sent ERR to {activeUsers[addr]}')
            else:
                files.append(filePubQueryName + " " + activeUsers[addr])
                # print(f"files: {files}")
                # return OK message to client
                data = "PUB " + "OK"
                data = data.encode("utf-8")
                server.sendto(data, addr)
                print(f'{formatTime} Sent OK to {activeUsers[addr]}')
        
        ## handle commands UNP
        if data.split()[0] == "unp":
            ## parse and sort incoming data packet
            fileUnpubQueryName = data.split()[1]
            storedFileQuery = fileUnpubQueryName + " " + activeUsers[addr]
            
            ## check if the queried file is in the published files array
            if storedFileQuery in files:
                ## remove queried file from the files array
                files.remove(storedFileQuery)
                data = "UNP " + "OK"
                data = data.encode("utf-8")
                server.sendto(data, addr)
                print(f'{formatTime} Sent OK to {activeUsers[addr]}')
            else:
                ## create OK data packet to client
                data = "UNP " + "404"
                ## encode and send OK data packet to client
                data = data.encode("utf-8")
                server.sendto(data, addr)
                print(f'{formatTime} Sent ERR to {activeUsers[addr]}')
                                        
## function declaration for closing server    
def close(server):
    server.close()

## main function declaration
if __name__ == "__main__":
    main()
