import socket
import threading
import time
import os
import sys

## Using gethostname to get host IP address, typically 127.0.0.1
host = socket.gethostname()

## If statement to check whether or not user has inputted 2 arguments (file location, port number)
arg_requirement = 2
if len(sys.argv) != arg_requirement:
    print(f"Error: {arg_requirement} arguments required")
    sys.exit(1)

## Declaring variables for sockets e.g. port numbers, server addresses, buffer sizes
UDP_port = int(sys.argv[1])
UDP_server_addr = (host, UDP_port)
TCP_port = ''
TCP_server_addr = (host, 0)
buffer_size = '5'

## Setting global boolean variables
stop_thread = False
authenticated = False

## Creating tuple of commands accepted from client side
commands = ("get", "lap", "lpf", "pub", "sch", "unp", "xit")

## main function declaration
def main():
    # open UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # initial connect msg from client to server
    data = "Hello"
    data = data.encode("utf-8")
    client_socket.sendto(data, UDP_server_addr)
    
    # open TCP socket, bind socket to TCP address and listen for incoming connections
    welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    welcome_socket.bind(TCP_server_addr)
    welcome_socket.listen(5)
    welcome_socket_addr = welcome_socket.getsockname()
    
    # Un-commment the next 3 lines for testing
    # print(f"TCP server socket: {welcome_socket}")
    # print(f"UDP socket: {client_socket}")
    # print(f"Connection established with {tcp_port}")
    
    #start thread 1 -> handleClientRequests function
    threading.Thread(target=handleClientRequests, args=(client_socket, UDP_server_addr, welcome_socket_addr,)).start()
    #start thread 2 -> sendHeartBeat function
    threading.Thread(target=sendHeartBeat, args=(client_socket, UDP_server_addr,)).start()
    
    ## Call setup_welcome_socket to open peer server socket
    welcome_socket = setup_welcome_socket(welcome_socket)
    
# function declaration for setup_welcome_socket
# starts thread 3 -> handleGetFileRequests
# this function creates a TCP welcome socket and starts the thread that calls a function
def setup_welcome_socket(welcome_socket):
    while True:
        connection_socket, TCP_client_address = welcome_socket.accept()
        # print(f"{connection_socket}, {TCP_client_address} has connected")
        #start thread 3
        threading.Thread(target=handleGetFileRequests, args=(connection_socket,)).start()

# function declaration for handleGetFileRequests
# This function will accept incoming TCP connection requests and send desired files to requesting peers
def handleGetFileRequests(connection_socket):
    try:
        # TCP socket waits to recieve get file query and returns file chunk by chunk
        getFileQuery = connection_socket.recv(1024)
        getFileQuery = getFileQuery.decode('utf-8')
        with open(getFileQuery, 'rb') as file:
            while True:
                chunk = file.read(1024)
                if not chunk:
                    break
                connection_socket.sendall(chunk)
        # print(f"File {getFileQuery} sent successfully")
    except Exception as e:
        print(f"An error occured sending file {e}")
    finally:
        connection_socket.close()

# function declaration for sendHeartBeat function
# This function sends heartbeats to the server once the client has been successfully authenticated
def sendHeartBeat(client_socket, server_addr):
    global authenticated
    global stop_thread
    # check if xit command has been called
    # check if user has authenticated with the server
    while not stop_thread:
        if authenticated == True:
            # create time-stamp using time module
            formatTime = time.strftime("%Y-%m-%d %H:%M:%S :", time.localtime())
            # send heartbeat 
            try:
                data = "HBT HBT"
                data = data.encode("utf-8")
                client_socket.sendto(data, server_addr)
                # print(f"{formatTime} : HBT HBT")
                time.sleep(2)
            except Exception as e:
                print(f"{e}")

