import pandas as pd
import folium
import numpy as np
import os
import random
from pathlib import Path
import colorsys
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt

def load_ais_data(file_path, max_rows=None, chunksize=100000):
    """
    Indlæser AIS-data fra CSV-fil med progress tracking
    
    Parameters:
    -----------
    file_path : str
        Sti til CSV-filen
    max_rows : int, optional
        Maksimalt antal rækker at læse (for hukommelsesstyring)
    chunksize : int, optional
        Antal rækker at læse ad gangen for progress tracking
    
    Returns:
    --------
    pd.DataFrame
        Indlæst AIS-data
    """
    print(f"Starter indlæsning af AIS-data fra {file_path}...")
    
    try:
        # Først tæl antallet af linjer i filen for at estimere størrelse
        # Men spring dette over hvis max_rows er defineret
        total_rows = None
        if not max_rows:
            try:
                print("Estimerer filstørrelse...")
                with open(file_path, 'r') as f:
                    for i, _ in enumerate(f):
                        if i % 1000000 == 0 and i > 0:
                            print(f"  Talt {i/1000000:.1f} millioner linjer...")
                        pass
                total_rows = i + 1
                print(f"Fil indeholder ca. {total_rows:,} linjer (inkl. header)")
            except Exception as e:
                print(f"Kunne ikke tælle linjer i filen: {str(e)}")
                print("Fortsætter uden progress estimation...")
        
        # Indlæs data i chunks for at vise progress
        print(f"Starter indlæsning af data{' (kan tage flere minutter)' if total_rows and total_rows > 1000000 else ''}...")
        
        if max_rows:
            # Hvis max_rows er specificeret, læs direkte
            print(f"Læser op til {max_rows:,} rækker...")
            data = pd.read_csv(file_path, nrows=max_rows)
            print(f"✓ Indlæst {len(data):,} AIS-datapunkter")
            return data
        else:
            # Ellers læs i chunks med progress tracking
            chunks = []
            rows_read = 0
            
            # Læs filen i chunks
            for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunksize)):
                chunks.append(chunk)
                rows_read += len(chunk)
                
                # Vis progress hver 5 chunks eller ved hver million rækker
                if (i+1) % 5 == 0 or rows_read % 1000000 < chunksize:
                    progress = (rows_read / total_rows * 100) if total_rows else None
                    if progress:
                        print(f"  Indlæst {rows_read:,} rækker ({progress:.1f}% af filen)...")
                    else:
                        print(f"  Indlæst {rows_read:,} rækker...")
            
            # Kombiner alle chunks
            data = pd.concat(chunks, ignore_index=True)
            print(f"✓ Indlæsning afsluttet. Samlet {len(data):,} AIS-datapunkter")
            return data
    except Exception as e:
        print(f"Fejl ved indlæsning af data: {str(e)}")
        return None

def extract_dkaab_ships(data):
    """
    Filtrerer data til kun at inkludere skibe med destination DKAAB
    
    Parameters:
    -----------
    data : pd.DataFrame
        AIS-data
    
    Returns:
    --------
    pd.DataFrame
        Filtreret data
    """
    print("\nStarter filtrering efter destination DKAAB...")
    
    # Tjek om destination-kolonnen eksisterer
    if 'Destination' not in data.columns:
        print("Fejl: Destination-kolonne ikke fundet i data")
        return data
    
    # Brug .fillna for at undgå fejl med NaN-værdier
    print("Forbehandler destination-kolonne...")
    
    # Vis nogle eksempler på destinationer før filtrering
    dest_samples = data['Destination'].dropna().sample(min(10, len(data))).tolist()
    print(f"Eksempler på destinationer i datasættet: {dest_samples}")
    
    # Tæl unikke destinationer
    dest_counts = data['Destination'].value_counts().head(10)
    print("Top 10 destinationer i datasættet:")
    for dest, count in dest_counts.items():
        print(f"  {dest}: {count:,} signaler")
    
    # Filtrer efter destination DKAAB (case-insensitive)
    print("Filtrerer efter 'DKAAB'...")
    dkaab_data = data[data['Destination'].str.upper().str.strip() == 'DKAAB'].copy()
    
    print(f"✓ Fundet {len(dkaab_data):,} AIS-datapunkter med destination DKAAB")
    
    # Vis hvor mange unikke skibe det drejer sig om
    unique_ships = dkaab_data['MMSI'].nunique()
    print(f"  Dette omfatter {unique_ships} unikke skibe")
    
    return dkaab_data

