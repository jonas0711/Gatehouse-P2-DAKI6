# Har AIS data fra den 10-03-2025 til den 20-03-2025
import pandas as pd
import SQLSystem as sql
import numpy as np

from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer

def main():
    #preprocess("preprocessing/AIS/aisdk-2025-03-10/aisdk-2025-03-10.csv")
    preprocess("preprocessing/test.csv")

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
    
    #replace nan values with a constant value. in this case 'NULL'
    nan_fill_imputer = SimpleImputer(strategy="constant", missing_values = np.nan, fill_value = "'NULL'") 
    
    print("converting number formats step 1 / 17")
    handle_number_column(nan_fill_imputer, data, "Type of mobile")
    print("converting number formats step 2 / 17")
    handle_number_column(nan_fill_imputer, data, "Latitude")
    print("converting number formats step 3 / 17")
    handle_number_column(nan_fill_imputer, data, "Longitude")
    print("converting number formats step 4 / 17")
    handle_number_column(nan_fill_imputer, data, "ROT")
    print("converting number formats step 5 / 17")
    handle_number_column(nan_fill_imputer, data, "SOG")
    print("converting number formats step 6 / 17")
    handle_number_column(nan_fill_imputer, data, "COG")
    print("converting number formats step 7 / 17")
    handle_number_column(nan_fill_imputer, data, "Heading")
    print("converting number formats step 8 / 17")
    handle_number_column(nan_fill_imputer, data, "Ship type")
    print("converting number formats step 9 / 17")
    handle_number_column(nan_fill_imputer, data, "Width")
    print("converting number formats step 10 / 17")
    handle_number_column(nan_fill_imputer, data, "Length")
    print("converting number formats step 11 / 17")
    handle_number_column(nan_fill_imputer, data, "Type of position fixing device")
    print("converting number formats step 12 / 17")
    handle_number_column(nan_fill_imputer, data, "Draught")
    print("converting number formats step 13 / 17")
    handle_number_column(nan_fill_imputer, data, "Data source type")
    print("converting number formats step 14 / 17")
    handle_number_column(nan_fill_imputer, data, "A")
    print("converting number formats step 15 / 17")
    handle_number_column(nan_fill_imputer, data, "B")
    print("converting number formats step 16 / 17")
    handle_number_column(nan_fill_imputer, data, "C")
    print("converting number formats step 17 / 17")
    handle_number_column(nan_fill_imputer, data, "D")
    
    print("converting text formats step 1 / 5")
    handle_text_column(data, "Navigational status")
    print("converting text formats step 2 / 5")
    handle_text_column(data, "IMO")
    print("converting text formats step 3 / 5")
    handle_text_column(data, "Callsign")
    print("converting text formats step 4 / 5")
    handle_text_column(data, "Cargo type")
    print("converting text formats step 5 / 5")
    handle_text_column(data, "Destination")
    
    print("converting dateTime formats step 1 / 2")
    handle_datetime(data, "Timestamp")
    print("converting dateTime formats step 2 / 2")
    handle_datetime(data, "ETA")


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
    print("creating ship tables")
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
    
    #number_of_rows = data.shape[0]
    
    #Prepare data for bulk inserts into the ship tables
    """ OLD:
    rows_to_insert = {mmsi: [] for mmsi in unique_mmsi}
    for index, row in data.iterrows():
        print(f"progress: {index} / {number_of_rows}")
        if pd.notna(row["MMSI"]) and row["MMSI"] != "":
            rows_to_insert[row["MMSI"]].append((
                row["Timestamp"],
                row["Type of mobile"],
                row["Latitude"],
                row["Longitude"],
                row["Navigational status"],
                row["ROT"],
                row["SOG"],
                row["COG"],
                row["Heading"],
                row["IMO"],
                row["Callsign"],
                row["Name"],
                row["Ship type"],
                row["Cargo type"],
                row["Width"],
                row["Length"],
                row["Type of position fixing device"],
                row["Draught"],
                row["Destination"],
                row["ETA"],
                row["Data source type"],
                row["A"],
                row["B"],
                row["C"],
                row["D"]
            ))"""

    valid_data = data[pd.notna(data["MMSI"]) & (data["MMSI"] != "")]  # Filter valid MMSI rows

    # Define the columns you need to extract
    columns = [
        "Timestamp", "Type of mobile", "Latitude", "Longitude", "Navigational status",
        "ROT", "SOG", "COG", "Heading", "IMO", "Callsign", "Name", "Ship type",
        "Cargo type", "Width", "Length", "Type of position fixing device", "Draught",
        "Destination", "ETA", "Data source type", "A", "B", "C", "D"
    ]
    print("Collecting data for tables")
    rows_to_insert = valid_data.groupby("MMSI")[columns].apply(lambda x: list(x.itertuples(index=False, name=None))).to_dict()

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
        return f"{year_day_month[2]}-{year_day_month[1]}-{year_day_month[0]} {text_bits[1]}"
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
        text = text.replace("'", "''")
        return text
    else:
        return "'Null'"

def handle_number_column(imputer, data, column_name):
    data[column_name] = data[column_name].astype(str).apply(handle_number)
    
def handle_text_column(data, column_name):
    data[column_name] = data[column_name].apply(handle_text)
  
def handle_datetime(data, column_name):
    data[column_name] = data[column_name].apply(convert_to_datetime)
    
    
if __name__ == "__main__":
    main()
