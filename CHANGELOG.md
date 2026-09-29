# Changelog

Alle noemenswaardige wijzigingen aan deze integratie worden hier bijgehouden. De versienummers volgen [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) en komen overeen met de `version` in `custom_components/evides_tarieven/manifest.json` en met de GitHub-release/tag.

## [1.2.0] - 2026-09-29

### Toegevoegd
- Sensor **Totaal tarief per m³** (variabel tarief + BoL), direct bruikbaar als prijs-entiteit voor water in het Energiedashboard.
- Sensor **Vastrecht per dag** (houdt rekening met schrikkeljaren).
- Diagnostische sensor **Laatst gecontroleerd** (tijdstempel van de laatste geslaagde controle).
- Event `evides_tarieven_tarief_gewijzigd` zodra een tarief verandert, voor notificaties/automatiseringen.
- Reparatiemelding (Instellingen → Reparaties) als de Evides-pagina gewijzigd is en tarieven niet meer gevonden worden; verdwijnt vanzelf zodra alles weer gevonden wordt.
- Diagnostiek downloaden via het integratiemenu.
- Tests (pytest) en GitHub Actions voor hassfest, HACS-validatie, tests en een wekelijkse controle van de live Evides-pagina.

### Gewijzigd
- Laatst bekende tarieven worden lokaal bewaard: bij een tijdelijke storing van evides.nl (ook direct na een herstart) blijven de sensoren de laatste waarden tonen in plaats van `unavailable` te worden. Alleen bij een gewijzigde paginastructuur worden sensoren `unavailable`.
- Een tarief dat ontbreekt op de pagina geeft nu `unavailable` in plaats van `unknown`.
- Weergaveprecisie ingesteld (2 decimalen voor euro's, 3 voor €/m³).
- Attribuut `laatst_gecontroleerd` wordt niet meer in de recorder-database opgeslagen (scheelt een databaserij per controle).
- Opties-scherm gebruikt een numeriek invoerveld met eenheid en uitleg.
- Modernisering voor recente Home Assistant-versies: `entry.runtime_data`, `DeviceEntryType.SERVICE`, `aiohttp.ClientTimeout`, `config_entry` in de coordinator, nieuwe OptionsFlow-stijl en `single_config_entry` in de manifest. Minimale HA-versie is nu 2024.11.

### Opgelost
- `LICENSE`-bestand (MIT) toegevoegd; de README noemde MIT al, maar HACS vereist het bestand.
- `codeowners` in de manifest verwijst nu naar het juiste GitHub-account (`@Gtolsma`).
- README noemde entity-ID's (`sensor.vastrecht`, …) die Home Assistant in werkelijkheid niet aanmaakt; de tabel toont nu de echte ID's.

## [1.1.0] - 2026-09-22

### Toegevoegd
- Brand-icoon (logo) voor de integratie, zodat deze zichtbaar is met een eigen icoon in Instellingen → Apparaten & Services en in HACS: `custom_components/evides_tarieven/brand/icon.png` + `dark_icon.png` voor dark mode. Gebruikt het inline brand-mechanisme van Home Assistant 2026.3+ (geen aparte PR naar `home-assistant/brands` nodig).

## [1.0.0] - 2026-09-21

Eerste versie.

### Toegevoegd
- Scraper voor de drinkwatertarieven op `evides.nl/service/tarieven` (vastrecht, variabel tarief per m³, belasting op leidingwater/BoL per m³).
- UI config flow — installatie zonder YAML.
- Opties-flow om het controle-interval aan te passen (standaard 24 uur).
- Sensoren met attributen `jaar`, `jaar_bron`, `bron_url` en `laatst_gecontroleerd`.
- HACS-structuur (`hacs.json`) zodat de repo als aangepaste repository toegevoegd kan worden.
