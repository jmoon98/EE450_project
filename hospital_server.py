import socket
import threading
import sys

UDP_PORT = 25214
TCP_PORT = 26214 
HOST = "127.0.0.1"
BACKLOG = 5

def handle_client_connection(new_fd, addr):
    client_msg = new_fd.recv(4096).decode()  # recv blocks! 

    if client_msg.split(',')[0] == "AUTHENTICATE":
        username, password = client_msg.split(',')[1], client_msg.split(',')[2]
        print(f"Hospital Server received an authentication request from a user with hash suffix {username[-5:]}.")
        message = f"AUTHENTICATE,{username},{password}"

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            udp_sock.bind((HOST, 0))  # 0 = let OS assign dynamic port
            try: 
                udp_sock.sendto(message.encode(), (HOST, 21214))
                print("Hospital Server has sent an authentication request to the Authentication Server.")
                auth_serv_response, _ = udp_sock.recvfrom(4096)
                udp_addr = udp_sock.getsockname()[1]
                print(f"Hospital server has received the response from the authentication server using UDP over port {udp_addr}.")
                # check if doctor or patient and provide appropriate access
                is_doctor = False
                if auth_serv_response.decode() == "SUCCESS":
                    print(f"User with a hash suffix {username[-5:]} has been granted access to the system. Determining the access of the user.")
                    with open("hospital.txt", "r") as f:
                        in_doctors_section = False
                        for line in f:
                            line = line.strip()
                            if line == "[Doctors]":
                                in_doctors_section = True
                                continue
                            if line == "[Treatments]":
                                break
                            if in_doctors_section and line and not line.startswith('['):
                                parts = line.split()
                                if len(parts) >= 2 and username == parts[1]:
                                    is_doctor = True
                    if is_doctor:
                        print(f"User with hash suffix {username[-5:]} will be granted doctor access.")
                        new_fd.send(b"DOCTOR_ACCESS")
                    else:
                        print(f"User with hash {username[-5:]} will be granted patient access.")
                        new_fd.send(b"PATIENT_ACCESS")
                    tcp_port = new_fd.getsockname()[1]
                    print(f"Hospital Server has sent the response from Authentication Server to the client using TCP over port {tcp_port}.")
                else:
                    new_fd.send(auth_serv_response)
                udp_sock.close()
                new_fd.close()
            except OSError as e:
                print("socket error:", e)
                udp_sock.close()
                sys.exit(1)

    elif client_msg.split(',')[0] == "LOOKUP":
        hash_suffix = client_msg.split(',')[1][-5:]
        tcp_port = new_fd.getsockname()[1]
        print(f"Hospital Server received a lookup request from a user with a hash suffix {hash_suffix} over port {tcp_port}.")
        message = "LOOKUP"

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            udp_sock.bind((HOST, 0))  # 0 = let OS assign dynamic port
            try: 
                udp_sock.sendto(message.encode(), (HOST, 23214))
                print("Hospital Server sent the doctor lookup request to the Appointment server.")
                appt_server_response, _ = udp_sock.recvfrom(4096)
                udp_addr = udp_sock.getsockname()[1]
                print(f"Hospital Server has received the response from Appointment Server using UDP over port {udp_addr}.")
                new_fd.send(appt_server_response)
                print("Hospital Server has sent the doctor lookup to the client.")
                udp_sock.close()
                new_fd.close()
            except OSError as e:
                print("socket error:", e)
                udp_sock.close()
                sys.exit(1)

    elif client_msg.split(',')[0] == "LOOKUP_D":
        hash_suffix = client_msg.split(',')[1][-5:]
        doc_name = client_msg.split(',')[2]
        tcp_port = new_fd.getsockname()[1]
        print(f"Hospital Server has received a lookup request from a user with hash suffix {hash_suffix} to lookup {doc_name} availability using TCP over port {tcp_port}.")
        message = f"LOOKUP_D,{doc_name}"

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            udp_sock.bind((HOST, 0))  # 0 = let OS assign dynamic port
            try: 
                udp_sock.sendto(message.encode(), (HOST, 23214))
                print("Hospital Server sent the doctor lookup request to the Appointment server.")
                appt_server_response, _ = udp_sock.recvfrom(4096)
                udp_port = udp_sock.getsockname()[1]
                print(f"Hospital Server has received the response from Appointment Server using UDP over port {udp_port}.")
                new_fd.send(appt_server_response)
                print("The Hospital Server has sent the response to the client.")
                udp_sock.close()
                new_fd.close() 
            except OSError as e:
                print("socket error:", e)
                udp_sock.close()
                sys.exit(1)
        
    elif client_msg.split(',')[0] == "SCHEDULE":
        tcp_port = new_fd.getsockname()[1]
        print(f"Hospital Server has received a schedule request from a user with hash suffix: {client_msg.split(',')[1][-5:]} to book an appointment using TCP over port {tcp_port}.")
        message = client_msg

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            udp_sock.bind((HOST, 0))
            try:
                udp_sock.sendto(message.encode(), (HOST, 23214))
                print("Hospital Server has sent the schedule request to the appointment server.")
                appt_server_response, _ = udp_sock.recvfrom(4096)
                udp_port = udp_sock.getsockname()[1]
                print(f"Hospital Server has received the response from Appointment Server using UDP over {udp_port}.")
                new_fd.send(appt_server_response)
                print("The hospital server has sent the response to the client.")
                udp_sock.close()
                new_fd.close() 
            except OSError as e:
                print("socket error:", e)
                udp_sock.close()
                sys.exit(1)


        '''
        with open("hospital.txt", "r") as f:
            doctors_list = ""
            in_doctors_section = False
            for line in f:
                line = line.strip()
                if line == "[Doctors]":
                    in_doctors_section = True
                    continue
                elif line == "[Treatments]":
                    break
                if in_doctors_section and line and not line.startswith('['):
                    doctors_list += f"{line.split()[0]};"
        new_fd.send(doctors_list.encode())
        '''
        


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
        sockfd.bind((HOST, TCP_PORT))
        sockfd.listen(BACKLOG)
        print(f"Hospital Server is up and running using UDP on port {UDP_PORT}.")
        try:
            while True:
                new_fd, addr = sockfd.accept()
                thread = threading.Thread(target=handle_client_connection, args=(new_fd, addr))
                thread.start() 

        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()


if __name__ == "__main__":
    main()
