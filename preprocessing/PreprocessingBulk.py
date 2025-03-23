# Har AIS data fra den 10-03-2025 til den 20-03-2025
import pandas as pd
import SQLSystem as sql

from sklearn.preprocessing import OrdinalEncoder

def main():
    preprocess("preprocessing/AIS/aisdk-2025-03-10/aisdk-2025-03-10.csv")
    #preprocess("preprocessing/test.csv")

def preprocess(csv_file_path):
    #----------------------------------#
    #-------normal preprocessing-------#
    #----------------------------------#
    
    print("loading csv")
    data = pd.read_csv(csv_file_path)
    
    #ordinal encoding for the values that only have a few options (mby use on cargo type or destination)
    type_of_mobile_enc = OrdinalEncoder()
    ship_type_enc = OrdinalEncoder()
    type_of_position_fixing_device_enc = OrdinalEncoder()
    data_source_type_enc = OrdinalEncoder()
    
    print("Encoding: Type of mobile")
    data["Type of mobile"] = type_of_mobile_enc.fit_transform(data[["Type of mobile"]])
    
    print("Encoding: Ship type")
    data["Ship type"] = ship_type_enc.fit_transform(data[["Ship type"]])
    
    print("Encoding: Type of position fixing device")
    data["Type of position fixing device"] = type_of_position_fixing_device_enc.fit_transform(data[["Type of position fixing device"]])
    
    print("Encoding: source type")
    data["Data source type"] = data_source_type_enc.fit_transform(data[["Data source type"]])
    

    #-----------------------------------------------------------------------------------------#
    #-------converting to sql database and removing duplicates in the following section-------#
    #-----------------------------------------------------------------------------------------#
    database = sql.create_connection("preprocessing/ais.db")
    
    sql.execute_query(database, """CREATE TABLE IF NOT EXISTS Ships (
        table_name TEXT NOT NULL UNIQUE);""")
    
    #Get a list of unique MMSI
    print("finding all ships")
    unique_mmsi = data["MMSI"].unique()
    
    #Prepare data for bulk inserts
    print("preparing ships")
    ship_inserts = [(f"ship_{mmsi}",) for mmsi in unique_mmsi]
    
    #Bulk insert into Ships table (insert all ship table names at once)
    print("inserting ships into sql database")
    sql.execute_query(database, """INSERT OR IGNORE INTO Ships (table_name) VALUES (?);""", ship_inserts)
    
    #The following is for bulk inserting the values into the sql database
    #Loop through unique MMSI and create ship tables if necessary
    for mmsi in unique_mmsi:
        sql.execute_query(database, 
            f"""CREATE TABLE IF NOT EXISTS ship_{mmsi} (
                Timestamp DATETIME NOT NULL,
                Type_of_mobile SMALLINT,
                Latitude FLOAT,
                Longitude FLOAT,
                Navigational_status TEXT,
                ROT FLOAT,
                SOG FLOAT,
                COG FLOAT,
                Heading FLOAT,
                IMO TEXT,
                Callsign TEXT,
                Name TEXT,
                Ship_type SMALLINT,
                Cargo_type TEXT,
                Width FLOAT,
                Length FLOAT,
                Type_of_position_fixing_device SMALLINT,
                Draught TEXT,
                Destination TEXT,
                ETA DATETIME,
                Data_source_type SMALLINT,
                A FLOAT,
                B FLOAT,
                C FLOAT,
                D FLOAT,
                UNIQUE(Timestamp));""")
    
    number_of_rows = data.shape[0]
    
    #Prepare data for bulk inserts into the ship tables
    rows_to_insert = {mmsi: [] for mmsi in unique_mmsi}
    for index, row in data.iterrows():
        print(f"progress: {index} / {number_of_rows}")
        if pd.notna(row["MMSI"]) and row["MMSI"] != "":
            rows_to_insert[row["MMSI"]].append((
                convert_to_datetime(row["Timestamp"]),
                handle_number(row["Type of mobile"]),
                handle_number(row["Latitude"]),
                handle_number(row["Longitude"]),
                handle_text(row["Navigational status"]),
                handle_number(row["ROT"]),
                handle_number(row["SOG"]),
                handle_number(row["COG"]),
                handle_number(row["Heading"]),
                handle_text(row["IMO"]),
                handle_text(row["Callsign"]),
                handle_text(row["Name"]),
                handle_number(row["Ship type"]),
                handle_text(row["Cargo type"]),
                handle_number(row["Width"]),
                handle_number(row["Length"]),
                handle_number(row["Type of position fixing device"]),
                handle_number(row["Draught"]),
                handle_text(row["Destination"]),
                convert_to_datetime(row["ETA"]),
                handle_number(row["Data source type"]),
                handle_number(row["A"]),
                handle_number(row["B"]),
                handle_number(row["C"]),
                handle_number(row["D"])
            ))

    print("inserting into sql database")
    #Bulk insert into the corresponding ship tables
    number_of_ships = unique_mmsi.shape[0]
    index = 0
     # Loop to bulk insert into ship tables
    for mmsi in unique_mmsi:
        print(f"progress sql: {index} / {number_of_ships}")
        index += 1
        # Create the table name dynamically
        table_name = f"ship_{mmsi}"
        
        # Get rows for the current MMSI from the dictionary
        ship_rows = rows_to_insert.get(mmsi, [])
        
        # Skip if there are no rows for the current ship
        if not ship_rows:
            continue
        
        # Build the insert query with the dynamic table name
        insert_query = f"""
        INSERT OR IGNORE INTO {table_name} (
            Timestamp, Type_of_mobile, Latitude, Longitude, Navigational_status,
            ROT, SOG, COG, Heading, IMO, Callsign, Name, Ship_type, Cargo_type, Width,
            Length, Type_of_position_fixing_device, Draught, Destination, ETA, Data_source_type,
            A, B, C, D
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        # Insert the rows into the dynamic table
        sql.execute_query(database, insert_query, ship_rows)
    
    
    #To print the encoder categories at the end
    print("finished creating database")
    print(f"Type of mobile categories: {type_of_mobile_enc.categories_}")
    print(f"Ship type categories: {ship_type_enc.categories_}")
    print(f"Type of position fixing device categories: {type_of_position_fixing_device_enc.categories_}")
    print(f"Data source type categories: {data_source_type_enc.categories_}")
    
#converts the timestamp format from DD/MM/YYYY HH:MM:SS to YYYY-MM-DD HH:MM:SS, so that sql can understand it
def convert_to_datetime(text: str) -> str:
    if pd.notna(text):
        text_bits = text.split(" ")
        year_day_month = text_bits[0].split("/")
        return f"'{year_day_month[2]}-{year_day_month[1]}-{year_day_month[0]} {text_bits[1]}'"
    else:
        return "'NULL'"
    
#makes sure NULL appears in the table if 
def handle_number(number):
    if pd.notna(number):
        return number
    else:
        return "'NULL'"

#makes sure the text values have '' so sql can understand them, and turnes single ' into '', so that sql dosent think it is the end of the string (some names have ' in them)
def handle_text(text: str) -> str:
    if pd.notna(text):
        return f"'{text.replace("'", "''")}'"
    else:
        return "'Null'"
    
  
    
if __name__ == "__main__":
    main()
