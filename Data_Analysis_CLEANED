
# To plot Top Hops by Frequency
if enriched_data['Hop IP'].notna().sum() > 0:
    top_hops = enriched_data['Hop IP'].value_counts().head(10)
    if not top_hops.empty:
        plt.figure(figsize=(10, 6))
        ax = top_hops.plot(kind='bar', color='skyblue')
        plt.title('Top 10 Most Frequent Hops')
        plt.xlabel('Hop IP')
        plt.ylabel('Frequency')
        plt.xticks(rotation=45)

        # unknown if org is missing
        for i, (ip, count) in enumerate(top_hops.items()):
            org = enriched_data[enriched_data['Hop IP'] == ip]['Org'].iloc[0] if pd.notna(
                enriched_data[enriched_data['Hop IP'] == ip]['Org'].iloc[0]) else "Unknown"
            ax.annotate(org, (i, count), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8)

        plt.savefig("top_10_most_frequent_hops2.png")
    else:
        print("No data available for 'Top 10 Most Frequent Hops' plot.")

# Group by hour and count the number of hops per hour
hops_per_hour = enriched_data.groupby('Hour')['Hop Number'].count()

# Plot the number of hops per hour
plt.figure(figsize=(10, 6))
hops_per_hour.plot(kind='bar', color='skyblue')
plt.title('Number of Hops Recorded per Hour')
plt.xlabel('Hour of Day (0 = Midnight, 23 = 11 PM)')
plt.ylabel('Number of Hops')
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig("hops_per_hour.png")

print("Done")
