# HA Elpriser

En simpel Home Assistant custom integration, der henter spotpriser fra Energy-Charts og viser:

- aktuel elpris
- de naeste 24 timers timepriser
- en 7-dages prisprognose markeret som estimat

## HACS

Repoet er gjort klar til HACS som custom repository.

Naar repoet ligger offentligt paa GitHub, kan du installere det saadan:

1. Aabn HACS i Home Assistant.
2. Tryk paa menuen med de tre prikker.
3. Vaelg `Custom repositories`.
4. Indsaet GitHub-URL'en til repoet.
5. Vaelg typen `Integration`.
6. Installer `HA Elpriser`.
7. Genstart Home Assistant.

## Funktioner

Integrationen bruger `https://api.energy-charts.info/price` til faktiske day-ahead spotpriser.

Energy-Charts udstiller ikke en officiel 7-dages prisprognose i samme endpoint, saa denne integration beregner i stedet et estimat ud fra de seneste 28 dages historiske priser med match paa ugedag og klokkeslaet. Prognosen skal derfor ses som vejledende, ikke som en markedspris.

## Installation

Hvis du ikke bruger HACS endnu:

1. Kopier `custom_components/elpriser` til din Home Assistant `custom_components` mappe.
2. Genstart Home Assistant.
3. Tilfoej dette til `configuration.yaml`:

```yaml
sensor:
  - platform: elpriser
    name: Elpriser
    bidding_zone: DK1
    forecast_days: 7
```

## Entiteter

Integrationen opretter to sensorer:

- `sensor.elpriser_nuvaerende_elpris`
- `sensor.elpriser_elpris_ugeprognose`

Den foerste sensor har attributter med `prices_next_24h`, `cheapest_hour` og `most_expensive_hour`.

Den anden sensor har attributter med `forecast_hourly`, `forecast_daily` og `forecast_method`.

## Stoettede budzoner

Alle budzoner som Energy-Charts understoetter i `/price`, fx `DK1`, `DK2`, `DE-LU`, `SE4` og `NO2`.

## Kilde

- Energy-Charts API: <https://api.energy-charts.info/>

## Foer du publicerer paa GitHub

Opdater disse to felter i `custom_components/elpriser/manifest.json` med din rigtige GitHub URL:

- `documentation`
- `issue_tracker`

Som den staar nu bruger filen en `OWNER` placeholder, saa det er tydeligt hvad der skal udskiftes.
