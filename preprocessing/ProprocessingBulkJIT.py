import pandas as pd
import SQLSystem as sql
import numpy as np
from numba import jit, prange, float64, int64
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
import time

def main():
    start_time = time.time()
    preprocess("C:\\Users\\jonas\\Desktop\\Design og anvendelse af kunstig inteligens\\2. Semester\\Projekt - Gatehouse\\AIS\\aisdk-2025-03-10.csv")
    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

def preprocess(csv_file_path):
    print("loading csv")
    data = pd.read_csv(csv_file_path)
    
    print("Available columns:")
    print(data.columns.tolist())
    
    # ----------------------------------------------------------#
    # ----------drop/change values that are not needed----------#
    # ----------------------------------------------------------#
    data = data[data["Type of mobile"].isin(["Class A"])]
    data["Navigational status"] = data["Navigational status"].apply(lambda x: x if x == "Under way using engine" or x == "Engaged in fishing" 
                                                                   or x == "Unknown value" or x == "Moored" or x == "Restricted maneuverability"
                                                                   or x == "Under way sailing" or x == "Constrained by her draught" else "Other")
    
    # Filter rows with NaN values - doing this in one step is more efficient
    required_columns = ["Latitude", "Longitude", "ROT", "SOG", "COG", "Heading", "Width", "Length", "Draught"]
    data = data.dropna(subset=required_columns)
    
    # ---------------------------------------------------------------------------------------------------------------#
    # ----------encoding for the values that only have a few options (mby use on cargo type or destination)----------#
    # ---------------------------------------------------------------------------------------------------------------#
    navigational_status_enc = OrdinalEncoder()
    
    print("Encoding: Navigational status")
    data["Navigational status"] = navigational_status_enc.fit_transform(data[["Navigational status"]])
    
    # ---------------------------------------------------------------------------------#
    # ----------replace nan values with a constant value. in this case 'NULL'----------#
    # ---------------------------------------------------------------------------------#
    nan_fill_imputer = SimpleImputer(strategy="constant", missing_values=np.nan, fill_value="'NULL'")
    
    # Optimize the number format conversion by using NumPy vectorized operations
    numeric_columns = [
        "Latitude", "Longitude", "ROT", "SOG", "COG", 
        "Heading", "Width", "Length", "Draught", "Navigational status"
    ]
    
    print("Converting numeric columns format")
    for i, column in enumerate(numeric_columns):
        print(f"converting number formats step {i+1} / {len(numeric_columns)}")
        handle_number_column(nan_fill_imputer, data, column)
    
    text_columns = ["Cargo type", "Destination"]
    print("Converting text columns format")
    for i, column in enumerate(text_columns):
        print(f"converting text formats step {i+1} / {len(text_columns)}")
        handle_text_column(data, column)
    
    print("Converting datetime formats")
    # Korrigeret kolonnenavn fra "Timestamp" til "# Timestamp"
    handle_datetime(data, "# Timestamp")
    
    # -----------------------------------------------------------------------------------------#
    # -------converting to sql database and removing duplicates in the following section-------#
    # -----------------------------------------------------------------------------------------#
    database = sql.create_connection("preprocessing/chunked_ais.db")
    
    sql.execute_query(database, """CREATE TABLE IF NOT EXISTS Ships (
        table_name TEXT NOT NULL UNIQUE);""")
    
    # Get a list of unique MMSI
    print("finding all ships")
    unique_mmsi = data["MMSI"].unique()
    
    # Prepare data for bulk inserts
    print("preparing ships")
    ship_inserts = [(f"ship_{mmsi}",) for mmsi in unique_mmsi]
    
    # Bulk insert into Ships table (insert all ship table names at once)
    print("inserting ships into sql database")
    sql.execute_query(database, """INSERT OR IGNORE INTO Ships (table_name) VALUES (?);""", ship_inserts)
    
    # Create ship tables - use JIT for this loop if possible
    print("creating ship tables")
    create_ship_tables(database, unique_mmsi)
    
    valid_data = data[pd.notna(data["MMSI"]) & (data["MMSI"] != "")]  # Filter valid MMSI rows
    
    # Define the columns you need to extract - korrigeret "Timestamp" til "# Timestamp"
    columns = [
        "# Timestamp", "Latitude", "Longitude", "Navigational status",
        "ROT", "SOG", "COG", "Heading",
        "Cargo type", "Width", "Length", "Draught", "Destination"
    ]
    
    print("Collecting data for tables")
    # Use optimized grouping and conversion to dictionaries
    rows_to_insert = prepare_data_for_insert(valid_data, columns)
    
    print("inserting into sql database")
    # Bulk insert into the corresponding ship tables
    number_of_ships = len(unique_mmsi)
    # Use JIT for database insertion loop
    insert_data_into_tables(database, unique_mmsi, rows_to_insert, number_of_ships)
    
    # To print the encoder categories at the end
    print("finished creating database")
    print_precentages(data, "Navigational status", navigational_status_enc)


