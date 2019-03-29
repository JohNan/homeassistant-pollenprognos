# Home Assistant Pollennivå

Support for getting current pollen levels from Klart.se
Visit https://www.klart.se/se/pollenprognoser/ to find available cities

States
* 0 = None
* 1 = Low
* 2 = Medium
* 3 = High
* 4 = Extra high

Place the folder `pollenniva` in `<HA_CONFIG_DIR>/custom_components`
Add configuration to your `configuration.yaml`

This will create sensors named `senson.pollenniva_CITY_ALLERGEN` and the state will be the current level of that allergen

Example configuration

```
sensor:
  - platform: pollenniva
    scan_interval: 4 (default, optional)
    sensors:
      - city: Stockholm
        allergen: Gräs
      - city: Stockholm
        allergen: Hassel
      - city: Östersund
        allergen: Hassel
```