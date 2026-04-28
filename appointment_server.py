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
    
def handle_schedule(hash_usr: str, doc_name:str, block_period:str, illness:str):
    found_doc = False
    appt_failed = False
    avail_times = []

    if ':' not in block_period:
        appt_failed = True
    else:
        hr, min = block_period.split(':')
        if int(hr) < 9 or int(hr) > 16 or min != '00':
            appt_failed = True

    with open("appointments.txt", "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip() == doc_name:
            found_doc = True
            continue

        if found_doc:
            if line.strip() and "Dr." in line.strip():
                break
            line_split = line.strip().split()
            if not line_split:
                continue
            if line_split[0] == block_period:
                if len(line_split) >= 2:
                    appt_failed = True
                elif not appt_failed:
                    # logic for changing appointment.txt! 
                    lines[i] = f"{block_period} {hash_usr} {illness}\n"
                    break
            elif len(line_split) == 1:
                avail_times.append(line_split[0])
    # write everything back
    if not appt_failed:
        with open("appointments.txt", "w") as f:
            f.writelines(lines)

    if not appt_failed:
        return True, []
    else:
        return False, avail_times
                

def handle_cancel(hash_usr: str):
    found_and_canceled = False
    canceled_appt = []
    curr_doc = ""

    with open("appointments.txt", "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "Dr." in line:
            curr_doc = line.strip()
            continue
        line_entries = line.strip().split()
        if len(line_entries) > 1:
            if line_entries[1] == hash_usr:
                canceled_appt.append(curr_doc.strip())
                canceled_appt.append(line_entries[0])
                lines[i] = f"{line_entries[0]}\n"
                found_and_canceled = True
                break
    
    if found_and_canceled:
        with open("appointments.txt", "w") as f:
            f.writelines(lines)
        return True, ",".join(canceled_appt)
    return False, ""

def handle_view_appt(hash_usr: str):
    found_appt = None
    curr_doc = ""

    with open("appointments.txt", "r") as f:
        for line in f:
            if "Dr." in line:
                curr_doc = line.strip()
                continue
            line_entries = line.strip().split()
            if len(line_entries) >= 2:
                if line_entries[1] == hash_usr:
                    found_appt = line_entries
                    break
    
    if found_appt is not None:
        return True, f"SUCCESS,{curr_doc},{found_appt[0]}"
    return False, "FAILURE"

def handle_view_appts(doc_usr: str):
    doc_appts = []
    doc_found = False
    with open("appointments.txt", "r") as f:
        for line in f:
            if not doc_found and line.strip() == doc_usr:
                doc_found = True
                continue
            elif doc_found and "Dr." in line:
                break
            if doc_found:
                line_split = line.strip().split()
                if not line_split: 
                    continue
                if len(line_split) >= 2:
                    doc_appts.append(line_split[0])
    return doc_appts

def handle_find_illness(hash_usr: str):
    with open("appointments.txt", "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        cols = line.strip().split()
        if len(cols) > 1 and len(cols[1]) >= 5 and cols[1][-5:] == hash_usr:
            # retrieve associated illness value
            # then removes hashed patient identifier and illness from that time block
            # (leaving only original time entry)
            illness = cols[2]
            timeblock = cols[0]
            print(f"Sending back the requested information to the Hospital server.")
            lines[i] = f"{timeblock}\n"


    with open("appointments.txt", "w") as f:
        f.writelines(lines)
        print(f"Successfully removed {hash_usr} appointment slot, {timeblock} is now free to be scheduled for tomorrow.")

    return illness





def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
        sockfd.bind((HOST, PORT))
        sockfd.settimeout(1.0)
        print(f"Appointment Server is up and running using UDP on port {PORT}.")
        try:
            while True:
                try:
                    data, addr = sockfd.recvfrom(4096)
                except socket.timeout:
                    continue
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
                    hash_usr, doc_name, block_period, illness = data.strip().split(',')[1], data.strip().split(',')[2], data.strip().split(',')[3], data.strip().split(',')[4]
                    hash_sfx = hash_usr[-5:]
                    print(f"Appointment scheduling request received (time: {block_period}, doctor: {doc_name}, patient hash suffix: {hash_sfx}, illness: {illness}).")
                    scheduled, other_times = handle_schedule(hash_usr, doc_name, block_period, illness)
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

                elif data.strip().split(',')[0] == "CANCEL":
                    hash_usr = data.strip().split(',')[1]
                    print(f"Appointment Server has received a cancel appointment command for the user with hash suffix: {hash_usr[-5:]}.")
                    cancel_res, canceled_appt = handle_cancel(hash_usr)
                    if cancel_res:
                        print("Successfully cancelled appointment.")
                        sockfd.sendto(f"SUCCESS,{canceled_appt}".encode(), addr)
                    else:
                        print("Error: Failed to find appointment.")
                        sockfd.sendto("FAILURE".encode(), addr)

                elif data.strip().split(',')[0] == "VIEW_APPT":
                    hash_usr = data.strip().split(',')[1]
                    print(f"Appointment Server has received a view appointment command for the user with hash suffix {hash_usr[-5:]}.")
                    scheduled, msg = handle_view_appt(hash_usr)
                    if scheduled:
                        print(f"Returning details regarding the appointment for the user with hash suffix {hash_usr[-5:]}.")
                    else:
                        print(f"The user with hash suffix {hash_usr[-5:]} has no appointment in the system.")
                    sockfd.sendto(msg.encode(), addr)

                elif data.strip().split(',')[0] == "VIEW_APPTS":
                    doc_usr = data.strip().split(',')[2]
                    print(f"Appointment Server has received a request to view appointments scheduled for {doc_usr}.")
                    doc_appts = handle_view_appts(doc_usr)
                    if len(doc_appts) == 0:
                        print(f"No appointments have been made for {doc_usr}.")
                        msg = "FAILURE"
                    else:
                        print(f"Returning the scheduled appointments for {doc_usr}.")
                        msg = f"SUCCESS,{','.join(doc_appts)}"
                    sockfd.sendto(msg.encode(), addr)

                elif data.strip().split(',')[0] == "PRESCRIBE":
                    doc_name, hash_suffix = data.strip().split(',')[1], data.strip().split(',')[2]
                    print(f"Appointment Server has received a request from Hospital Server regarding information about a user with hash suffix {hash_suffix} from {doc_name}.")
                    illness = handle_find_illness(hash_suffix)
                    sockfd.sendto(illness.encode(), addr)

                    

    
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            sockfd.close()
        except OSError as e:
            print(f"Server error: {e}")
            sockfd.close()
            sys.exit(1)

if __name__ == "__main__":
    main()