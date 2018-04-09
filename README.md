# home-assistant-pollenkoll

Support for getting current pollen levels from Pollenkollen.se
Visit https://pollenkoll.se/pollenprognos/ to find available cities
Visit https://pollenkoll.se/pollenprognos-ostersund/ to find available states
Example configuration

```
sensor:
  - platform: pollenkoll
    sensors:
      - city: Stockholm
        state: Gräs
      - city: Östersund
        state: Hassel
```
