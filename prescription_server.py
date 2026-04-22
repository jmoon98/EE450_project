import socket
import sys

HOST = "127.0.0.1"
PORT = 22214

def handle_prescription(doc_name:str, hash_user:str, treatment:str, frequency:str):
    with open("prescriptions.txt", "a") as f:
        f.write(f"{doc_name} {hash_user} {treatment} {frequency}\n")

def handle_view_presc(patient_hash:str):
    with open("prescriptions.txt", "r") as f:
        for line in f:
            cols = line.strip().split()
            if cols[1] == patient_hash:
                return [cols[0], cols[2], cols[3]]
        
        return []


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

                elif data.strip().split(',')[0] == "VIEW_P":
                    patient_hash = data.strip().split(',')[1]
                    print(f"The prescription server has received a request to view the prescription for the user with hash suffix: {patient_hash[-5:]}.")

                    presc = handle_view_presc(patient_hash)

                    if len(presc) == 0:
                        print(f"There are no current prescriptions for this user.")
                        sockfd.sendto("FAILURE".encode(), addr)
                    else:
                        print(f"A prescription exists for this user.")
                        sockfd.sendto(",".join(presc).encode(), addr)



                

        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
        except OSError as e:
            print(f"Server error: {e}")
            sockfd.close()
            sys.exit(1)