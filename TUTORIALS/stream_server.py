import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 12345
BACKLOG = 5

def handle_client(new_fd):
    client_msg = new_fd.recv(4096)
    client_msg = client_msg.decode()
    print(f"server received from client: {client_msg}")
    if client_msg == "poop butt":
        new_fd.send(b"butt poop")
    else:
        new_fd.send(b"roflcopter")
    new_fd.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
        sockfd.bind((HOST, PORT))
        sockfd.listen(BACKLOG)
        print(f"Listening on {HOST}:{PORT}")

        try:
            while True:
                new_fd, addr = sockfd.accept()
                thread = threading.Thread(target=handle_client, args=(new_fd,))
                thread.start()           # parent doesn't need connected socket
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
    
                
if __name__ == "__main__":
    main()