def identify_top_ships_by_signals(data, n=10):
    """
    Identificerer de n skibe med flest AIS-signaler
    
    Parameters:
    -----------
    data : pd.DataFrame
        AIS-data
    n : int, optional
        Antal skibe at vælge
    
    Returns:
    --------
    list
        Liste af MMSI for top n skibe
    dict
        Ordnet dictionary med MMSI og signalantal
    """
    print(f"\nAnalyserer {len(data):,} AIS-datapunkter for at finde top {n} skibe...")
    
    # Tæl antal signaler per MMSI
    print("Tæller signaler per skib...")
    start_time = datetime.now()
    signal_counts = Counter(data['MMSI'])
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    print(f"✓ Optælling gennemført på {elapsed:.2f} sekunder")
    
    # Find top n skibe
    print(f"Identificerer top {n} skibe...")
    top_ships = signal_counts.most_common(n)
    
    # Lav en tabel til output
    print(f"\n{'='*50}")
    print(f"Top {n} skibe efter antal AIS-signaler:")
    print(f"{'='*50}")
    print(f"{'MMSI':<12} | {'Navn':<25} | {'Type':<25} | {'Signaler':<10}")
    print(f"{'-'*12}-+-{'-'*25}-+-{'-'*25}-+-{'-'*10}")
    
    # Detaljer om hvert skib
    for mmsi, count in top_ships:
        # Forsøg at hente skibsnavn og type hvis det findes
        name = "Ukendt"
        ship_type = "Ukendt"
        
        if 'Name' in data.columns:
            names = data[data['MMSI'] == mmsi]['Name'].unique()
            if len(names) > 0 and not pd.isna(names[0]):
                name = names[0]
        
        if 'Ship type' in data.columns:
            types = data[data['MMSI'] == mmsi]['Ship type'].unique()
            if len(types) > 0 and not pd.isna(types[0]):
                ship_type = types[0]
        
        print(f"{mmsi:<12} | {name[:25]:<25} | {str(ship_type)[:25]:<25} | {count:<10,}")
    
    print(f"{'='*50}")
    
    # Returner liste af MMSI og dictionary med counts
    return [mmsi for mmsi, _ in top_ships], dict(top_ships)

def generate_distinct_colors(n):
    """
    Genererer n visuelt adskilte farver
    
    Parameters:
    -----------
    n : int
        Antal farver at generere
    
    Returns:
    --------
    list
        Liste af farver i hex-format
    """
    colors = []
    for i in range(n):
        # Brug HSV-farverum for bedre visuel adskillelse
        h = i / n
        s = 0.7 + 0.3 * (i % 3) / 2  # Varierende mætning
        v = 0.9
        
        # Konverter HSV til RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        # Konverter til hex-format
        hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        colors.append(hex_color)
    
    return colors

