# AIS Database Struktur og Indhold

## Database Oversigt
- **Databasenavn**: ais.db
- **Databasetype**: SQLite
- **Samlet antal tabeller**: 3676 (som vist i første skærmbillede)

## Hovedtabeller og Struktur

### Ships Tabel
- **Tabeltype**: Hovedtabel som indeholder referencer til individuelle skibstabeller
- **Primærnøgle**: `table_name` (TEXT NOT NULL UNIQUE)
- **Beskrivelse**: Indeholder navne på alle skibstabeller i databasen
- **Antal poster**: Ca. 3.675 skibe (baseret på skærmbilledet)

### Individuelle Skibstabeller (f.eks. ship_205011000)
Hver skibstabel indeholder AIS-data for ét specifikt skib, identificeret ved MMSI-nummer i tabelnavnet:

- **Struktur**: `CREATE TABLE ship_MMSINUMMER (Timestamp DATETIME NOT NULL, Latitude FLOAT, Longitude FLOAT, Navigational_status [...])`
- **Primærnøgle**: Antageligvis `Timestamp`
- **Kolonner**:
  1. **Timestamp** (DATETIME NOT NULL) - Tidspunktet for AIS-signalet
  2. **Latitude** (FLOAT) - Skibets breddegrad
  3. **Longitude** (FLOAT) - Skibets længdegrad
  4. **Navigational_status** - Skibets navigationsstatus
  5. **ROT** (FLOAT) - Rate of Turn, skibets drejningshastighed
  6. **SOG** (FLOAT) - Speed Over Ground, skibets hastighed
  7. **COG** (FLOAT) - Course Over Ground, skibets kurs
  8. **Heading** (FLOAT) - Skibets retning
  9. **Cargo_type** - Type af last
  10. **Width** (FLOAT) - Skibets bredde
  11. **Length** (FLOAT) - Skibets længde
  12. **Draught** (FLOAT) - Skibets dybgang
  13. **Destination** (TEXT) - Skibets planlagte destination

## Dataeksempler og Karakteristika

### Ships Tabel Eksempler
Tabellen indeholder skibsidentifikatorer som:
- ship_235108525
- ship_219000604
- ship_219000179
- ship_219423000
- ...og flere tusinde andre skibsidentifikatorer

### Skibsdata Eksempel (fra ship_205011000)
Data for hvert skib er organiseret som tidsserie med målinger hver ~10 sekunder:

| Timestamp          | Latitude  | Longitude | Nav_status | ROT | SOG | COG   | Heading | Cargo | Width | Length | Draught | Destination |
|-------------------|-----------|-----------|------------|-----|-----|-------|---------|-------|-------|--------|----------|-------------|
| 2025-03-10 00:04:21 | 54.673215 | 13.563692 |            | 0   | 0.0 | 8.8  | 136.8   | 135.0 | 'Null' | 12.0  | 89.0    | 5.3        | PLSZZ PS  |
| 2025-03-10 00:04:25 | 54.67289  | 13.564233 |            | 0   | 0.0 | 8.8  | 135.9   | 134.0 | 'Null' | 12.0  | 89.0    | 5.3        | PLSZZ PS  |
| 2025-03-10 00:04:35 | 54.672597 | 13.564722 |            | 0   | 0.0 | 8.8  | 135.9   | 134.0 | 'Null' | 12.0  | 89.0    | 5.3        | PLSZZ PS  |

## Databasestrukturens Anvendelse

### Relationel Organisation
- Databasen er organiseret med én primær indekstabel (`Ships`) og tusindvis af individuelle skibstabeller
- Dette design tillader effektiv lagring og adgang til store mængder tidsseriedata for hvert skib

### Dataanvendelse
- **Tidsserieopbygning**: Hver skibstabel indeholder kronologisk sorterede datapunkter, ideelle til tidsserieanalyse
- **Positionsforudsigelse**: Kolonner som Timestamp, Latitude, Longitude, SOG, COG og Heading danner grundlaget for positionsforudsigelsesmodeller
- **Skibsidentifikation**: MMSI-nummeret indkodet i tabelnavnet (f.eks. ship_205011000) fungerer som unik identifikator

### Datamængde og Kvalitet
- Databasen indeholder store mængder AIS-data med flere tusinde skibe
- Hvert skib har tusindvis af målinger (f.eks. 5.521 rækker i ship_205011000-tabellen)
- Timestamp-intervallerne er relativt regelmæssige (ca. 10-11 sekunders mellemrum), hvilket giver konsistente tidsserier

## Potentielle Anvendelser til Analyseformål
- **Ruteprognoser**: Forudsigelse af fremtidige skibspositioner baseret på historiske mønstre
- **Trafikanalyse**: Identifikation af trafikmønstre og -tendenser i bestemte maritime områder
- **Afvigelsessporing**: Identifikation af usædvanlig skibsadfærd baseret på historiske ruter
- **Ankomsttidsprognose**: Beregning af forventede ankomsttider til destinationer baseret på aktuel position og hastighed

## Tekniske Overvejelser
- **Lagringseffektivitet**: Opdelingen i separate tabeller pr. skib optimerer forespørgselseffektiviteten for individuelle skibe
- **Skalerbarhed**: Strukturen tillader let tilføjelse af nye skibe som separate tabeller
- **Dataindsamlingsperiode**: Baseret på timestampene ser det ud til at være nyere data (2025-03-10) 