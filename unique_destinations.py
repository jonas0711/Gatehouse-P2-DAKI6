import csv
from collections import Counter
import os
import time

def tael_destinationer(filsti, output_filsti="destination_analyse.csv"):
    """
    Læser en CSV-fil med AIS-data, tæller unikke destinationer og gemmer resultatet til en fil.
    Optimeret for store filer med statusopdateringer.
    
    Args:
        filsti (str): Stien til CSV-filen med AIS-data
        output_filsti (str): Stien hvor resultatet skal gemmes
    
    Returns:
        None: Udskriver status til konsollen og gemmer resultater til fil
    """
    # Start timer for at måle udførelsestid
    start_tid = time.time()
    
    # Opret en tom Counter til at tælle destinationer
    destination_taeller = Counter()
    
    # Få filstørrelse for at estimere fremskridt
    filstoerrelse = os.path.getsize(filsti)
    print(f"Påbegynder analyse af fil: {filsti}")
    print(f"Filstørrelse: {filstoerrelse / (1024 * 1024):.2f} MB")
    
    try:
        # Identificer destination-kolonnen først ved kun at læse header
        with open(filsti, 'r', encoding='utf-8') as fil:
            # Læs kun første linje for at identificere kolonner
            header = next(csv.reader(fil))
            
            # Find kolonnen der indeholder destination
            dest_index = None
            for i, kolonne in enumerate(header):
                if 'Destination' == kolonne:
                    dest_index = i
                    print(f"Fandt 'Destination' kolonne ved index {i}")
                    break
                elif 'dest' in kolonne.lower():
                    dest_index = i
                    print(f"Fandt destination-lignende kolonne '{kolonne}' ved index {i}")
                    break
            
            if dest_index is None:
                print("Kunne ikke finde en destinationskolonne i filen.")
                return
        
        # Nu læs hele filen og tæl destinationer
        with open(filsti, 'r', encoding='utf-8') as fil:
            reader = csv.reader(fil)
            next(reader)  # Spring header over
            
            linjer_behandlet = 0
            sidste_update = time.time()
            update_interval = 5  # Sekunder mellem statusopdateringer
            
            for række in reader:
                linjer_behandlet += 1
                
                # Vis fremskridtsindikator
                if time.time() - sidste_update > update_interval:
                    position = fil.tell()
                    procent_færdig = (position / filstoerrelse) * 100
                    elapsed = time.time() - start_tid
                    print(f"Behandlet {linjer_behandlet:,} linjer ({procent_færdig:.1f}%) - Tid brugt: {elapsed:.1f} sekunder")
                    sidste_update = time.time()
                
                # Tæl destinationen hvis den ikke er tom
                if len(række) > dest_index:
                    destination = række[dest_index].strip()
                    if destination:  # Ignorer tomme værdier
                        destination_taeller[destination] += 1
    
    except Exception as e:
        print(f"Fejl under læsning af filen: {e}")
        return
    
    # Beregn total tid
    total_tid = time.time() - start_tid
    
    # Gem resultater til fil
    try:
        with open(output_filsti, 'w', newline='', encoding='utf-8') as output_fil:
            writer = csv.writer(output_fil)
            writer.writerow(['Destination', 'Antal'])
            
            for destination, antal in sorted(destination_taeller.items(), 
                                          key=lambda x: x[1], reverse=True):
                writer.writerow([destination, antal])
        
        print(f"\nResultater gemt til {output_filsti}")
    except Exception as e:
        print(f"Fejl ved gemning af fil: {e}")
    
    # Udskriv opsummering
    print("\nOPSUMMERING:")
    print("-" * 40)
    
    if not destination_taeller:
        print("Ingen destinationer fundet.")
        return
    
    # Vis kun de 20 mest almindelige destinationer i terminalen
    print("Top 20 destinationer:")
    for destination, antal in destination_taeller.most_common(20):
        print(f"{destination}: {antal}")
    
    print("-" * 40)
    print(f"Antal unikke destinationer: {len(destination_taeller)}")
    print(f"Totalt antal registrerede destinationer: {sum(destination_taeller.values())}")
    print(f"Total tid brugt: {total_tid:.2f} sekunder")

# Eksempelkørsel
if __name__ == "__main__":
    # Sti til AIS-data filen
    filsti = "aisdk-2025-02-27/aisdk-2025-02-27.csv"
    output_filsti = "destinations_analyse_output.csv"
    
    if not os.path.exists(filsti):
        print(f"Filen '{filsti}' findes ikke. Kontroller stien og prøv igen.")
    else:
        tael_destinationer(filsti, output_filsti)