def visualize_ship_trajectories(data, top_mmsi, signal_counts):
    """
    Visualiserer ruter for top n skibe med destination DKAAB
    
    Parameters:
    -----------
    data : pd.DataFrame
        AIS-data
    top_mmsi : list
        Liste af MMSI for top skibe
    signal_counts : dict
        Ordbog med MMSI og signalantal
    
    Returns:
    --------
    folium.Map
        Kort med visualiserede ruter
    """
    print("\nStarter visualisering af skibsruter...")
    
    # Filtrer data til kun at inkludere top skibe
    print(f"Udtrækker data for {len(top_mmsi)} skibe...")
    top_ships_data = data[data['MMSI'].isin(top_mmsi)].copy()
    print(f"✓ Udtrukket {len(top_ships_data):,} AIS-punkter for top skibe")
    
    # Sorter efter MMSI og timestamp
    print("Sorterer datapunkter efter MMSI og tidspunkt...")
    if 'Timestamp' in top_ships_data.columns:
        try:
            top_ships_data['Timestamp'] = pd.to_datetime(top_ships_data['Timestamp'])
            top_ships_data = top_ships_data.sort_values(['MMSI', 'Timestamp'])
            print("✓ Data sorteret efter MMSI og tidspunkt")
        except Exception as e:
            print(f"Advarsel: Kunne ikke konvertere tidsstempel: {str(e)}")
            print("  Fortsætter uden tidsmæssig sortering")
    
    # Beregn center for kortet baseret på gennemsnit af positioner
    print("Beregner kortcenter baseret på positioner...")
    center = [
        top_ships_data['Latitude'].mean(),
        top_ships_data['Longitude'].mean()
    ]
    
    # Opret kort
    print("Opretter basiskort...")
    m = folium.Map(location=center, zoom_start=8, tiles='CartoDB positron')
    
    # Tilføj titel og info
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>Skibe med destination DKAAB</b></h3>
        <h4 align="center" style="font-size:14px">Viser top {len(top_mmsi)} skibe efter antal AIS-signaler</h4>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Generer en række visuelt adskilte farver
    colors = generate_distinct_colors(len(top_mmsi))
    
    # Tilføj feature gruppe til legend
    legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 1px solid grey; border-radius: 5px;">'
    legend_html += '<h4 style="margin-top: 0;">Skibsruter</h4>'
    
    print("\nBehandler skibsruter...")
    print(f"{'MMSI':<12} | {'Signaler':<8} | {'Punkter plottet':<15} | Status")
    print(f"{'-'*12}-+-{'-'*8}-+-{'-'*15}-+-{'-'*30}")
    
    # Opret en feature gruppe for hver skib
    for i, mmsi in enumerate(top_mmsi):
        # Filtrer data for dette skib
        ship_data = top_ships_data[top_ships_data['MMSI'] == mmsi]
        
        # Hent skibsinfo
        ship_name = "Ukendt"
        ship_type = "Ukendt"
        
        if 'Name' in ship_data.columns and len(ship_data) > 0:
            name_values = ship_data['Name'].dropna()
            if len(name_values) > 0:
                ship_name = name_values.iloc[0]
        
        if 'Ship type' in ship_data.columns and len(ship_data) > 0:
            type_values = ship_data['Ship type'].dropna()
            if len(type_values) > 0:
                ship_type = type_values.iloc[0]
        
        # Tjek om vi har nok data til at plotte
        if len(ship_data) < 2:
            print(f"{mmsi:<12} | {signal_counts[mmsi]:<8,} | {0:<15} | Springes over (for få punkter)")
            continue
        
        # Vælg farve for dette skib
        color = colors[i]
        
        # Opret en feature gruppe for dette skib
        fg = folium.FeatureGroup(name=f"Skib: {ship_name} (MMSI: {mmsi})")
        
        # Tilføj til legend
        legend_html += f'<div><span style="background-color: {color}; width: 20px; height: 10px; display: inline-block;"></span> {ship_name} (MMSI: {mmsi}) - {signal_counts[mmsi]} signaler</div>'
        
        # Tilføj linje for ruten
        coordinates = ship_data[['Latitude', 'Longitude']].values.tolist()
        folium.PolyLine(
            coordinates,
            color=color,
            weight=4,
            opacity=0.8,
            popup=f"MMSI: {mmsi}<br>Navn: {ship_name}<br>Type: {ship_type}<br>AIS-signaler: {signal_counts[mmsi]}"
        ).add_to(fg)
        
        # Tæller for visualiserede punkter
        points_plotted = 0
        max_points = min(500, len(ship_data))  # Begræns antallet af punkter af performance-hensyn
        
        # Beregn step size for at vælge punkter jævnt fordelt
        step = max(1, len(ship_data) // max_points)
        
        # Tilføj punkter for positioner med timestamp
        if 'Timestamp' in ship_data.columns:
            for idx, row in ship_data.iloc[::step].iterrows():
                # Formatter tidsstemplet hvis det findes
                timestamp_str = row['Timestamp']
                if isinstance(timestamp_str, (pd.Timestamp, datetime)):
                    timestamp_formatted = timestamp_str.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp_formatted = str(timestamp_str)
                
                # Opret popup-tekst
                popup_text = f"""
                <b>Skib:</b> {ship_name}<br>
                <b>MMSI:</b> {mmsi}<br>
                <b>Tidspunkt:</b> {timestamp_formatted}<br>
                <b>Position:</b> {row['Latitude']:.5f}, {row['Longitude']:.5f}
                """
                
                # Tilføj cirkelmarkør for positionen
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=3,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=popup_text
                ).add_to(fg)
                
                points_plotted += 1
        
        # Tilføj markører for start- og slutpunkter
        folium.Marker(
            coordinates[0], 
            popup=f"Start: {ship_name}<br>Tid: {ship_data['Timestamp'].iloc[0] if 'Timestamp' in ship_data.columns else 'Ukendt'}",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(fg)
        
        folium.Marker(
            coordinates[-1],
            popup=f"Slut: {ship_name}<br>Tid: {ship_data['Timestamp'].iloc[-1] if 'Timestamp' in ship_data.columns else 'Ukendt'}",
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(fg)
        
        # Tilføj skibets feature gruppe til kortet
        fg.add_to(m)
        
        # Vis info om dette skib
        print(f"{mmsi:<12} | {signal_counts[mmsi]:<8,} | {points_plotted:<15} | Plottet (rute + punkter)")
    
    # Afslut legend
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Tilføj lagkontrol
    print("\nTilføjer kortfunktioner...")
    folium.LayerControl().add_to(m)
    
    # Tilføj måleinstrument
    folium.plugins.MeasureControl(position='topright', primary_length_unit='kilometers').add_to(m)
    
    print("✓ Kortet er genereret med alle ruter og punkter")
    return m

def create_signal_distribution_chart(signal_counts, output_dir):
    """
    Opretter et søjlediagram over fordelingen af AIS-signaler for top-skibe
    
    Parameters:
    -----------
    signal_counts : dict
        Dictionary med MMSI og antal signaler
    output_dir : Path
        Sti til output-mappen
    """
    plt.figure(figsize=(12, 6))
    mmsi_short = [str(mmsi)[-6:] for mmsi in signal_counts.keys()]  # Forkortet MMSI for bedre læsbarhed
    counts = list(signal_counts.values())
    
    # Opret søjlediagram
    bars = plt.bar(mmsi_short, counts, color='skyblue')
    
    # Tilføj værdier oven på hver søjle
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', rotation=0)
    
    plt.title('Antal AIS-signaler per skib med destination DKAAB')
    plt.xlabel('MMSI (sidste 6 cifre)')
    plt.ylabel('Antal signaler')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Gem figuren
    chart_path = output_dir / "ais_signal_distribution.png"
    plt.savefig(chart_path)
    print(f"Signalfordelingsgraf gemt til {chart_path}")
    plt.close()

def main():
    print("\n" + "="*70)
    print("  AIS RUTEPLOTTER FOR DKAAB DESTINATION - START")
    print("="*70)
    start_time = datetime.now()
    print(f"Start tidspunkt: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Indstil filsti - tjek forskellige formater
    file_path = "aisdk-2025-02-27/aisdk-2025-02-27.csv"
    alt_file_path = "aisdk-2025-02-27\\aisdk-2025-02-27.csv"
    
    print("\nSøger efter AIS data...")
    # Prøv forskellige stiformater
    if os.path.exists(file_path):
        actual_path = file_path
        print(f"✓ Fandt fil ved sti: {file_path}")
    elif os.path.exists(alt_file_path):
        actual_path = alt_file_path
        print(f"✓ Fandt fil ved sti: {alt_file_path}")
    else:
        print(f"❌ Fejl: Kunne ikke finde fil på hverken {file_path} eller {alt_file_path}")
        print("   Juster venligst filstien eller sørg for at filen eksisterer.")
        return
    
    # Mulige begrænsninger
    print("\nKonfigurerer indlæsning...")
    # Indstillinger for dataindlæsning
    max_rows = None  # Ingen begrænsning - indlæs alle rækker
    # Hvis du vil begrænse datamængden (for hurtigere test), udkommenter linjen nedenfor:
    # max_rows = 1000000  # Begræns til 1 million rækker for hurtig test
    
    if max_rows:
        print(f"⚠️ Begrænser indlæsning til {max_rows:,} rækker (for test)")
    else:
        print("ℹ️ Indlæser alle rækker i CSV-filen (kan tage lang tid)")
    
    # Indlæs data
    ais_data = load_ais_data(actual_path, max_rows)
    
    if ais_data is None:
        print("❌ Fejl: Data kunne ikke indlæses. Afslutter.")
        return
    
    if len(ais_data) == 0:
        print("❌ Fejl: Ingen data fundet i filen. Afslutter.")
        return
    
    # Filtrer til kun at inkludere skibe med destination DKAAB
    dkaab_data = extract_dkaab_ships(ais_data)
    
    # Frigør hukommelse fra den store dataframe hvis muligt
    if len(dkaab_data) > 0:
        print("\nFrigør hukommelse fra den komplette AIS-dataset...")
        del ais_data
        import gc
        gc.collect()
        print("✓ Hukommelse frigjort")
    
    if len(dkaab_data) == 0:
        print("❌ Ingen skibe fundet med destination DKAAB. Afslutter.")
        return
    
    # Identificer top 10 skibe med flest AIS-signaler
    top_mmsi, signal_counts = identify_top_ships_by_signals(dkaab_data, n=10)
    
    # Opret output-mappe
    output_dir = Path("rute_kort")
    print(f"\nOpretter output-mappe: {output_dir}")
    output_dir.mkdir(exist_ok=True)
    print("✓ Output-mappe klar")
    
    # Opret visualiseringskort med ruterne
    route_map = visualize_ship_trajectories(dkaab_data, top_mmsi, signal_counts)
    
    # Gem kortet
    map_file = output_dir / "dkaab_top10_ships.html"
    print(f"\nGemmer kort til fil: {map_file}")
    route_map.save(str(map_file))
    print(f"✓ Kort med skibsruter gemt til {map_file}")
    
    # Opret og gem signaldistribution
    print("\nGenererer signaldistributionsgraf...")
    create_signal_distribution_chart(signal_counts, output_dir)
    
    # Vis afslutning og tidsforbrug
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print("\n" + "="*70)
    print("  AIS RUTEPLOTTER FOR DKAAB DESTINATION - AFSLUTTET")
    print("="*70)
    print(f"Start:     {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Slut:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Varighed:  {int(hours)}t {int(minutes)}m {int(seconds)}s")
    print("\nGenererede filer:")
    print(f"  - {map_file} (interaktivt kort)")
    print(f"  - {output_dir}/ais_signal_distribution.png (graf)")
    print("\n✅ Processen er fuldført med succes!")

if __name__ == "__main__":
    try:
        import folium.plugins
    except ImportError:
        print("Advarsel: folium.plugins ikke fundet. Installerer...")
        import pip
        pip.main(['install', 'folium'])
        import folium.plugins
    
    main()