import socket
import sys

HOST = "127.0.0.1"
PORT = 21214

def check_users(username:str, password:str):
    with open("users.txt", "r") as f:
        for line in f: 
            parts = line.strip().split()
            if parts[0] == username and parts[1] == password:
                return True
        return False 

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
        sockfd.bind((HOST, PORT))
        sockfd.settimeout(1.0)
        print(f"Authentication Server is up and running using UDP on port {PORT}.")
        try:
            while True:
                try:
                    data, addr = sockfd.recvfrom(1024)
                except socket.timeout:
                    continue
                data = data.decode()
                username, password = data.split(',')[1], data.split(',')[2]
                print(f"Authentication Server has received an authentication request for a user with hash suffix: {username[-5:]}.")
                if check_users(username, password):
                    print(f"Authentication succeeded for a user with hash suffix: {username[-5:]}.")
                    sockfd.sendto(b"SUCCESS", addr)
                else:
                    print(f"Authentication failed for a user with hash suffix: {username[-5:]}.")
                    sockfd.sendto(b"FAIL", addr)
                print("The Authentication Server has sent the authentication result to the Hospital Server.")

        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
        except OSError as e:
            print(f"Server error: {e}")
            sockfd.close()
            sys.exit(1)

if __name__ == "__main__":
    main() 
