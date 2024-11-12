import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load and preprocess the data
data = pd.read_csv('mtr_data_enriched_cleaned.csv')

# Clean up 'Latency' column: remove non-numeric characters and convert to numeric
data['Latency'] = data['Latency'].replace(r'[^\d.]', '', regex=True)
data['Latency'] = pd.to_numeric(data['Latency'], errors='coerce')

# Drop rows with invalid latencies or 0.0 ms
data = data.dropna(subset=['Latency'])
data = data[data['Latency'] > 0.0]

# Convert 'Timestamp' to datetime format and extract Hour
data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
data['Hour'] = data['Timestamp'].dt.hour

# Ensure 'Hop Number' is numeric
data['Hop Number'] = pd.to_numeric(data['Hop Number'], errors='coerce')
data = data.dropna(subset=['Hop Number'])  # Drop rows with invalid hop numbers
data['Hop Number'] = data['Hop Number'].astype(int)  # Convert to integer after cleaning

# Get unique target IPs for analysis
unique_target_ips = data['Target IP'].unique()

# Initialize dictionary to store analysis results
results = {
    'latency_distribution': {},
    'mean_latency_by_hour': {},
    'hop_count': {},
    'latency_per_hop': {},
    'time_series': {}
}

# Loop through each target IP for detailed analysis
for target_ip in unique_target_ips:
    # Filter data for this specific Target IP
    filtered_data = data[data['Target IP'] == target_ip]

    # 1. Latency Distribution for each Target IP
    results['latency_distribution'][target_ip] = filtered_data['Latency']

    # 2. Mean Latency by Hour (Time-of-Day Analysis)
    results['mean_latency_by_hour'][target_ip] = filtered_data.groupby('Hour')['Latency'].mean()

    # 3. Hop Count Analysis
    # Calculate the average hop count per target IP (by averaging the 'Hop Number')
    hop_data = filtered_data.groupby('Timestamp')['Hop Number'].max()  # Max Hop Number per Timestamp
    results['hop_count'][target_ip] = hop_data.mean()  # Average hop count for this target IP

    # 4. Latency per Hop Analysis (Average Latency by Hop Number)
    latency_per_hop = filtered_data.groupby('Hop Number')['Latency'].mean()
    results['latency_per_hop'][target_ip] = latency_per_hop

    # 5. Time Series Analysis (Resample by Hour and calculate mean Latency)
    time_series = filtered_data.set_index('Timestamp').resample('H')[
        'Latency'].mean()  # Resample hourly and compute mean latency
    results['time_series'][target_ip] = time_series

# --- Visualization ---

# 1. Plot Latency Distribution per Target IP
plt.figure(figsize=(10, 6))
for target_ip in unique_target_ips:
    sns.histplot(results['latency_distribution'][target_ip], kde=True, label=target_ip, bins=20)
plt.xlabel('Latency (ms)')
plt.ylabel('Frequency')
plt.title('Latency Distribution for Each Target IP')
plt.legend(title='Target IP')
plt.grid(True)
plt.show()

# 3. Plot Average Number of Hops per Target IP
plt.figure(figsize=(10, 6))
hop_counts = [results['hop_count'][ip] for ip in unique_target_ips]
plt.bar(unique_target_ips, hop_counts)
plt.xlabel('Target IP')
plt.ylabel('Average Hop Count')
plt.title('Average Hop Count for Each Target IP')
plt.xticks(rotation=45)
plt.grid(True)
plt.show()


