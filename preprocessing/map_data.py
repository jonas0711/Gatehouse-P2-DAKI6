import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def plot_ship_positions_only(db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of all ship table names from Ships table
    cursor.execute("SELECT table_name FROM Ships")
    ship_tables = cursor.fetchall()

    # Set up the map using Cartopy
    fig = plt.figure(figsize=(12, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-2, 24, 50, 64], crs=ccrs.PlateCarree())  # Denmark and surrounding waters
    ax.coastlines(resolution='10m')
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=True)

    # Plot all ship positions as dots (same color)
    for table_name_tuple in ship_tables:
        table_name = table_name_tuple[0]
        try:
            df = pd.read_sql_query(f"SELECT Latitude, Longitude FROM {table_name}", conn)
            if not df.empty:
                ax.scatter(df['Longitude'], df['Latitude'], color='red', s=3, alpha=0.6, transform=ccrs.PlateCarree())
        except Exception as e:
            print(f"Error reading {table_name}: {e}")

    plt.title("Ship Positions in and Around Denmark")
    plt.show()

    # Close DB connection
    conn.close()


plot_ship_positions_only("preprocessing/ais.db")