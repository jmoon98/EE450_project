import socket
import sys

HOST = "127.0.0.1"
PORT = 22214

def handle_prescription(doc_name:str, hash_user:str, treatment:str, frequency:str):
    with open("prescriptions.txt", "a") as f:
        f.write(f"{doc_name} {hash_user} {treatment} {frequency}\n")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
        sockfd.bind((HOST, PORT))
        print(f"Prescription Server is up and running using UDP on port {PORT}.")

        try:
            while True:
                data, addr = sockfd.recvfrom(4096)
                data = data.decode()

                if data.strip().split(',')[0] == "PRESCRIBE":
                    doc_name, hash_user, treatment, frequency = data.strip().split(',')[1], data.strip().split(',')[2], data.strip().split(',')[3], data.strip().split(',')[4]
                    print(f"Prescription Server has received a request from {doc_name} to prescribe the user with hash suffix {hash_user[-5:]}.")

                    handle_prescription(doc_name, hash_user, treatment, frequency)

                    print(f"Successfully saved the prescription details for user with hash suffix: {hash_user[-5:]}.")
                    sockfd.sendto(f"SUCCESS,{treatment}".encode(), addr)

        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
        except OSError as e:
            print(f"Server error: {e}")
            sockfd.close()
            sys.exit(1)