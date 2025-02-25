# CSV-kolonner og Deres Anvendelse

## 1. Timestamp
- **Beskrivelse**: Tidspunktet, hvor beskeden er modtaget fra AIS-basestationen
- **Anvendelse**: Grundlæggende for at sætte data i en tidsserie; bruges til at indeksere og segmentere datapunkter over tid

## 2. Type of mobile
- **Beskrivelse**: Angiver hvilken type mål beskeden stammer fra (fx Class A AIS Vessel, Class B AIS Vessel)
- **Anvendelse**: Kan anvendes til at filtrere data - f.eks. fokusere på en bestemt skibstype (fx containerskibe)

## 3. MMSI
- **Beskrivelse**: Unikt identifikationsnummer for skibet
- **Anvendelse**: Identifikation af individuelle skibe; nyttigt til at spore historiske ruter og adfærd for et bestemt skib

## 4. Latitude
- **Beskrivelse**: Breddegrad for den rapporterede position
- **Anvendelse**: Sammen med Longitude danner denne kolonne den primære positionsinformation, som er central for at forudsige fremtidige positioner

## 5. Longitude
- **Beskrivelse**: Længdegrad for den rapporterede position
- **Anvendelse**: Som med Latitude, bruges til at placere skibet geografisk og udgør en del af inputtet til positionsforudsigelsen

## 6. Navigational status
- **Beskrivelse**: Angiver skibets navigationsstatus (fx 'Under way using engine', 'Engaged in fishing')
- **Anvendelse**: Kan hjælpe med at vurdere skibets driftstilstand og dermed påvirke forudsigelsesmodellen - f.eks. ændres adfærden, hvis skibet fisker

## 7. ROT (Rate of Turn)
- **Beskrivelse**: Angiver skibets drejningshastighed
- **Anvendelse**: Vigtig for at forstå, om skibet foretager markante kursændringer; kan være med til at forudsige ruteafvigelser

## 8. SOG (Speed Over Ground)
- **Beskrivelse**: Skibets hastighed over jordens overflade
- **Anvendelse**: Kritisk for at beregne, hvor langt et skib kan bevæge sig i et givent tidsrum; påvirker forudsigelser af fremtidige positioner

## 9. COG (Course Over Ground)
- **Beskrivelse**: Den kurs, som skibet følger baseret på den faktiske bevægelse
- **Anvendelse**: Anvendes til at estimere skibets rute og til at modellere kursændringer over tid

## 10. Heading
- **Beskrivelse**: Skibets retning, som angivet af skibets instrumenter
- **Anvendelse**: Kan give en yderligere indikator på skibets orientering og sammenlignes med COG for at vurdere eventuelle afvigelser

## 11. IMO
- **Beskrivelse**: Et andet unikt identifikationsnummer for skibe (bruges internationalt)
- **Anvendelse**: Kan supplere MMSI til at sikre entydig identifikation af et skib

## 12. Callsign
- **Beskrivelse**: Skibets radiokaldesign
- **Anvendelse**: Muligt nyttigt til yderligere identifikation og verifikation af skibets identitet

## 13. Name
- **Beskrivelse**: Skibets navn
- **Anvendelse**: Bruges til rapportering og visualisering; kan hjælpe med at gruppere eller filtrere data baseret på skibstype eller operatør

## 14. Ship type
- **Beskrivelse**: Angiver skibets type ud fra AIS klassifikation
- **Anvendelse**: Central for at vælge et specifikt segment (fx containerskibe) for forudsigelsesmodellen, hvilket kan reducere kompleksiteten

## 15. Cargo type
- **Beskrivelse**: Type af gods, skibet transporterer
- **Anvendelse**: Kan give indikation af skibets operationelle karakter - nogle gods-typer kan f.eks. være forbundet med faste ruter

## 16. Width
- **Beskrivelse**: Skibets bredde
- **Anvendelse**: Kan være relevant for sikkerhedsanalysen (f.eks. bredden kan påvirke manøvredygtigheden) men er mindre central for positionsforudsigelse

