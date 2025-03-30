import os
import pandas as pd
from collections import Counter
import time
from pathlib import Path

def find_unique_destinations(folder_path, output_file="unique_destinations.txt"):
    """
    Finder alle unikke værdier i kolonnen 'Destination' på tværs af alle Excel-filer i den angivne mappe.
    Gemmer resultatet til en txt-fil.
    
    Args:
        folder_path (str): Stien til mappen med AIS Excel-filer
        output_file (str): Stien til output filen
        
    Returns:
        set: Et sæt med alle unikke destinationsværdier
    """
    print(f"Starter søgning efter unikke destinationer i: {folder_path}")
    start_time = time.time()
    
    # Opret en tom mængde til at gemme unikke destinationer
    unique_destinations = set()
    
    # Opret en counter til statistik
    destination_counter = Counter()
    
    # Find alle Excel-filer i mappen
    excel_files = []
    for file in os.listdir(folder_path):
        if file.endswith(('.xlsx', '.xls', '.csv')):
            excel_files.append(os.path.join(folder_path, file))
    
    print(f"Fandt {len(excel_files)} filer til behandling")
    
    # Tjek om der er filer at behandle
    if not excel_files:
        print("Ingen Excel eller CSV filer fundet i den angivne mappe!")
        return set()
    
    # Bearbejd hver fil
    for i, file_path in enumerate(excel_files, 1):
        file_name = os.path.basename(file_path)
        print(f"Behandler fil {i}/{len(excel_files)}: {file_name}")
        
        try:
            # Læs fil baseret på filtype
            if file_path.endswith('.csv'):
                # For CSV-filer, læs kun 'Destination' kolonnen hvis den findes
                # Først tjek header
                with open(file_path, 'r', encoding='utf-8') as f:
                    header = f.readline().strip().split(',')
                
                # Find index for 'Destination' kolonnen (case-insensitive)
                dest_idx = None
                for idx, col in enumerate(header):
                    if col.lower() == 'destination':
                        dest_idx = idx
                        break
                
                if dest_idx is not None:
                    # Læs kun den specifikke kolonne for at spare hukommelse
                    df = pd.read_csv(file_path, usecols=[dest_idx])
                else:
                    print(f"  Advarsel: Ingen 'Destination' kolonne fundet i {file_name}")
                    continue
            else:
                # For Excel-filer
                # Først læs kolonne-navnene for at tjekke om 'Destination' findes
                excel_headers = pd.read_excel(file_path, nrows=0).columns
                
                if 'Destination' in excel_headers:
                    df = pd.read_excel(file_path, usecols=['Destination'])
                else:
                    # Prøv case-insensitive søgning
                    dest_col = None
                    for col in excel_headers:
                        if col.lower() == 'destination':
                            dest_col = col
                            break
                    
                    if dest_col:
                        df = pd.read_excel(file_path, usecols=[dest_col])
                    else:
                        print(f"  Advarsel: Ingen 'Destination' kolonne fundet i {file_name}")
                        continue
            
            # Håndter kolonne-navnet (kan variere i case)
            dest_column = None
            for col in df.columns:
                if col.lower() == 'destination':
                    dest_column = col
                    break
            
            if dest_column is None:
                print(f"  Fejl: Kunne ikke identificere 'Destination' kolonnen i {file_name}")
                continue
            
            # Fjern NaN-værdier og trim whitespace
            destinations = df[dest_column].dropna().astype(str).str.strip()
            
            # Tæl frekvenser for statistik
            file_destinations = Counter(destinations)
            destination_counter.update(file_destinations)
            
            # Tilføj til det unikke sæt
            unique_destinations.update(destinations)
            
            # Vis frekvente destinationer i denne fil
            top_destinations = file_destinations.most_common(3)
            if top_destinations:
                print(f"  Top 3 destinationer i denne fil:")
                for dest, count in top_destinations:
                    print(f"    - {dest}: {count} forekomster")
            
            print(f"  Fandt {len(file_destinations)} unikke destinationer i denne fil")
            print(f"  Samlet antal unikke destinationer indtil nu: {len(unique_destinations)}")
            
        except Exception as e:
            print(f"  Fejl ved behandling af {file_name}: {str(e)}")
    
    # Sorter destinationerne alfabetisk
    sorted_destinations = sorted(unique_destinations)
    
    # Gem resultatet til en txt-fil
    with open(output_file, 'w', encoding='utf-8') as f:
        # Skriv header med statistik
        f.write(f"# Unikke destinationer fundet på tværs af {len(excel_files)} AIS-filer\n")
        f.write(f"# Samlet antal unikke destinationer: {len(sorted_destinations)}\n")
        f.write(f"# Top 10 mest frekvente destinationer:\n")
        
        # Skriv top 10 mest almindelige destinationer med deres antal
        for dest, count in destination_counter.most_common(10):
            f.write(f"# {dest}: {count} forekomster\n")
        
        f.write("#" + "-" * 50 + "\n\n")
        
        # Skriv alle unikke destinationer
        for dest in sorted_destinations:
            f.write(f"{dest}\n")
    
    # Beregn og vis statistik
    total_time = time.time() - start_time
    print("\nOPSUMMERING:")
    print("-" * 40)
    print(f"Behandlet {len(excel_files)} filer")
    print(f"Fundet {len(unique_destinations)} unikke destinationer")
    print(f"Top 10 mest frekvente destinationer:")
    for dest, count in destination_counter.most_common(10):
        print(f"  - {dest}: {count} forekomster")
    print(f"Resultatet er gemt til: {output_file}")
    print(f"Total tid brugt: {total_time:.2f} sekunder")
    
    return unique_destinations

if __name__ == "__main__":
    # Sti til mappen med AIS-filer
    folder_path = r"C:\Users\jonas\Desktop\Design og anvendelse af kunstig inteligens\2. Semester\Projekt - Gatehouse\AIS"
    
    # Sti til output-filen
    output_file = os.path.join(folder_path, "unique_destinations.txt")
    
    # Check om stien findes
    if not os.path.exists(folder_path):
        print(f"Fejl: Mappen '{folder_path}' findes ikke!")
    else:
        # Start søgningen efter unikke destinationer
        find_unique_destinations(folder_path, output_file)