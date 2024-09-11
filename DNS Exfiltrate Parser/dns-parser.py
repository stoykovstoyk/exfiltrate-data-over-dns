#!/usr/bin/python3
#
# dns-parse.py v0.6
# Extracts and converts hex- or base32-encoded data exfiltrated to Bind query logs or private Burp Collaborator output
#
# Private Burp Collaborator output may be logged via 'tee':
# java -jar burpsuite_pro.jar --collaborator-server | tee collaborator.log
#
# Eric Conrad
# https://ericconrad.com
# 
# Modified by Stoyko Stoykov to handle unique data correctly
#
# Todo list:
# - Detect compressed data and automatically decompress

import re
import sys
import base64

def decode_base32(data):
    try:
        # Add padding if needed
        pad = '=' * (8 - len(data) % 8) if len(data) % 8 != 0 else ''
        data += pad
        decoded_data = base64.b32decode(data).decode('utf-8')
        return decoded_data
    except Exception as e:
        print(f'Error decoding base32 data: {e}')
        return None

def decode_hex(data):
    try:
        decoded_data = bytes.fromhex(data).decode('utf-8')
        return decoded_data
    except Exception as e:
        print(f'Error decoding hex data: {e}')
        return None

if len(sys.argv) == 3:
    dnsname = sys.argv[1]
    logname = sys.argv[2]
    seen_chunks = set()  # To keep track of unique chunks
    base32 = ''  # To accumulate final base32-encoded data
    hexadecimal = ''  # To accumulate final hex-encoded data

    with open(logname) as f:
        for line in f:
            if dnsname in line:
                # Split the line, using all non-alphanumeric characters as delimiters. The hex- or
                # base32-encoded label (DNS name) is the 13th field in a bind query log and the 19th 
                # field in a Burp Collaborator log. The 7th field can be used to distinguish bind 
                # ('client') from Burp Collaborator ('Received')
                substring = re.split('\W+', line)
                if substring[7] == 'client':  # Bind query log
                    chunk = substring[13]
                elif substring[7] == 'Received':  # Burp Collaborator log
                    chunk = substring[19]

                if chunk not in seen_chunks:
                    seen_chunks.add(chunk)
                    if re.search("^[A-Z2-7]*$", chunk.upper()):  # base32
                        base32 += chunk.upper()  # Accumulate base32 chunks
                    elif re.search("^[0-9a-f]*$", chunk):  # Hex
                        hexadecimal += chunk  # Accumulate hex chunks

    # Process and print accumulated base32 final data
    if base32:
        try:
            # Add padding if needed
            pad = '=' * (8 - len(base32) % 8) if len(base32) % 8 != 0 else ''
            base32 += pad
            decoded_data = decode_base32(base32)
            if decoded_data:
                print(decoded_data, end='')
        except Exception as e:
            print(f'Error processing accumulated base32 data: {e}')
    
    # Process and print accumulated hex final data
    if hexadecimal:
        try:
            decoded_data = decode_hex(hexadecimal)
            if decoded_data:
                print(decoded_data, end='')
        except Exception as e:
            print(f'Error processing accumulated hex data: {e}')

else:
    print(f'Usage: {sys.argv[0]} <DNS name> <log name>')
