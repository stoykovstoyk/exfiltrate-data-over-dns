import threading
import base64
import argparse
from datetime import datetime
from dnslib import DNSRecord, QTYPE, RR, A
from dnslib.server import DNSServer, BaseResolver, DNSLogger

# Function to log DNS queries to both the console and server.log
def log_request(current_time, source_ip, query_type, qname, interaction_id):
    if source_ip != '127.0.0.1':
        # Format the log message to match the required format
        log_message = f"{current_time} : Received DNS query with type {query_type} from [{source_ip}] for [{qname}] containing interaction IDs: {interaction_id}\n"

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
        # Get the current date and time with milliseconds
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Get the source IP address
        source_ip = handler.client_address[0]

        qname = str(request.q.qname).strip(".")
        qtype = QTYPE[request.q.qtype]

        labels = qname.split('.')

        # Determine the interaction ID as the label immediately before 'pingns'
        if "pingns" in labels:
            pingns_index = labels.index("pingns")
            if pingns_index > 0:
                interaction_id = labels[pingns_index - 1]  # Take the label before 'pingns'
            else:
                interaction_id = "unknown"
        else:
            interaction_id = "unknown"

        # Log the DNS query with timestamp, source IP, query type, and interaction ID
        log_request(current_time, source_ip, qtype, qname, interaction_id)

        # Return a fake non-existing IP address as a response (e.g., 0.0.0.0)
        reply = request.reply()
        reply.add_answer(RR(qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=300))
        return reply

    def decode_and_print(self, unique_id):
        base64_data = ''.join(self.chunks.get(unique_id, []))
        try:
            decoded_data = base64.b64decode(base64_data).decode('utf-8')
            log_request(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], "127.0.0.1", "A", f"Decoded command for {unique_id}", unique_id)
            # Clear the stored chunks for this unique ID
            del self.chunks[unique_id]
        except Exception as e:
            log_request(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], "127.0.0.1", "A", f"Failed to decode command for {unique_id}", unique_id)

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
