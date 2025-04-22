import pandas as pd
import sqlite3
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import OrdinalEncoder

databse_path = "preprocessing/ais.db"
time_error_rate = 3600
time_lags = [4, 12, 24]  # in hours
exclude_columns = ['Destination', 'Cargo_type']
max_ship_count = 10

def main():
    ships_dataframe = get_ship_data("Ships")
    
    data = pd.DataFrame()
    
    for i, ship in enumerate(ships_dataframe["table_name"]):
        if i < max_ship_count:
            data = pd.concat([data, get_datapoints_from_ship(get_ship_data(ship))])
            
    encoder = OrdinalEncoder()
    data["Cargo_type"] = encoder.fit_transform(data[["Cargo_type"]])
    
    y = data['Destination']
    x = data.drop(columns=['Timestamp', 'Destination'])

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    # Initialize and train model
    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Evaluate model
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Classification Report:\n", classification_report(y_test, y_pred))
    
            
    print(data)

    

def get_datapoints_from_ship(df: pd.DataFrame) -> pd.DataFrame:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp")

    # Set index to timestamp for merging
    df.set_index("Timestamp", inplace=True)

    # Initialize result with original data
    result_df = df.copy()

    cols_to_shift = [col for col in df.columns if col not in exclude_columns]

    # Create lagged variables for each time lag
    for lag in time_lags:
        lag_hours = f"{lag}h"
        lagged_df = df[cols_to_shift].shift(freq=pd.Timedelta(hours=lag))
        lagged_df.columns = [f"{lag_hours}_{col}" for col in lagged_df.columns]
        result_df = result_df.join(lagged_df, how="left")

    # Drop rows where any of the lagged variables (4h, 12h, 24h) are NaN
    lagged_columns = [f"{lag}h_{col}" for lag in time_lags for col in cols_to_shift]
    result_df = result_df.dropna(subset=lagged_columns)

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