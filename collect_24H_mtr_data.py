import subprocess
import time
from datetime import datetime, timedelta

# Load all YouTube IPs
with open("youtube_ipv4.txt", "r") as file:
    target_ips = [line.strip() for line in file if line.strip()]


# run MTR and capture output
def run_mtr(ip):
    try:
        command = ["sudo", "/usr/local/sbin/mtr", "-T", "-c", "5", "-r", ip]
        result = subprocess.run(command, capture_output=True, text=True)
        result.check_returncode()  # Raise exception if the command failed
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] MTR failed for IP {ip}: {result.stderr.strip()}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error occurred for IP {ip}: {e}")
        return None


# To run every 30 minutes and stop after 24 hours
def collect_data(interval=1800, duration=86400):
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=duration)
    print(f"[INFO] Data collection started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] Scheduled to end at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    with open("mtr_data.csv", "a") as f:
        f.write("Timestamp,Target IP,Hop Number,Hop IP,Latency\n")

        while datetime.now() < end_time:
            cycle_start_time = datetime.now()
            timestamp = cycle_start_time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[INFO] Cycle started at {timestamp}. Running MTR for target IPs...")

            # run MTR for each target IP
            for ip in target_ips:
                print(f"[INFO] Running MTR for IP: {ip}")
                output = run_mtr(ip)
                if output is None:
                    continue

                # Parse MTR output to extract hop data
                lines = output.strip().split("\n")
                if not lines:
                    continue

                # Process each line, starting from the second one to skip the header
                for line in lines[1:]:
                    fields = line.split()
                    if len(fields) < 8:
                        continue  # skip weird lines

                    # Extract hop number, hop IP, and avg latency
                    hop_number = fields[0].replace(".|--", "").replace(".", "").strip()  # Clean hop number
                    hop_ip = fields[1] if fields[1] != "???" else "???"
                    latency = fields[4] + " ms"  # extract avg latency

                    # write parsed data to the CSV file with timestamp
                    f.write(f"{timestamp},{ip},{hop_number},{hop_ip},{latency}\n")

            # calc time to wait until the next cycle starts
            next_cycle_start = cycle_start_time + timedelta(seconds=interval)
            remaining_wait_time = (next_cycle_start - datetime.now()).total_seconds()
            if remaining_wait_time > 0:
                print(
                    f"[INFO] Waiting {remaining_wait_time // 60:.0f} minutes and {remaining_wait_time % 60:.0f} seconds until the next cycle.")
                time.sleep(remaining_wait_time)

    print(f"[INFO] Data collection finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


collect_data()
