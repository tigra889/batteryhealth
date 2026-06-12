# BatteryHealth Sensor

## Changelog

### v1.4.0 (2026-06-12)
- SOH measurement section finalized only when SOC rises again (no fixed SOC-drop interval)
- Only one SOH sample recorded per discharge section to avoid skewing the average
- Full-charge plateau detection: positive power at SOC >= 99.5 % is not counted as discharge energy
- New service batteryhealth.reset_history to clear SOH history (optional entry_id parameter)
- New config option soc_rise_hysteresis: configurable SOC rise threshold for section detection (default 0.3 %)
- Sensor display name now follows config entry title — rename takes effect after integration reload
- Dashboard updated for multiple devices: auto-discovery overview tab and per-device detail tabs

### v1.3.0
- Initial public release via HACS

## EN

### Overview

This integration estimates battery SoH (State of Health) from SOC trend and power.
Setup is config-flow-only in Home Assistant.

### Setup

1. Home Assistant -> Settings -> Devices & Services -> Add Integration.
2. Select BatteryHealth Sensor.
3. Fill in:
  - name
  - soc_entity (battery SOC sensor, 0..100 %)
  - power_entity (power sensor)
  - nominal_capacity_kwh (nominal battery capacity)
  - soc_rise_hysteresis (SOC increase threshold to close a section, default 0.3 %)
  - invert_power_sign (enable only if discharge is reported as negative)

### Install via HACS

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Open the menu and select Custom repositories.
4. Repository URL: https://github.com/tigra889/batteryhealth
5. Category: Integration.
6. Install BatteryHealth Sensor and restart Home Assistant.
7. Add the integration in Settings -> Devices & Services.

### Calculation Logic

1. Integrate discharge energy from positive power:
  - delta_hours = (now - last_update).seconds / 3600
  - discharge_power_w = max(power_value, 0)
  - delta_energy_kwh = (discharge_power_w / 1000) * delta_hours
2. Update energy counters:
  - discharged_energy_kwh += delta_energy_kwh
  - discharged_energy_total_kwh += delta_energy_kwh
3. Manage SOC reference:
  - first valid SOC sets soc_reference
  - if soc_value > soc_reference + 0.3, reset section values
4. SOH measurement section behavior:
  - a section starts at current SOC reference
  - while SOC falls, the minimum SOC in section is tracked
  - SOH is finalized only when SOC rises above the reference (new section start)
  - no fixed SOC interval threshold is used
5. Formulas:
  - soc_drop = soc_reference - soc_min_in_section
  - estimated_capacity_kwh = discharged_energy_kwh / (soc_drop / 100)
  - raw_health_percent = (estimated_capacity_kwh / nominal_capacity_kwh) * 100
  - soh_current = round(max(0, raw_health_percent), 2)
  - soh_average = mean(soh_history)
  - full_charge_cycles = discharged_energy_total_kwh / nominal_capacity_kwh

### Full Flowchart

```mermaid [..\SOC and Power State Change-2026-06-11-201809.png]
flowchart TD 
   A[State change event<br/>SOC or Power] --> B{SOC entity available?}
   B -- No --> B1[Set SOC/Power outputs to None<br/>Notify listeners] --> Z[End]
   B -- Yes --> C{SOC value valid?}
   C -- No --> C1[Set SOC-related outputs to None<br/>Notify listeners] --> Z
   C -- Yes --> D[Parse SOC in range 0..100]

   D --> E{Power entity configured?}
  E -- No --> E1[Power value not available]
   E -- Yes --> F{Power value valid?}
  F -- No --> F1[Power value invalid or unavailable]
   F -- Yes --> F2[Parse Power<br/>kW to W if needed<br/>optional sign inversion]

   E1 --> G
   F1 --> G
   F2 --> G

  G{Last update exists} -- No --> H[Store current timestamp as last update]
  G -- Yes --> I[Compute time delta in hours]
  I --> J[Compute delta energy from positive power]
  J --> K[Increase section discharge energy]
  K --> L[Increase total discharge energy]
   L --> H

  H --> M{SOC reference exists}
  M -- No --> M1[Set SOC reference from current SOC]
  M -- Yes --> N{Current SOC above reference plus hysteresis}
   N -- Yes --> N1[Start new section<br/>Reset section values]
   N -- No --> O
   M1 --> O
   N1 --> O

  O[Compute soc drop from reference and current SOC] --> P{SOH preconditions met?<br/>soc drop at least 3 percent and energy positive and nominal positive}
  P -- No --> P1[No current SOH output]
   P -- Yes --> Q[Compute C_estimated]
  Q --> R[Compute raw health percent]
  R --> S[Set current SOH and append history]

  P1 --> T[Notify listeners about updated state]
   S --> T
   T --> Z
```

