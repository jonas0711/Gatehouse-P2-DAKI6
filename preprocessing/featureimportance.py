import pandas as pd
import sqlite3
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import OrdinalEncoder
import matplotlib.pyplot as plt
import numpy as np

####################################
#---------Settings (Start)---------#
####################################

databse_path = "preprocessing/ais.db"
max_ship_count = 100
use_all_ships = False #if true the model will train on all ships

use_includes = False # will only include ships with the destination in the include list
use_excludes = False # will exclude any ships with a destination in the exlude list
include = []
exclude = []

time_lags = [4, 8, 12]  # in hours
exclude_columns_from_lag = ['Destination', 'Cargo_type']
exclude_colums_from_traning = [] #excluded after time lagged variables are made

####################################
#----------Settings (End)----------#
####################################

def main():
    ships_dataframe = get_ship_data("Ships")
    
    data = pd.DataFrame()
    effective_max_ship_count = max_ship_count

    if use_all_ships:
        effective_max_ship_count, _ = ships_dataframe.shape
    
    for i, ship in enumerate(ships_dataframe["table_name"]):
        if i < effective_max_ship_count:
            print(f"concating: {i} / {effective_max_ship_count}")
            data = pd.concat([data, get_datapoints_from_ship(get_ship_data(ship))])

    print("Encoding cargo type")  
    encoder = OrdinalEncoder()
    data["Cargo_type"] = encoder.fit_transform(data[["Cargo_type"]])
    
    print("Processing destinations")
    if use_includes:
        data = data[data["Destination"].isin(include)]     
    if use_excludes:
        data = data[~data["Destination"].isin(include)]
    if len(exclude_colums_from_traning) > 0:
        data = data.drop(columns=exclude_colums_from_traning)
    
    y = data['Destination']
    x = data.drop(columns=['Timestamp', 'Destination'])

    # Split data
    print("Test train split")
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    print("Traning Gradient boosting model")
    # Initialize and train model
    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    
    print(model.feature_importances_)

    # Make predictions
    y_pred = model.predict(X_test)

    # Evaluate model
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Classification Report:\n", classification_report(y_test, y_pred))
    
    # And your feature names
    feature_names = X_train.columns  # If X_train is a DataFrame

    # Get feature importances and sort them
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]  # Sort in descending order

    # Plot
    plt.figure(figsize=(10, 6))
    plt.title("Feature Importances")
    plt.bar(range(len(importances)), importances[indices], align="center")
    plt.xticks(range(len(importances)), feature_names[indices], rotation=90)
    plt.tight_layout()
    plt.show()

    

def get_datapoints_from_ship(df: pd.DataFrame) -> pd.DataFrame:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp")

    # Set index to timestamp for merging
    df.set_index("Timestamp", inplace=True)

    # Initialize result with original data
    result_df = df.copy()

    cols_to_shift = [col for col in df.columns if col not in exclude_columns_from_lag]

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