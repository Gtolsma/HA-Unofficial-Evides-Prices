# Evides Tarieven voor Home Assistant

Onofficiële Home Assistant-integratie die de actuele drinkwatertarieven scrapet van de publieke Evides-pagina [www.evides.nl/service/tarieven](https://www.evides.nl/service/tarieven). Er is geen account, API-sleutel of officiële Evides-API voor nodig — die bestaat niet publiek, dus deze integratie leest de HTML-pagina rechtstreeks.

⚠️ **Dit is geen officiële Evides-integratie.** Evides kan de opmaak van hun website op elk moment wijzigen zonder aankondiging. Als dat gebeurt, kan het zijn dat deze integratie geen tarieven meer kan vinden — de sensoren worden dan `unavailable` in plaats van dat er foute waarden getoond worden, maar je zult de code dan wel moeten bijwerken.

## Wat het doet

Elke 24 uur (instelbaar) haalt de integratie de tarievenpagina op en leest de tabel met drinkwatertarieven uit. Dit zijn tarieven die maar één keer per jaar wijzigen, dus een dagelijkse controle is ruim voldoende om een tariefwijziging snel te detecteren zonder de Evides-site onnodig te belasten.

## Sensoren

Na het toevoegen verschijnt er één apparaat "Evides Tarieven" met drie sensoren:

| Sensor | Betekenis | Eenheid |
|---|---|---|
| `sensor.vastrecht` | Vastrecht per jaar (incl. 9% btw) | EUR |
| `sensor.variabel_tarief_per_m3` | Variabel tarief per m³ (incl. 9% btw) | EUR/m³ |
| `sensor.belasting_op_leidingwater_per_m3` | Belasting op leidingwater / BoL (incl. 9% btw) | EUR/m³ |

Elke sensor heeft daarnaast de attributen `jaar` (het tariefjaar zoals gevonden op de pagina), `jaar_bron`, `bron_url` en `laatst_gecontroleerd`.

Met deze drie waarden kun je zelf, bijvoorbeeld via een template sensor of de Energiedashboard-kostenconfiguratie, je waterkosten berekenen op basis van je werkelijke verbruik (`vastrecht / 365` per dag + `verbruik_m3 * (variabel_tarief + belasting)`).

## Installatie via HACS (custom repository)

Deze integratie staat niet in de standaard HACS-store, dus voeg hem toe als custom repository:

1. Deze integratie staat in [github.com/Gtolsma/HA-Unofficial-Evides-Prices](https://github.com/Gtolsma/HA-Unofficial-Evides-Prices), met `hacs.json` in de root en `custom_components/evides_tarieven/...` eronder.
2. In Home Assistant: **HACS → drie-puntjes-menu (rechtsboven) → Aangepaste repositories**.
3. Voeg de repository-URL toe, categorie **Integratie**.
4. Zoek in HACS naar "Evides Tarieven" en installeer.
5. Herstart Home Assistant.
6. Ga naar **Instellingen → Apparaten & Services → Integratie toevoegen**, zoek "Evides Tarieven" en volg de wizard (er hoeft niets ingevuld te worden — bevestigen is genoeg).

### Zonder HACS

Kopieer de map `custom_components/evides_tarieven` rechtstreeks naar `/config/custom_components/` op je Home Assistant-installatie, herstart, en voeg de integratie daarna op dezelfde manier toe via de UI.

## Instellingen

Via **Instellingen → Apparaten & Services → Evides Tarieven → Configureren** kun je het controle-interval aanpassen (standaard 24 uur, tussen 1 en 720 uur).

## Hoe de scraper werkt

De pagina heeft geen bruikbare CSS-classes of id's op de tarieventabel, dus de integratie matcht op de Nederlandse rij-labels in de tabel ("Vastrecht", "Variabel tarief", "Belasting op Leidingwater" / "BoL") in plaats van op vaste HTML-selectors. Zie `custom_components/evides_tarieven/coordinator.py` voor de exacte parsing-logica.

## Versiebeheer

De versie staat op twee plekken en die moeten synchroon lopen:

- `custom_components/evides_tarieven/manifest.json` → veld `"version"` (nu `1.0.0`).
- Een **GitHub release/tag** met exact dezelfde naam (`1.0.0`, zonder `v`-prefix).

HACS bepaalt namelijk welke versie geïnstalleerd is aan de hand van GitHub-releases, niet aan de hand van de manifest alleen. Dus bij elke wijziging:

1. Werk de code bij.
2. Verhoog `version` in `manifest.json` (patch voor bugfixes: `1.0.1`, minor voor nieuwe features: `1.1.0`, major voor breaking changes: `2.0.0`).
3. Voeg een sectie toe boven aan `CHANGELOG.md` met wat er veranderd is.
4. Commit, push, en maak op GitHub een nieuwe **release** met tag `X.Y.Z` (Releases → Draft a new release → tag = versienummer, geen `v`).
5. HACS ziet de nieuwe release vanzelf en biedt hem als update aan.

Dit project begint bij versie **1.0.0**, oftewel "versie 1".

## Licentie

MIT — vrij te gebruiken en aan te passen voor eigen gebruik.