### Simplified SOH Flowchart

```mermaid
flowchart TD
  A[SOC and Power update] --> B[Compute soc drop from reference and current SOC]
  B --> C{Is soc drop at least 3 percent}
   C -- No --> X[No SOH output]
  C -- Yes --> D{Is discharged energy positive and nominal capacity positive}
   D -- No --> X
  D -- Yes --> E[Compute estimated capacity from discharged energy and soc drop]
  E --> F[Compute raw health percent from estimated and nominal capacity]
  F --> G[Set current soh from raw health percent with lower bound zero]
   G --> H[Append soh_current to history]
```

### Entities Created

Per config entry, these sensor entities are created:

- SOH Current (%)
- SOH Average (%)
- C Estimated (kWh)
- C Nominal (kWh)
- Discharged Energy (kWh, section-based)
- Discharged Energy Total (kWh, cumulative)
- Full Charge Cycles
- SOC Reference (%)
- SOC Drop (%)
- SOC Current (%)
- Power Current (W)
- SOH Raw (%)
- SOH Measurements (count)
- Calculation Ready (0 or 1)

### Notes

- Discharge should be positive power. Otherwise enable invert_power_sign.
- If SOC or Power is temporarily unavailable, calculation pauses until valid states return.
- SOH is section-based and one sample is finalized when SOC rises and a new section begins.
- Only one SOH sample is added to history per discharge section to avoid skewing the average.
- At SOC near 100 % on a full-charge plateau, positive power is ignored for energy integration to avoid top-off distortion.

### Service

- Service: batteryhealth.reset_history
- Optional field: entry_id (reset one config entry)
- Without entry_id, SOH history is reset for all BatteryHealth entries.

## DE

### Ueberblick

Diese Integration schaetzt den Batterie-SoH (State of Health) aus SOC-Verlauf und Leistung.
Die Einrichtung erfolgt ausschliesslich ueber den Config Flow.

### Einrichtung

1. Home Assistant -> Einstellungen -> Geraete & Dienste -> Integration hinzufuegen.
2. BatteryHealth Sensor waehlen.
3. Folgende Felder ausfuellen:
  - name
  - soc_entity (Batterie-SOC-Sensor, 0..100 %)
  - power_entity (Leistungssensor)
  - nominal_capacity_kwh (Nennkapazitaet)
  - soc_rise_hysteresis (SOC-Anstieg fuer Abschnittsabschluss, Standard 0.3 %)
  - invert_power_sign (nur aktivieren, wenn Entladung negativ geliefert wird)

### Installation ueber HACS

1. HACS in Home Assistant oeffnen.
2. Zu Integrations wechseln.
3. Menue oeffnen und Benutzerdefinierte Repositories waehlen.
4. Repository URL: https://github.com/tigra889/batteryhealth
5. Kategorie: Integration.
6. BatteryHealth Sensor installieren und Home Assistant neu starten.
7. Integration unter Einstellungen -> Geraete & Dienste hinzufuegen.

### Berechnungslogik

1. Entladeenergie wird aus positiver Leistung integriert:
  - delta_hours = (now - last_update).seconds / 3600
  - discharge_power_w = max(power_value, 0)
  - delta_energy_kwh = (discharge_power_w / 1000) * delta_hours
2. Energiezaehler werden aktualisiert:
  - discharged_energy_kwh += delta_energy_kwh
  - discharged_energy_total_kwh += delta_energy_kwh
3. SOC-Referenz wird verwaltet:
  - erste gueltige SOC-Messung setzt soc_reference
  - bei soc_value > soc_reference + 0.3 startet ein neuer Abschnitt
4. Verhalten je SOH-Messabschnitt:
  - ein Abschnitt startet bei aktueller SOC-Referenz
  - waehrend SOC faellt, wird der minimale SOC im Abschnitt verfolgt
  - SOH wird erst abgeschlossen, wenn SOC wieder ueber die Referenz steigt (neuer Abschnitt)
  - es gibt keinen festen SOC-Intervall-Schwellwert
5. Formeln:
  - soc_drop = soc_reference - soc_min_in_section
  - estimated_capacity_kwh = discharged_energy_kwh / (soc_drop / 100)
  - raw_health_percent = (estimated_capacity_kwh / nominal_capacity_kwh) * 100
  - soh_current = round(max(0, raw_health_percent), 2)
  - soh_average = mean(soh_history)
  - full_charge_cycles = discharged_energy_total_kwh / nominal_capacity_kwh

