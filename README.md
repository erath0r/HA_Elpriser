# HA Elpriser

En simpel Home Assistant custom integration, der henter spotpriser fra Energy-Charts og viser:

- aktuel elpris
- de naeste 24 timers timepriser i DKK/kWh
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

Priserne bliver omregnet fra `EUR/MWh` til `DKK/kWh` med en fast kurs paa `7.46`.

De viste priser er kun spotpris og inkluderer ikke nettarif, afgifter eller moms.

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

## Diagram i Lovelace

Det pæneste resultat faar du med `ApexCharts Card`, som kan installeres via HACS:

- <https://github.com/RomRider/apexcharts-card>

Naar kortet er installeret, kan du bruge dette eksempel i et manuelt dashboard-kort:

```yaml
type: custom:apexcharts-card
graph_span: 48h
span:
  start: hour
header:
  show: true
  title: Elpriser
  show_states: true
  colorize_states: true
now:
  show: true
  color: '#d97706'
apex_config:
  chart:
    height: 320
  legend:
    show: true
  stroke:
    width: 3
  fill:
    type: gradient
    gradient:
      shadeIntensity: 0.25
      opacityFrom: 0.45
      opacityTo: 0.05
  xaxis:
    labels:
      datetimeUTC: false
  yaxis:
    decimalsInFloat: 2
series:
  - entity: sensor.elpriser_nuvaerende_elpris
    name: Naeste 24 timer
    type: column
    color: '#0f766e'
    data_generator: |
      return (entity.attributes.prices_next_24h || []).map((item) => {
        return [new Date(item.start).getTime(), item.price_dkk_kwh];
      });
  - entity: sensor.elpriser_elpris_ugeprognose
    name: Prognose
    type: line
    curve: smooth
    color: '#dc2626'
    data_generator: |
      return (entity.attributes.forecast_hourly || []).slice(0, 24).map((item) => {
        return [new Date(item.start).getTime(), item.price_dkk_kwh];
      });
```

Det giver soejler for de kendte timer og en roed, glat prognoselinje ovenpaa.

## Stoettede budzoner

Alle budzoner som Energy-Charts understoetter i `/price`, fx `DK1`, `DK2`, `DE-LU`, `SE4` og `NO2`.

## Kilde

- Energy-Charts API: <https://api.energy-charts.info/>

## GitHub

Repoet er sat op til:

- <https://github.com/erath0r/HA_Elpriser>
