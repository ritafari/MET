import pandas as pd
import requests
import csv
import socket
import whois
import time

API_TOKEN = "eb0270c9b16892"
API_URL = "http://ipinfo.io/{}/json?token=" + API_TOKEN


def get_ip_info(ip):
    url = API_URL.format(ip)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to retrieve info: {response.status_code}"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


def get_ip_from_hostname(hostname):
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        return None


def truncate_to_domain(hostname):
    parts = hostname.split(".")
    if len(parts) > 2:
        return ".".join(parts[-2:])
    return hostname


def get_whois_info(domain):
    try:
        w = whois.whois(domain)
        return w
    except Exception as e:
        return {"error": "WHOIS lookup failed"}



mtr_data = pd.read_csv("mtr_data.csv")

# unique IPs/hostnames from both Hop IP and Target IP columns
unique_hosts = pd.concat([mtr_data["Hop IP"].dropna(), mtr_data["Target IP"].dropna()]).unique()
unique_hosts = [host for host in unique_hosts if host != "???"]


ip_info_dict = {}

print("Starting IP/hostname lookup...")
for host in unique_hosts:
    print(f"Processing: {host}")

    # attempt to resolve IP if the host is a hostname
    ip = get_ip_from_hostname(host) if not host.replace('.', '').isdigit() else host

    if ip is None:
        # if IP lookup fails, attempt a WHOIS lookup for the truncated domain
        truncated_domain = truncate_to_domain(host)
        print(f"Attempting WHOIS lookup for domain: {truncated_domain}")
        whois_info = get_whois_info(truncated_domain)
        ip_info_dict[host] = {"error": whois_info.get("error", ""), "WHOIS": whois_info}
    else:
        # get IP info from ipinfo.io
        ip_info = get_ip_info(ip)
        ip_info_dict[host] = ip_info
    time.sleep(2)  # delay to avoid rate-limiting

# save the IP info to ip_info.csv
output_file = "ip_info.csv"
with open(output_file, "w", newline="") as csvfile:
    fieldnames = ["Host/IP", "Resolved IP", "Hostname", "City", "Region", "Country", "Org", "Error", "WHOIS"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for host, info in ip_info_dict.items():
        row = {
            "Host/IP": host,
            "Resolved IP": info.get("ip", "N/A") if "error" not in info else "N/A",
            "Hostname": info.get("hostname", "N/A"),
            "City": info.get("city", "N/A"),
            "Region": info.get("region", "N/A"),
            "Country": info.get("country", "N/A"),
            "Org": info.get("org", "N/A"),
            "Error": info.get("error", ""),
            "WHOIS": info.get("WHOIS", "")
        }
        writer.writerow(row)

print(f"IP and hostname information saved to {output_file}")