### Vollstaendiger Ablauf

```mermaid
flowchart TD
   A[Statusaenderung<br/>SOC oder Leistung] --> B{SOC-Entitaet vorhanden?}
   B -- Nein --> B1[Werte auf None setzen<br/>Listener benachrichtigen] --> Z[Ende]
   B -- Ja --> C{SOC gueltig?}
   C -- Nein --> C1[SOC-Werte auf None setzen<br/>Listener benachrichtigen] --> Z
   C -- Ja --> D[SOC parsen 0..100]

   D --> E{Power-Entitaet konfiguriert?}
  E -- Nein --> E1[Power Wert nicht verfuegbar]
   E -- Ja --> F{Power gueltig?}
  F -- Nein --> F1[Power Wert ungueltig oder unavailable]
   F -- Ja --> F2[Power parsen<br/>kW nach W falls noetig<br/>optional Vorzeichen invertieren]

   E1 --> G
   F1 --> G
   F2 --> G

  G{Last Update vorhanden} -- Nein --> H[Aktuellen Zeitstempel als Last Update speichern]
  G -- Ja --> I[Zeitdifferenz in Stunden berechnen]
  I --> J[Delta Energie aus positiver Leistung berechnen]
  J --> K[Abschnitts Energie erhoehen]
  K --> L[Gesamt Energie erhoehen]
   L --> H

  H --> M{SOC Referenz vorhanden}
  M -- Nein --> M1[SOC Referenz aus aktuellem SOC setzen]
  M -- Ja --> N{Aktueller SOC ueber Referenz plus Hysterese}
   N -- Ja --> N1[Neuen Abschnitt starten<br/>Abschnittswerte resetten]
   N -- Nein --> O
   M1 --> O
   N1 --> O

  O[SOC Drop aus Referenz und aktuellem SOC berechnen] --> P{SOH Bedingungen erfuellt?<br/>SOC Drop mindestens 3 Prozent und Energie positiv und Nennkapazitaet positiv}
  P -- Nein --> P1[Kein aktueller SOH Wert]
   P -- Ja --> Q[C_estimated berechnen]
  Q --> R[Roh SoH Prozent berechnen]
  R --> S[Aktuellen SOH setzen und Historie erweitern]

  P1 --> T[Listener ueber neuen Zustand benachrichtigen]
   S --> T
   T --> Z
```

### Vereinfachter SOH-Ablauf

```mermaid
flowchart TD
  A[SOC und Power Update] --> B[SOC Drop aus Referenz und aktuellem SOC berechnen]
  B --> C{Ist SOC Drop mindestens 3 Prozent}
   C -- Nein --> X[Kein SOH-Wert]
  C -- Ja --> D{Ist entladene Energie positiv und Nennkapazitaet positiv}
   D -- Nein --> X
  D -- Ja --> E[C estimated aus entladener Energie und SOC Drop berechnen]
  E --> F[Roh SoH Prozent aus C estimated und C nominal berechnen]
  F --> G[Aktuellen SoH setzen mit Untergrenze null]
   G --> H[soh_current in Historie speichern]
```

### Erzeugte Entitaeten

Pro Config Entry werden diese Sensoren erstellt:

- SOH Current (%)
- SOH Average (%)
- C Estimated (kWh)
- C Nominal (kWh)
- Discharged Energy (kWh, abschnittsbezogen)
- Discharged Energy Total (kWh, kumulativ)
- Full Charge Cycles
- SOC Reference (%)
- SOC Drop (%)
- SOC Current (%)
- Power Current (W)
- SOH Raw (%)
- SOH Measurements (Anzahl)
- Calculation Ready (0 oder 1)

### Hinweise

- Entladung sollte als positive Leistung vorliegen. Sonst invert_power_sign aktivieren.
- Wenn SOC oder Leistung kurz unavailable ist, pausiert die Berechnung bis wieder gueltige Werte vorliegen.
- Die SOH-Berechnung ist abschnittsbasiert; ein Messwert wird abgeschlossen, wenn SOC wieder steigt und ein neuer Abschnitt beginnt.
- Pro Entladeabschnitt wird nur ein SOH-Wert in die Historie geschrieben, damit der Mittelwert nicht verzerrt.
- Bei SOC nahe 100 % auf dem Voll-Ladeplateau wird positive Leistung nicht als Energie integriert, um Top-Off-Verzerrung zu vermeiden.

### Service

- Service: batteryhealth.reset_history
- Optionales Feld: entry_id (setzt nur einen Config Entry zurueck)
- Ohne entry_id wird die SOH-Historie fuer alle BatteryHealth-Entries zurueckgesetzt.
