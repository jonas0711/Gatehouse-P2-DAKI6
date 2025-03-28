import os
import pandas as pd
from collections import Counter
import time

def find_unique_destinations_single_file(file_path, output_file="unique_destinations.txt"):
    """
    Finder alle unikke værdier i kolonnen 'Destination' i én specifik CSV- eller Excel-fil.
    Gemmer resultatet til en txt-fil.
    
    Args:
        file_path (str): Stien til den AIS-fil der skal behandles
        output_file (str): Stien til output filen
        
    Returns:
        set: Et sæt med alle unikke destinationsværdier
    """
    print(f"Starter søgning i filen: {file_path}")
    start_time = time.time()

    unique_destinations = set()
    destination_counter = Counter()
    file_name = os.path.basename(file_path)

    try:
        if file_path.endswith('.csv'):
            # Tjek først om 'Destination' findes i header
            with open(file_path, 'r', encoding='utf-8') as f:
                header = f.readline().strip().split(',')

            dest_idx = None
            for idx, col in enumerate(header):
                if col.lower() == 'destination':
                    dest_idx = idx
                    break

            if dest_idx is not None:
                df = pd.read_csv(file_path, usecols=[dest_idx])
            else:
                print(f"  Advarsel: Ingen 'Destination' kolonne fundet i {file_name}")
                return set()
        else:
            print("  Filtypen understøttes ikke – kun CSV i dette script")
            return set()

        # Identificér kolonnen uanset case
        dest_column = next((col for col in df.columns if col.lower() == 'destination'), None)

        if dest_column is None:
            print(f"  Fejl: 'Destination' kolonnen ikke fundet i {file_name}")
            return set()

        destinations = df[dest_column].dropna().astype(str).str.strip()
        file_destinations = Counter(destinations)
        destination_counter.update(file_destinations)
        unique_destinations.update(destinations)

        # Print statistik
        top_destinations = file_destinations.most_common(3)
        if top_destinations:
            print(f"  Top 3 destinationer:")
            for dest, count in top_destinations:
                print(f"    - {dest}: {count} forekomster")

        print(f"  Fundet {len(file_destinations)} unikke destinationer i filen")
        print(f"  Samlet antal: {len(unique_destinations)}")

        # Gem til fil
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Unikke destinationer i filen: {file_name}\n")
            f.write(f"# Antal unikke destinationer: {len(unique_destinations)}\n")
            f.write(f"# Top 10 mest frekvente:\n")
            for dest, count in destination_counter.most_common(10):
                f.write(f"# {dest}: {count} forekomster\n")
            f.write("#" + "-" * 50 + "\n\n")
            for dest in sorted(unique_destinations):
                f.write(f"{dest}\n")

        total_time = time.time() - start_time
        print("\nOPSUMMERING:")
        print("-" * 40)
        print(f"Fil behandlet: {file_name}")
        print(f"Unikke destinationer: {len(unique_destinations)}")
        print(f"Resultat gemt i: {output_file}")
        print(f"Tid brugt: {total_time:.2f} sekunder")

        return unique_destinations

    except Exception as e:
        print(f"  Fejl under behandling: {str(e)}")
        return set()

if __name__ == "__main__":
    # Angiv sti til den ene CSV-fil
    file_path = r"C:\Users\jonas\Desktop\Design og anvendelse af kunstig inteligens\2. Semester\Projekt - Gatehouse\AIS\aisdk-2025-03-10.csv"

    # Output-fil
    output_file = r"C:\Users\jonas\Desktop\Design og anvendelse af kunstig inteligens\2. Semester\Projekt - Gatehouse\AIS\unique_destinations.txt"

    # Tjek filen findes
    if not os.path.exists(file_path):
        print(f"Fejl: Filen '{file_path}' findes ikke!")
    else:
        find_unique_destinations_single_file(file_path, output_file)
