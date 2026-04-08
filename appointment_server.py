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
    
def handle_schedule(doc_name:str, block_period:str, illness:str):
    found_doc = False
    time_filled = False
    avail_times = []

    hr, min = block_period.split(':')
    if int(hr) < 9 or int(hr) > 16:
        time_filled = True
    # !! will they test invalid inputs..? like having 99 for min input, etc. 
    # specs to say "must be in format HH:MM"...
    # or non-00 mins?? 
    # what if they enter an invalid time AND all times are taken up? 

    with open("appointments.txt", "r") as f:
        for line in f:
            if line.strip() == doc_name:
                found_doc = True
                continue
            if found_doc:
                if line.strip() and line.strip() != doc_name and "Dr." in line.strip():
                    break
                line_split = line.strip().split()
                if line_split[0] == block_period:
                    if len(line_split) >= 2:
                        time_filled = True
                elif line_split[0] != block_period and len(line_split) == 1:
                    avail_times.append(line_split[0])
    if not time_filled:
        return True, []
    else:
        return False, avail_times
                
    



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
                elif data.strip().split(',')[0] == "SCHEDULE":
                    hash_sfx, doc_name, block_period, illness = data.strip().split(',')[1][-5:], data.strip().split(',')[2], data.strip().split(',')[3], data.strip().split(',')[4]
                    print(f"Appointment scheduling request received (time: {block_period}, doctor: {doc_name}, patient hash suffix: {hash_sfx}, illness: {illness}).")
                    scheduled, other_times = handle_schedule(doc_name, block_period, illness)
                    if scheduled:
                        print(f"Appointment has been scheduled successfully for user {hash_sfx} with {doc_name}.")
                        sockfd.sendto("SUCCESS".encode(), addr)
                    else:
                        print("The requested appointment time is not available.")
                        other_times_str = ",".join(other_times)
                        if len(other_times) == 0:
                            message = f"FAILURE_no,{other_times_str}"
                        else:
                            message = f"FAILURE_yes,{other_times_str}"
                        sockfd.sendto(message.encode(), addr)
                        

    
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
        except OSError as e:
            print(f"Server error: {e}")
            sockfd.close()
            sys.exit(1)

if __name__ == "__main__":
    main()