# JIT optimized function for creating ship tables
@jit(nopython=False)  # Can't use nopython due to SQL operations
def create_ship_tables(database, unique_mmsi):
    for mmsi in unique_mmsi:
        sql.execute_query(database, 
            f"""CREATE TABLE IF NOT EXISTS ship_{mmsi} (
                Timestamp DATETIME NOT NULL,
                Latitude FLOAT,
                Longitude FLOAT,
                Navigational_status SMALLINT,
                ROT FLOAT,
                SOG FLOAT,
                COG FLOAT,
                Heading FLOAT,
                Cargo_type TEXT,
                Width FLOAT,
                Length FLOAT,
                Draught TEXT,
                Destination TEXT,
                UNIQUE(Timestamp));""")


# JIT optimized function for data preparation
def prepare_data_for_insert(valid_data, columns):
    # Using pandas groupby is likely more efficient than a JIT version for this specific operation
    return valid_data.groupby("MMSI")[columns].apply(lambda x: list(x.itertuples(index=False, name=None))).to_dict()


# JIT optimized function for database insertion
@jit(nopython=False)  # Can't use nopython due to SQL operations
def insert_data_into_tables(database, unique_mmsi, rows_to_insert, number_of_ships):
    for index, mmsi in enumerate(unique_mmsi):
        print(f"progress sql: {index} / {number_of_ships}")
        
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
            Timestamp, Latitude, Longitude, Navigational_status,
            ROT, SOG, COG, Heading, Cargo_type, Width,
            Length, Draught, Destination
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        # Insert the rows into the dynamic table
        sql.execute_query(database, insert_query, ship_rows)


# JIT optimized datetime conversion function
@jit(nopython=True)
def convert_to_datetime_jit(text):
    if text != "nan" and text is not None and text != "":
        text_bits = text.split(" ")
        if len(text_bits) >= 2:
            year_day_month = text_bits[0].split("/")
            if len(year_day_month) >= 3:
                return f"{year_day_month[2]}-{year_day_month[1]}-{year_day_month[0]} {text_bits[1]}"
    return "NULL"


# JIT optimized number handler
@jit(nopython=True)
def handle_number_jit(number_str):
    if number_str != "nan" and number_str is not None and number_str != "":
        return number_str
    else:
        return "NULL"


# JIT optimized text handler
@jit(nopython=True)
def handle_text_jit(text):
    if text != "nan" and text is not None and text != "":
        return text.replace("'", "''")
    else:
        return "Null"


# These functions apply the JIT optimized functions to dataframe columns
def handle_number_column(imputer, data, column_name):
    try:
        # Convert column to numpy array for faster processing
        column_array = data[column_name].astype(str).values
        
        # Apply JIT function using numpy's vectorize for better performance
        vectorized_handle_number = np.vectorize(handle_number_jit)
        data[column_name] = vectorized_handle_number(column_array)
    except Exception as e:
        print(f"Error processing column {column_name}: {e}")


def handle_text_column(data, column_name):
    try:
        # Convert column to numpy array for faster processing
        column_array = data[column_name].astype(str).values
        
        # Apply JIT function using numpy's vectorize
        vectorized_handle_text = np.vectorize(handle_text_jit)
        data[column_name] = vectorized_handle_text(column_array)
    except Exception as e:
        print(f"Error processing column {column_name}: {e}")


def handle_datetime(data, column_name):
    try:
        # Convert column to numpy array for faster processing
        column_array = data[column_name].astype(str).values
        
        # Apply JIT function using numpy's vectorize
        vectorized_convert_datetime = np.vectorize(convert_to_datetime_jit)
        data[column_name] = vectorized_convert_datetime(column_array)
    except Exception as e:
        print(f"Error processing datetime column {column_name}: {e}")


def print_precentages(data: pd.DataFrame, column_name: str, encoder: OrdinalEncoder):
    print(f"---- categories for {column_name} ----")
    percentages = data[column_name].value_counts(normalize=True) * 100
    categories = list(encoder.categories_[0])
    percentage_dict = {categories[int(float(idx))]: pct for idx, pct in percentages.items()}
    
    for category, pct in percentage_dict.items():
        print(f"{category}: {pct:.2f}%")


if __name__ == "__main__":
    main()