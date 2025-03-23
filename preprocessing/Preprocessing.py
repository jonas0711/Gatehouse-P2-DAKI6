# Har AIS data fra den 10-03-2025 til den 20-03-2025
import pandas as pd
import SQLSystem as sql

from sklearn.preprocessing import OrdinalEncoder

def main():
    preprocess("preprocessing/AIS/aisdk-2025-03-10/aisdk-2025-03-10.csv")

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
    
    number_of_rows = data.shape[0]
    #loops though every row in the csv file
    for index, row in data.iterrows():
        if pd.notna(row["MMSI"]) and row["MMSI"] != "": #if the entry has a MMSI (essentially a unique id for every ship)
            
            print(f"progress: {index} / {number_of_rows}")
            #inserts ship into ships table
            sql.execute_query(database, 
                f"""INSERT OR IGNORE INTO Ships (table_name)
                VALUES
                    ('ship_{row["MMSI"]}');""") #IGNORE makes it not add the entry if it already exists
            
            #creates a table for the ship with the MMSI serving as its name (this table will contain the info from all the AIS messages the ship sent)
            sql.execute_query(database, 
                f"""CREATE TABLE IF NOT EXISTS ship_{row["MMSI"]} (
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
                    Destination Text,
                    ETA DATETIME,
                    Data_source_type SMALLINT,
                    A FLOAT,
                    B FLOAT,
                    C FLOAT,
                    D FLOAT,
                    UNIQUE(Timestamp));""") # UNIQUE(Timestamp) makes it so that there will only be one row that can have any given timestamp (no duplicates)
            
            #Inserts the current row's data into the table of the ship
            sql.execute_query(database, 
                f"""INSERT OR IGNORE INTO ship_{row["MMSI"]} (
                    Timestamp, Type_of_mobile, Latitude, Longitude, Navigational_status,
                    ROT, SOG, COG, Heading, IMO, 
                    Callsign, Name, Ship_type, Cargo_type, Width,
                    Length, Type_of_position_fixing_device, Draught, Destination, ETA, 
                    Data_source_type, A, B, C, D)
                VALUES
                    ({convert_to_datetime(row["Timestamp"])}, {handle_number(row["Type of mobile"])}, {handle_number(row["Latitude"])}, {handle_number(row["Longitude"])}, {handle_text(row["Navigational status"])}, 
                    {handle_number(row["ROT"])}, {handle_number(row["SOG"])}, {handle_number(row["COG"])}, {handle_number(row["Heading"])}, {handle_text(row["IMO"])}, 
                    {handle_text(row["Callsign"])}, {handle_text(row["Name"])}, {handle_number(row["Ship type"])}, {handle_text(row["Cargo type"])}, {handle_number(row["Width"])}, 
                    {handle_number(row["Length"])}, {handle_number(row["Type of position fixing device"])}, {handle_number(row["Draught"])}, {handle_text(row["Destination"])}, {convert_to_datetime(row["ETA"])}, 
                    {handle_number(row["Data source type"])}, {handle_number(row["A"])}, {handle_number(row["B"])}, {handle_number(row["C"])}, {handle_number(row["D"])});""") #IGNORE makes it not add the entry if it already exists
            
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
