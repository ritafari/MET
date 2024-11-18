import pandas as pd
import matplotlib.pyplot as plt
import re

# Load the data
mtr_data = pd.read_csv("mtr_data_enriched_cleaned.csv")

# Clean the Latency column by removing non-numeric values and converting to float
def clean_latency(value):
    try:
        # Remove non-numeric characters and convert to float
        return float(re.sub(r'[^\d.]', '', str(value)))
    except ValueError:
        # Return NaN if conversion fails
        return None

mtr_data['Cleaned_Latency'] = mtr_data['Latency'].apply(clean_latency)

# Drop NaN values from the cleaned column to focus on numeric latency values
mtr_data_cleaned = mtr_data.dropna(subset=['Cleaned_Latency'])

# Get the statistical values
Q1 = mtr_data_cleaned['Cleaned_Latency'].quantile(0.25)
median = mtr_data_cleaned['Cleaned_Latency'].median()
Q3 = mtr_data_cleaned['Cleaned_Latency'].quantile(0.75)


plt.figure(figsize=(10, 6))
plt.boxplot(mtr_data_cleaned['Cleaned_Latency'], patch_artist=True)
plt.title("Box Plot of Latency Values (Uncleaned Data)")
plt.ylabel("Latency (ms)")
plt.grid(True)

# Annotate the Q1, median, and Q3 values
plt.text(1.15, -200, f'Q1 = {Q1:.2f}', va='center', color='blue')
plt.text(1.15, median, f'Median = {median:.2f}', va='center', color='green')
plt.text(1.15, 250, f'Q3 = {Q3:.2f}', va='center', color='purple')

plt.xlim(0.5, 1.5)

plt.show()
