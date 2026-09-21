# Changelog

Alle noemenswaardige wijzigingen aan deze integratie worden hier bijgehouden. De versienummers volgen [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) en komen overeen met de `version` in `custom_components/evides_tarieven/manifest.json` en met de GitHub-release/tag.

## [1.0.0] - 2026-09-21

Eerste versie.

### Toegevoegd
- Scraper voor de drinkwatertarieven op `evides.nl/service/tarieven` (vastrecht, variabel tarief per m³, belasting op leidingwater/BoL per m³).
- UI config flow — installatie zonder YAML.
- Opties-flow om het controle-interval aan te passen (standaard 24 uur).
- Sensoren met attributen `jaar`, `jaar_bron`, `bron_url` en `laatst_gecontroleerd`.
- HACS-structuur (`hacs.json`) zodat de repo als aangepaste repository toegevoegd kan worden.
