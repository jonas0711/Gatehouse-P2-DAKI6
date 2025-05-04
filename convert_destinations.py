import json  # Importerer json-modul til at læse destinations.json
import sqlite3  # Importerer sqlite3-modul til at arbejde med SQLite-databasen
import os  # Importerer os-modul til at tjekke om filer findes

# --- Trin 1: Indlæs destinations.json og lav opslagstabel ---

# Åbner og læser destinations.json
with open('destinations.json', 'r', encoding='utf-8') as f:
    destinations_data = json.load(f)

# Opretter et opslag (dictionary) hvor alle alternative navne peger på det standardiserede navn
# Vi bruger lower() for at gøre opslaget case-insensitive
altname_to_standard = {}
for standard, alternativer in destinations_data.items():
    for alt in alternativer:
        altname_to_standard[alt.strip().lower()] = standard

# --- Trin 2: Forbind til ais.db og hent alle skibstabeller ---

db_path = 'ais.db'  # Sti til databasen
if not os.path.exists(db_path):
    print(f"Databasefilen '{db_path}' blev ikke fundet. Scriptet stopper.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Henter alle tabelnavne fra Ships-tabellen
cursor.execute("SELECT table_name FROM Ships")
ship_tables = [row[0] for row in cursor.fetchall()]
print(f"Antal skibstabeller fundet: {len(ship_tables)}")

# --- Trin 3: Gennemgå hver skibstabel og opdater destinationer ---

for table in ship_tables:
    print(f"Behandler tabel: {table}")
    # Henter alle rækker med Destination
    cursor.execute(f"SELECT rowid, Destination FROM {table}")
    rows = cursor.fetchall()
    updates = []  # Liste til at gemme opdateringer
    for rowid, dest in rows:
        if dest is None:
            continue  # Springer tomme destinationer over
        dest_key = dest.strip().lower()
        # Finder standardnavn hvis muligt
        standard = altname_to_standard.get(dest_key, None)
        if standard is not None and dest != standard:
            updates.append((standard, rowid))
        elif standard is None and dest != "Unknown":
            updates.append(("Unknown", rowid))
    # Udfører batch-opdatering for tabellen
    if updates:
        print(f"Opdaterer {len(updates)} destinationer i {table}")
        cursor.executemany(f"UPDATE {table} SET Destination = ? WHERE rowid = ?", updates)
        conn.commit()
    else:
        print(f"Ingen opdateringer nødvendige i {table}")

# --- Trin 4: Afslut ---
print("Alle destinationer er nu konverteret til standardnavne.")
conn.close() 