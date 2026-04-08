import socket
import sys

HOST = "127.0.0.1"
PORT = 23214


def handle_lookup():
    # collect all doctor names
    all_doctors = []
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
                all_doctors.append(line.split()[0])

    # check appointments.txt for doctors with at least one available slot 
    available_doctors = []
    with open("appointments.txt", "r") as f:
        current_doctor = None
        has_free_slot = False
        for line in f:
            line = line.strip()
            if not line:  # blank line between doctors
                if current_doctor and has_free_slot:
                    available_doctors.append(current_doctor)
                current_doctor = None
                has_free_slot = False
                continue
            if line in all_doctors:  # it's a doctor name
                current_doctor = line
                has_free_slot = False
            elif ":" in line and len(line.split()) == 1:
                # only a time with nothing after it = free slot
                has_free_slot = True
        
        # catch the last doctor in file (no trailing blank line)
        if current_doctor and has_free_slot:
            available_doctors.append(current_doctor)

    return ";".join(available_doctors) + ";"

def handle_lookup_d(doc_name:str):
    found_doc = False
    avail_times = []
    with open("appointments.txt", "r") as f:
        for line in f:
            if line.strip() == doc_name:
                found_doc = True
                continue
            if found_doc:
                if line.strip() and line.strip() != doc_name and "Dr." in line.strip():
                    break
                line_split = line.strip().split()
                if len(line_split) == 1:
                    avail_times.append(line_split[0])
    if found_doc:
        if len(avail_times) == 0:
            print(f"{doc_name} has no time slots available.")
        elif len(avail_times) == 8:
            print(f"All time blocks are available for {doc_name}.")
        else:
            print(f"{doc_name} has some time slots available.")
        return ",".join(avail_times)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
        sockfd.bind((HOST, PORT))
        print(f"Appointment Server is up and running using UDP on port {PORT}.")
        try:
            while True:
                data, addr = sockfd.recvfrom(4096)
                data = data.decode()

                if data.strip().split(',')[0] == "LOOKUP":
                    print("The Appointment Server has received a doctor availability request.")
                    sockfd.sendto(handle_lookup().encode(), addr)
                    print("The Appointment Server has sent the lookup result to the Hospital Server.")
                elif data.strip().split(',')[0] == "LOOKUP_D":
                    print("The Appointment Server has received a doctor availability request.")
                    sockfd.sendto(handle_lookup_d(data.strip().split(',')[1]).encode(), addr)
                    print("The Appointment Server has sent the lookup result to the Hospital Server.")
    
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
        except OSError as e:
            print(f"Server error: {e}")
            sockfd.close()
            sys.exit(1)

if __name__ == "__main__":
    main()