# function declaration for handleClientRequests function
# this function initially waits for user authentication inputs
# upon successful auth, this function will handle all user commands
def handleClientRequests(client_socket, server_addr, welcome_socket_addr):
    global stop_thread
    global authenticated
    global commands
    
    ## check username loop
    if authenticated == False:
        while not stop_thread:
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            
            # ensuring usernames do not contain whitespace
            if len(username.split()) != 1:
                print("Authentication failed. Please try again.")
                continue
            # ensuring passwords do not contain whitespace
            if len(password.split()) != 1:
                print("Authentication failed. Please try again.")
                continue
            
            # creating authentication packet for server    
            authPacket = "AUTH " + username + " " + password + " " + host + " " + str(welcome_socket_addr)
            # encoding auth packet
            authPacket = authPacket.encode("utf-8")
            # sending auth packet
            client_socket.sendto(authPacket, server_addr)
            # print("Auth request packet sent")
            
            # receiving response from server
            authResult, addr = client_socket.recvfrom(1024)
            authResult = authResult.decode("utf-8")
            # print("Auth response packet received")
            
            # interpreting server response for authentication
            if authResult == "user not found":
                print("Authentication failed. Please try again.")
                continue
            if authResult == "bad password":
                print("Authentication failed. Please try again")
                continue
            if authResult == "user active":
                print("Authentication failed. Please try again")
                continue
            if authResult == "login successful":
                # successful login -> welcome message and set authenticated to equal "True"
                print("Welcome to BitTrickle")
                authenticated = True
                break
    
    # after successful authentication, print list of available commands
    print("Available commands are: get, lap, lpf, pub, sch, unp, xit")
    while True:

        # accept user inputs
        data = input()
        # check atleast 1 arg has been entered:
        if not data.split()[0]:
            print(f" is not a valid command\nAvailable commands are: get, lap, lpf, pub, sch, unp, xit")
        
        # check arg 1 is a valid input
        if data.split()[0] not in commands:
            print(f"{data.split()[0]} is not a valid command\nAvailable commands are: get, lap, lpf, pub, sch, unp, xit")
            continue
        
        # xit request
        if data == 'xit':
            print("Goodbye!")
            break
        
        # get request
        if data.split()[0] == "get":
            args = data.split()
            # check valid no. of args
            if len(args) < 2 or len(args) > 2:
                print(f"get command takes 2 arguments, you entered: {len(args)}")
                continue
            else:
                getFileQuery = data.split()[1]
                data = "get " + getFileQuery
        
        # pub request
        if data.split()[0] == "pub":
            args = data.split()
            # check valid no. of args
            if len(args) < 2 or len(args) > 2:
                print(f"pub command takes 2 arguments, you entered: {len(args)}")
                continue
                
            else:
                # search local working directory for specified file
                FilePubQueryName = data.split()[1]
                if os.path.exists(FilePubQueryName):
                    # print(f"File exists: {FilePubQueryName}")
                    data = "pub " + FilePubQueryName
                else:
                    print(f"File does not exist")
                    continue
        
        # unpub request
        if data.split()[0] == "unp":
            args = data.split()
            # check valid no. of args
            if len(args) < 2 or len(args) > 2:
                print(f"pub command takes 2 arguments, you entered: {len(args)}")
                continue
            else:
                # create unp packet
                FileUnpubQueryName = data.split()[1]
                data = "unp " + FileUnpubQueryName
            
        # sch request
        if data.split()[0] == "sch":
            args = data.split()
            # check valid no. of args
            if len(args) < 2 or len(args) > 2:
                print(f"sch command takes 2 arguments, you entered: {len(args)}")
                continue
            else:
                # create sch packet
                schQueryName = data.split()[1]
                data = "sch " + schQueryName
        
        # encode and send data to server
        data = data.encode("utf-8")
        client_socket.sendto(data, server_addr)
    
        # receive and decode data from server
        data, addr = client_socket.recvfrom(1024)
        data = data.decode("utf-8")
        
        # get response
        if data.split("*")[0] == "GET":
            if data.split("*")[1]:
                # print(f"GET receieved: {data.split('*')[1]}, {data.split('*')[2]}, {data.split('*')[3]}, {data.split('*')[4]}")
                # parse and seperate incoming data packet into seperate categories to work with
                getFileQuery = data.split("*")[1]
                temp_files = eval(data.split("*")[2])
                activeUsers = eval(data.split("*")[3])
                TCP_addresses = eval(data.split("*")[4])
                # print(f"TCP_addresses: {TCP_addresses}")
                fileFound = False
                UploaderActive = False
                ## CHECK IF QUERIED FILE IS EXISTS (data.split("*")[2])
                for i in range(len(temp_files)):
                    if temp_files[i].split()[0] == getFileQuery:
                        fileUploaderUsername = temp_files[i].split()[1]
                        # print(f"File {getFileQuery} has been found")
                        fileFound = True

                ## CHECK IF FILE UPLOADER IS ACTIVE (data.split("*")[3])
                if fileFound == True:
                    for i in activeUsers:
                        if activeUsers[i] == fileUploaderUsername:
                            fileUploaderAddress = i
                            # print(f"File uploader: {fileUploaderAddress} is active")
                            UploaderActive = True
                
                if UploaderActive == True:
                    ## FIND TCP ADDRESS OF PEER
                    peer_address = TCP_addresses[fileUploaderAddress]
                    # print(f"peer address: {peer_address}")
                            
                    ## ESTABLISH A TCP CONNECTION WITH FILE UPLOADER                
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # print(f"P2P tcp socket created")
                    peer_socket.connect(peer_address)
                    # print(f"connected to peer")
                    peer_socket.sendall(getFileQuery.encode('utf-8'))
                    # print(f"sending file query to peer")
                    
                    ## DOWNLOAD FILE CHUNK BY CHUNK IN WORKING DIRECTORY
                    with open(getFileQuery, 'wb') as file:
                        # print(f"file opened and ready for writing")
                        while True:
                            chunk = peer_socket.recv(1024)
                            # print(f"TCP peer socket: {peer_socket}")
                            if not chunk:
                                break
                            file.write(chunk)
                            # print("chunk sent, chunk sent")
                    # print(f"file: {file}")
                    print(f"{getFileQuery} downloaded successfully")
                    # close socket
                    peer_socket.close()
                
                # display error message if file not found or user not active
                else:
                    print("File not found")
                
                
                
        # lpf response
        if data.split("*")[0] == "LPF":
            if data.split("*")[1]:
                # print(f"LPF recieved: {data.split("*")[1]}, {data.split("*")[2]}")
                temp_files = eval(data.split("*")[1])
                # print(f"type: {type(temp_files)}")
                # temp_ActiveUsers = eval(data.split("*")[2])
                
                # append all files published by user into MyFiles
                myFiles = []
                for i in range(len(temp_files)):
                    if temp_files[i].split()[1] == username:
                        myFiles.append(temp_files[i].split()[0])
                file_length = len(myFiles)
                
                # printing
                if file_length == 0:
                    print(f"No files published")
                else:
                    # print for 1 file found
                    if file_length == 1:
                        print(f"{file_length} file published:\n{myFiles[0]}")
                    # print for more than 1 file found
                    else:
                        # print out line by line file name and uploaded user by
                        print(f"{file_length} files published:")
                        for i in range(len(myFiles)):
                            print(myFiles[i])
                continue
        
        # lap response
        if data.split()[0] == "LAP":
            # parse information by evaluating data as iterable data structure
            data = data[4:]
            dataDict = eval(data)
            temp = []
            i,j = 0, 0
            # append all active usernamne that are not user in temp array
            for i in dataDict:
                if dataDict[i] != username:
                    temp.append(dataDict[i])
            
            # number of active peers is equal to the length of temp array
            no_of_users = len(temp)
            # case where no active peers found
            if no_of_users == 0:
                print(f"No active peers")
            else:
                # case where 1 active peer found
                if no_of_users == 1:
                    print(f"{no_of_users} active peer:\n{temp[0]}")
                else:
                    # case where >1 active peer found
                    print(f"{no_of_users} active peers:")
                    # print active peer usernames line by line
                    for j in range(len(temp)):
                        print(f"{temp[j]}")
            continue
        
        # pub response
        if data.split()[0] == "PUB":
            if data.split()[1] == "OK":
                print(f"File published successfully")
                continue
            if data.split()[1] == "DUP":
                print(f"This file has already been uploaded")
                continue

        # unpub response
        if data.split()[0] == "UNP":
            if data.split()[1] == "OK":
                print(f"File unpublished successfully")
                continue
            else:
                print(f"File unpublication failed")
        
        # sch response
        if data.split("*")[0] == "SCH":
            if data.split("*")[2]:
                
                ## parse and sort all received incoming data into workable data structures
                # print(f"SCH recieved: {data.split("*")[2]}, {data.split("*")[3]}")
                temp_files = eval(data.split("*")[2])
                # print(f"temp_files: {temp_files}")
                #temp_ActiveUsers = eval(data.split("*")[3])
                notMyFiles = []
                MyFiles = set()
                schQuery = data.split("*")[1]
                
                # sort out files that are not published by the user (appending into notMyFiles)
                for i in temp_files:
                    if i.split()[1] != username:
                        notMyFiles.append(i.split()[0])
                    else:
                        MyFiles.add(i.split()[0])
                # print(f"notmyfiles: {notMyFiles}")

                # search files with matching substrings (appending into schQueryMatches)
                schQueryMatches = []
                for i in range(len(notMyFiles)):
                    string = ''.join(notMyFiles[i])
                    for j in range(len(string) - len(schQuery)+1):
                        if string[j:j+len(schQuery)] == schQuery:
                            if notMyFiles[i] not in schQueryMatches:
                                schQueryMatches.append(notMyFiles[i])
                
                # check SchQueryMatches for files NOT owned by the user (appending into schQueryResultPrintList)
                SchQueryResultPrintList = []
                for i in range(len(schQueryMatches)):
                    if schQueryMatches[i] not in MyFiles:
                        SchQueryResultPrintList.append(schQueryMatches[i])
                          
                # printing 
                no_of_files = len(SchQueryResultPrintList)
                # case where no files are found
                if no_of_files == 0:
                    print("No files found")
                # case where 1 file is found
                if no_of_files == 1:
                    print(f"{no_of_files} file found:")
                    print(f"{SchQueryResultPrintList[0]}")
                else:
                    # case where >1 file is found
                    print(f"{no_of_files} files found:")
                    # print out line by line file name and uploaded user by
                    if SchQueryResultPrintList:
                        for i in SchQueryResultPrintList:
                            print(f"{i}")
                            
    ## triggers after "xit" command is called
    # de-auth the client  
    authenticated = False
    # stop heartbeat thread
    stop_thread = True
    # close client socket
    client_socket.close()
    
# calling main function
if __name__ == "__main__":

    main()






