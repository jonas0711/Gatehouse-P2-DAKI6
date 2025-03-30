import os
import json
import pandas as pd
from tqdm import tqdm
import time
import psutil
from datetime import datetime

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

print(f"[{datetime.now()}] Starting script...")
start_time = time.time()

# Sti til json-fil med destination mapping
json_path = "destinations.json"

# Sti til mappe med CSV-filer
csv_folder = r"C:\Users\jonas\Desktop\Design og anvendelse af kunstig inteligens\2. Semester\Projekt - Gatehouse\AIS"

# Indlæs destinations-mapping
with open(json_path, "r", encoding="utf-8") as file:
    destination_dict = json.load(file)

# Opret en "reverse lookup", så vi hurtigt kan finde hovednavnet ud fra en værdi
destination_lookup = {}
for standard_name, aliases in destination_dict.items():
    for alias in aliases:
        destination_lookup[alias.upper()] = standard_name

print(f"[{datetime.now()}] Loaded {len(destination_lookup)} destination mappings")
print(f"Current memory usage: {get_memory_usage():.2f} MB")

# Chunk size for processing large CSV files
CHUNK_SIZE = 100000

# Gennemgå alle CSV-filer i mappen
for filename in tqdm(os.listdir(csv_folder), desc="Processing files"):
    if filename.endswith(".csv"):
        file_path = os.path.join(csv_folder, filename)
        print(f"\n[{datetime.now()}] Processing: {filename}")
        file_start_time = time.time()

        try:
            # Get file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            print(f"File size: {file_size:.2f} MB")

            # Process file in chunks
            if "Destination" in pd.read_csv(file_path, nrows=1).columns:
                chunks = []
                for chunk in tqdm(pd.read_csv(file_path, chunksize=CHUNK_SIZE), desc="Processing chunks"):
                    if "Destination" in chunk.columns:
                        chunk["Destination"] = chunk["Destination"].apply(lambda x: 
                            destination_lookup.get(str(x).upper().strip(), x) if pd.notna(x) else x)
                        chunks.append(chunk)
                    
                print(f"[{datetime.now()}] Merging chunks...")
                df = pd.concat(chunks, ignore_index=True)
                
                print(f"[{datetime.now()}] Saving file...")
                df.to_csv(file_path, index=False)
                
                processing_time = time.time() - file_start_time
                print(f"File processed in {processing_time:.2f} seconds")
                print(f"Current memory usage: {get_memory_usage():.2f} MB")
            else:
                print(f"Skipping {filename} (no 'Destination' column)")
        
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

total_time = time.time() - start_time
print(f"\n[{datetime.now()}] Script completed!")
print(f"Total execution time: {total_time:.2f} seconds")
print(f"Final memory usage: {get_memory_usage():.2f} MB")
