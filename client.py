import sys
import hashlib
import socket 

HOST = "127.0.0.1"
HOSPITAL_TCP_PORT = 26214

def sha256_hash(text:str)->str:
    text = text.strip()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def stream_client(cmd:str, args=None):
    # change message variable, to be sent to respective backend servers, depending on cmd
    username = args[0]
    if cmd == "auth":
        password =  args[1]
        # "client must ensure both username and password are hashed before submitting a request to hospital server"
        message = f"AUTHENTICATE,{sha256_hash(username)},{sha256_hash(password)}"

    elif cmd == "lookup":
        message = f"LOOKUP,{sha256_hash(username)}"

    elif cmd == "lookup_d":
        doc_name = args[1]
        message = f"LOOKUP_D,{sha256_hash(username)},{doc_name}"

    elif cmd == "schedule":
        doc_name, block_period, illness = args[1], args[2], args[3]
        message = f"SCHEDULE,{sha256_hash(username)},{doc_name},{block_period},{illness}"
    

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
            sockfd.connect((HOST, HOSPITAL_TCP_PORT))
            sockfd.send(message.encode())
            if cmd == "auth":
                print(f"{username} sent an authentication request to the hospital server.")
            elif cmd == "lookup":
                print(f"{username} sent a lookup request to the hospital server.")
            elif cmd == "lookup_d":
                print(f"Patient {username} sent a lookup request to the hospital server for {doc_name}.")
            elif cmd == "schedule":
                print(f"{username} sent an appointment schedule request to the hospital server.")
            response = sockfd.recv(4096).decode() 
            client_port = sockfd.getsockname()[1]  # getting client-side port number!!
            sockfd.close()
            return response, client_port
    except OSError as e:
        print("socket error:", e)
        sockfd.close()
        sys.exit(1)

def main():
    print("The client is up and running.")
    username, password = sys.argv[1], sys.argv[2]

    # send request to hospital server 
    auth_response, auth_port = stream_client("auth", (username, password))
    if auth_response == "DOCTOR_ACCESS":
        print(f"{username} received the authentication result. Authentication successful. You have been granted doctor access.")
        
    elif auth_response == "PATIENT_ACCESS":
        print(f"{username} received the authentication result. Authentication successful. You have been granted patient access.")

        while True: 
            command = input(">").strip().split()
            
            # LOOKUP: hospital server -> appointment server, returns list of doctors with at least one available slot 
            if command[0] == "lookup" and len(command) == 1:
                lookup_response, lookup_port = stream_client("lookup", (username,))
                print(f"The client received the response from the hospital server using TCP over port {lookup_port}.")
                print("\nThe following doctors are available:")
                lookup_response_list = lookup_response.split(';')
                for doctor_name in lookup_response_list:
                    if doctor_name:
                        print(f"{doctor_name}")

            # LOOKUP <doctor_username>: retrieves doctor's availability; hospital server -> appointment server
            elif command[0] == "lookup" and len(command) >= 2:
                doc_name = command[1]
                lookup_d_response, lookup_d_port = stream_client("lookup_d", (username, doc_name))
                d_list = [t for t in lookup_d_response.split(',') if t]
                
                if len(d_list) == 8:
                    print(f"The client received the response from the hospital server using TCP over port {lookup_d_port}.")
                    print(f"\nAll time blocks are available for {doc_name}.")
                elif len(d_list) == 0:
                    print(f"The client received the response from the Hospital Server using TCP over port {lookup_d_port}.")
                    print(f"\n{doc_name} has no time slots available.")
                else:
                    print(f"The client received the response from the Hospital Server using TCP over port {lookup_d_port}.")
                    print(f"\n{doc_name} is available at times:")
                    for time in d_list:
                        print(time)

            elif command[0] == "schedule":
                doc_name, block_period, illness = command[1], command[2], command[3]
                schedule_response, schedule_port = stream_client("schedule", (username, doc_name, block_period, illness))
                print(f"The client received the response from the Hospital Server using TCP over port {schedule_port}")
                if schedule_response.split(',')[0] == "SUCCESS":
                    print(f"\nAn appointment has been successfully scheduled for patient {username} with {doc_name} at {block_period}.")
                elif schedule_response.split(',')[0] == "FAILURE_no":
                    print(f"\nUnable to schedule an appointment with {doc_name} at this time, as all time blocks have been taken up.")
                elif schedule_response.split(',')[0] == "FAILURE_yes":
                    print(f"Unable to schedule an appointment with {doc_name} at {block_period}. Other available time blocks are")
                    other_times = [t for t in schedule_response.split(',') if t and t != "FAILURE_yes"]
                    for time in other_times:
                        print(time)


    else:
        print("The credentials are incorrect. Please try again.")

if __name__ == "__main__":
    main()