## 17. Length
- **Beskrivelse**: Skibets længde
- **Anvendelse**: Som med width kan den bruges til at validere skibstypen og understøtte filterprocesser

## 18. Type of position fixing device
- **Beskrivelse**: Angiver hvilken type positionsudstyr, der er brugt (f.eks. GPS)
- **Anvendelse**: Kan bruges til at vurdere datakvalitet eller pålideligheden af positionsoplysningerne

## 19. Draught
- **Beskrivelse**: Skibets dybgang, som angiver, hvor dybt det går under vand
- **Anvendelse**: Relevant for nogle scenarier (f.eks. i forhold til havbundsforhold) men ikke nødvendigvis direkte for positionsforudsigelse

## 20. Destination
- **Beskrivelse**: Det planlagte destination for skibet, som rapporteret via AIS
- **Anvendelse**: Vigtigt input til at forudsige, hvilken havn skibet sandsynligvis nærmer sig, og kan sammenholdes med forudsigelser af rute og ankomsttidspunkt

## 21. ETA (Estimated Time of Arrival)
- **Beskrivelse**: Den estimerede ankomsttid, hvis oplyst
- **Anvendelse**: Kan bruges som et referencepunkt eller label for at træne og validere forudsigelsesmodellen med hensyn til tidsdimensionen

## 22. Data source type
- **Beskrivelse**: Angiver, hvilken type datakilde beskeden kommer fra (f.eks. AIS)
- **Anvendelse**: Kan hjælpe med at sikre ensartethed og kvalitet i dataudvalget

## 23. Size A (Length from GPS to the bow)
## 24. Size B (Length from GPS to the stern)
## 25. Size C (Length from GPS to starboard side)
## 26. Size D (Length from GPS to port side)
- **Beskrivelse**: Dimensioner af skibet målt fra GPS-positionen i forskellige retninger
- **Anvendelse**: Kan bruges til at validere skibstype, hjælpe med visualisering og i nogle tilfælde justere forudsigelser baseret på skibets fysiske størrelse (f.eks. manøvreringsevne)

# Hvordan CSV-dataene Understøtter Positionsforudsigelse

## Tidsserieopbygning
Ved at bruge Timestamp sammen med Latitude, Longitude, SOG, COG og Heading kan du opbygge en tidsserie for hver enkelt skib (identificeret med MMSI/IMO). Denne tidsserie er grundlaget for at træne en model (f.eks. LSTM) til at forudsige fremtidige positioner.

## Feature Engineering
Ud fra de tilgængelige kolonner kan du udlede ekstra features såsom:
- Ændringer i hastighed (delta SOG) og kurs (delta COG/ROT) over tid
- Perioder med manglende data (f.eks. hvornår et skib pludselig ikke sender signal)
- Skibstype-baseret adfærd (brug Ship type, Cargo type og dimensioner til at differentiere mellem forskellige skibstyper)

## Validations- og Referencepunkter
Destination og ETA kan anvendes til at validere, om forudsigelsen stemmer overens med skibets planlagte rute og ankomsttid. Dette er især relevant, når modellen skal forudsige, hvilket havnepunkt et skib nærmer sig, og hvornår.

## Datakvalitet og Rensning
Oplysninger om navigationsstatus, type af positionsfixeringsenhed og data source type hjælper med at vurdere datakvaliteten og filtrere ud data med for lav pålidelighed eller dubleringer.

# Opsummering
CSV-filen indeholder omfattende AIS-information, som giver et solidt grundlag for at:
- Udvikle en tidsserie-model (f.eks. en LSTM) til at forudsige skibenes positioner 1-24 timer frem
- Uddrage relevante features såsom hastighed, kurs, ændringer i ROT og andre navigationsparametre
- Validere forudsigelser ved at sammenholde med planlagte destinationer og ETA

Denne data kan dermed understøtte projektets mål om at udvikle et prædiktivt system, der kan håndtere de dynamiske forhold i maritime miljøer og levere brugbare indsigter til både logistik, sikkerhed og overvågning.
