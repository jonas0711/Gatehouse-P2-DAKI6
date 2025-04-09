import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier

databse_path = "preprocessing/ais.db"
time_error_rate = 3600
time_lags = [4, 12, 24]  # in hours
max_ship_count = 10

def main():
    ships_dataframe = get_ship_data("Ships")
    
    data = pd.DataFrame()

    for i, ship in enumerate(ships_dataframe["table_name"]):
        if i < max_ship_count:
            pd.concat(data, get_datapoints_from_ship(get_ship_data(ship)))

    

def get_datapoints_from_ship(df: pd.DataFrame) -> pd.DataFrame:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp")

    # Set index to timestamp for merging
    df.set_index("Timestamp", inplace=True)

    # Initialize result with original data
    result_df = df.copy()

    # Create lagged variables for each time lag
    for lag in time_lags:
        lag_hours = f"{lag}h"
        lagged_df = df.shift(freq=pd.Timedelta(hours=lag))
        lagged_df.columns = [f"{lag_hours}_{col}" for col in lagged_df.columns]
        result_df = result_df.join(lagged_df, how="left")

    result_df.reset_index(inplace=True)  # Bring timestamp back as column
    return result_df
    


#reads a table from the sql database, and converts it to a pandas dataframe
def get_ship_data(ship_table_name : str) -> pd.DataFrame:
    
    try:
        conection = sqlite3.connect(databse_path)
        query = f"SELECT * FROM {ship_table_name};"

        df = pd.read_sql_query(query, conection)
        conection.close()
        return df
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error


if __name__ == "__main__":
    main()