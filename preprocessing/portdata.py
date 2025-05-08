import sqlite3
import json
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

# Connect to your SQLite database
DB_PATH = 'preprocessing/ais.db'  # Replace with your actual database path
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Step 1: Get all ship table names
cursor.execute("SELECT table_name FROM Ships")
ship_tables = [row[0] for row in cursor.fetchall()]

# Data structures for aggregation
destination_counts = Counter()
destination_ships = defaultdict(set)

# Step 2: Iterate through each ship table
for table in ship_tables:
    try:
        query = f"SELECT Destination FROM {table} WHERE Destination IS NOT NULL AND TRIM(Destination) != ''"
        cursor.execute(query)
        destinations = [row[0].strip() for row in cursor.fetchall() if row[0].strip()]

        # Count messages per destination
        destination_counts.update(destinations)

        # Record which ships have entries for each destination
        for dest in set(destinations):  # Only once per ship per destination
            destination_ships[dest].add(table)
    except Exception as e:
        print(f"Error processing table {table}: {e}")

# Step 3: Prepare data for JSON
destination_ship_list = {
    dest: list(tables) for dest, tables in destination_ships.items()
}

with open("port_ship_mapping.json", "w") as f:
    json.dump(destination_ship_list, f, indent=2)

# Step 4: Print stats to console
print(f"{'Port':<30} {'Unique Ships':<15} {'Total Messages'}")
for dest, count in destination_counts.most_common():
    print(f"{dest:<30} {len(destination_ships[dest]):<15} {count}")

# Step 5: Bar graph of top 20 ports
top_20 = destination_counts.most_common(20)
ports, message_counts = zip(*top_20)

plt.figure(figsize=(12, 6))
plt.bar(ports, message_counts, color='skyblue')
plt.xticks(rotation=45, ha='right')
plt.title("Top 20 Most Frequently Mentioned Ports")
plt.xlabel("Port")
plt.ylabel("Number of AIS Messages")
plt.tight_layout()
plt.savefig("top_20_ports.png")
plt.show()

# Cleanup
conn.close()