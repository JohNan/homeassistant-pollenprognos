# Home Assistant Pollennivå

Support for getting current pollen levels from Pollenkollen.se
Visit https://pollenkoll.se/pollenprognos/ to find available cities
Visit https://pollenkoll.se/pollenprognos-ostersund/ to find available allergens

Available states:

```
STATES = {
    "i.h.": 0,
    "L": 1,
    "L-M": 2,
    "M": 3,
    "M-H": 4,
    "H": 5,
    "H-H+": 6
}
``` 

Place the folder `pollenniva` in `<HA_CONFIG_DIR>/custom_components`
Add configuration to your `configuration.yaml`

This will create sensors named `senson.pollenniva_CITY_ALLERGEN_day_[0-3]` and the state will be the current level of that allergen.

Example configuration

```
sensor:
  - platform: pollenniva
    scan_interval: 4 # (default, optional)
    state_as_string: false # (default, optional, show states as strings as per STATES above)
    sensors:
      - city: Stockholm
        days_to_track: 3 # (0-3, optional)
        allergens:
          - Gräs
          - Hassel
      - city: Östersund
        allergens:
          - Hassel
```



Custom card for Lovelace can be found here:
https://github.com/isabellaalstrom/pollenkoll-card

<img src="https://github.com/isabellaalstrom/pollenkoll-card/blob/master/pollenkoll-card.png" alt="Pollenkoll Lovelace Card" />
