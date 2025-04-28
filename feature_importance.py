import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import OrdinalEncoder
import numpy as np
import matplotlib.pyplot as plt

# --- Parametre ---
database_path = "preprocessing/ais.db"
max_ship_count = 10  # Antal skibe der bruges til analysen
# Tidslags-parametre (samme som i model.py)
time_lags = [4, 12, 24]  # i timer
exclude_columns = ['Destination', 'Cargo_type']

# --- Funktion til at hente data fra en tabel ---
def get_ship_data(ship_table_name: str) -> pd.DataFrame:
    try:
        con = sqlite3.connect(database_path)
        query = f"SELECT * FROM {ship_table_name};"
        df = pd.read_sql_query(query, con)
        con.close()
        return df
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return pd.DataFrame()

# --- Funktion til at lave lagged features (tidslags-features) ---
def get_datapoints_from_ship(df: pd.DataFrame) -> pd.DataFrame:
    # Konverter Timestamp til datetime og sorter
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp")
    df.set_index("Timestamp", inplace=True)
    result_df = df.copy()
    # Udvælg kolonner der skal lages (alle undtagen exclude_columns)
    cols_to_shift = [col for col in df.columns if col not in exclude_columns]
    # Lav lagged features for hver time-lag
    for lag in time_lags:
        lag_hours = f"{lag}h"
        lagged_df = df[cols_to_shift].shift(freq=pd.Timedelta(hours=lag))
        lagged_df.columns = [f"{lag_hours}_{col}" for col in lagged_df.columns]
        result_df = result_df.join(lagged_df, how="left")
    # Drop rækker hvor nogen lagged features mangler
    lagged_columns = [f"{lag}h_{col}" for lag in time_lags for col in cols_to_shift]
    result_df = result_df.dropna(subset=lagged_columns)
    result_df.reset_index(inplace=True)
    return result_df

# --- Hent alle skibstabeller ---
con = sqlite3.connect(database_path)
ships_df = pd.read_sql_query("SELECT table_name FROM Ships", con)
ship_tables = ships_df['table_name'].tolist()
con.close()

# --- Saml data fra flere skibe med lagged features ---
data = pd.DataFrame()
for i, ship in enumerate(ship_tables):
    if i >= max_ship_count:
        break
    print(f"Indlæser og laver lagged features for: {ship}")
    df = get_ship_data(ship)
    if not df.empty:
        lagged_df = get_datapoints_from_ship(df)
        data = pd.concat([data, lagged_df], ignore_index=True)

print(f"Samlet antal rækker: {len(data)}")

# --- Udvælg features og target (samme som i model.py) ---
features = [
    'Latitude', 'Longitude', 'Navigational_status', 'ROT', 'SOG', 'COG',
    'Heading', 'Cargo_type', 'Width', 'Length', 'Draught'
]
# Tilføj lagged features til feature-listen
for lag in time_lags:
    lag_hours = f"{lag}h"
    for col in features:
        if col not in exclude_columns:
            features.append(f"{lag_hours}_{col}")
target = 'Destination'

# --- Fjern rækker med manglende værdier ---
data = data.dropna(subset=features + [target])
print(f"Antal rækker efter rensning: {len(data)}")

# --- Kod alle ikke-numeriske features i X til tal ---
encoder = OrdinalEncoder()
for col in ['Cargo_type', 'Navigational_status']:
    if col in data.columns:
        data[[col]] = encoder.fit_transform(data[[col]])
        print(f"OrdinalEncoder brugt på kolonne: {col}")
# Kod også lagged tekst-features hvis de findes
for lag in time_lags:
    lag_hours = f"{lag}h"
    for col in ['Cargo_type', 'Navigational_status']:
        lag_col = f"{lag_hours}_{col}"
        if lag_col in data.columns:
            data[[lag_col]] = encoder.fit_transform(data[[lag_col]])
            print(f"OrdinalEncoder brugt på kolonne: {lag_col}")

# --- Forbered X og y ---
X = data[features]
y = data[target]

# --- Split i train/test ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Træn Random Forest Classifier ---
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# --- Evaluer model ---
y_pred = rf.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# --- Udtræk og vis feature importances ---
importances = rf.feature_importances_
feature_importance = pd.Series(importances, index=features).sort_values(ascending=False)

print("\nFeature Importance (højeste først):")
for feat, imp in feature_importance.items():
    print(f"  {feat}: {imp:.4f}")

plt.figure(figsize=(12,6))
feature_importance.plot(kind='bar')
plt.title('Random Forest Feature Importance for Destination (med lagged features)')
plt.ylabel('Importance')
plt.xlabel('Feature')
plt.tight_layout()
plt.show() 