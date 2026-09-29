# Evides Tarieven voor Home Assistant

Onofficiële Home Assistant-integratie die de actuele drinkwatertarieven scrapet van de publieke Evides-pagina [www.evides.nl/service/tarieven](https://www.evides.nl/service/tarieven). Er is geen account, API-sleutel of officiële Evides-API voor nodig — die bestaat niet publiek, dus deze integratie leest de HTML-pagina rechtstreeks.

⚠️ **Dit is geen officiële Evides-integratie.** Evides kan de opmaak van hun website op elk moment wijzigen zonder aankondiging. Als dat gebeurt, kan het zijn dat deze integratie geen tarieven meer kan vinden — de betreffende sensoren worden dan `unavailable` in plaats van dat er foute waarden getoond worden, en je krijgt een melding onder **Instellingen → Reparaties**.

## Wat het doet

Elke 24 uur (instelbaar) haalt de integratie de tarievenpagina op en leest de tabel met drinkwatertarieven uit. Dit zijn tarieven die maar één keer per jaar wijzigen, dus een dagelijkse controle is ruim voldoende om een tariefwijziging snel te detecteren zonder de Evides-site onnodig te belasten.

De laatst gevonden tarieven worden lokaal bewaard. Is evides.nl even onbereikbaar (storing, onderhoud, geen internet), dan blijven de sensoren gewoon de laatst bekende tarieven tonen — ook na een herstart van Home Assistant. Zo krijgt je Energiedashboard geen gaten in de kostenberekening.

## Sensoren

Na het toevoegen verschijnt er één apparaat "Evides Tarieven" met deze sensoren:

| Sensor (entity-ID bij nieuwe installatie) | Betekenis | Eenheid |
|---|---|---|
| `sensor.evides_tarieven_fixed_annual_charge` | Vastrecht per jaar (incl. 9% btw) | € |
| `sensor.evides_tarieven_variable_rate_per_m3` | Variabel tarief per m³ (incl. 9% btw) | €/m³ |
| `sensor.evides_tarieven_water_tax_per_m3` | Belasting op leidingwater / BoL per m³ (incl. 9% btw) | €/m³ |
| `sensor.evides_tarieven_total_rate_per_m3` | **Totaal tarief per m³** = variabel tarief + BoL | €/m³ |
| `sensor.evides_tarieven_fixed_charge_per_day` | Vastrecht per dag (vastrecht / 365, of 366 in een schrikkeljaar) | € |
| `sensor.evides_tarieven_last_checked` | Tijdstip van de laatste geslaagde controle (diagnostisch) | tijdstempel |

De weergavenamen volgen de taal van je Home Assistant (in het Nederlands dus "Vastrecht", "Totaal tarief per m³", enz.). De entity-ID's worden door Home Assistant altijd uit de Engelse naam afgeleid. Had je de integratie al eerder geïnstalleerd, dan houden bestaande sensoren hun huidige entity-ID; je kunt ze zien of hernoemen via **Instellingen → Entiteiten**.

De tariefsensoren hebben daarnaast de attributen `jaar` (het tariefjaar zoals gevonden op de pagina), `jaar_bron`, `bron_url` en `laatst_gecontroleerd`.

> BoL wordt door Evides alleen geheven tot 50.000 m³ per jaar; voor een huishouden maakt dat niet uit.

## Gebruik in het Energiedashboard

Heb je een watermeter in het Energiedashboard (bijv. via een P1-/watermeter-lezer), dan kun je de kosten automatisch laten berekenen:

1. **Instellingen → Dashboards → Energie → Waterverbruik** → je watermeter bewerken.
2. Kies **"Gebruik een entiteit met de huidige prijs"** en selecteer `sensor.evides_tarieven_total_rate_per_m3`.

Het vastrecht zit daar niet in (dat is onafhankelijk van je verbruik). Wil je totale kosten per dag, gebruik dan bijvoorbeeld een template-sensor:

```yaml
template:
  - sensor:
      - name: "Waterkosten vandaag"
        unit_of_measurement: "€"
        device_class: monetary
        state: >
          {{ (states('sensor.evides_tarieven_fixed_charge_per_day') | float(0)
              + states('sensor.waterverbruik_vandaag') | float(0)
                * states('sensor.evides_tarieven_total_rate_per_m3') | float(0)) | round(2) }}
```

(`sensor.waterverbruik_vandaag` is een voorbeeld; gebruik je eigen dagverbruik in m³, bijv. via een Utility Meter.)

## Melding bij een tariefwijziging

Als een tarief verandert ten opzichte van de vorige controle, vuurt de integratie het event `evides_tarieven_tarief_gewijzigd` af. De data bevat `gewijzigd` (lijst van gewijzigde tarieven), `oud`, `nieuw` en `jaar`. Voorbeeld-automatisering:

```yaml
automation:
  - alias: "Evides-tarief gewijzigd"
    triggers:
      - trigger: event
        event_type: evides_tarieven_tarief_gewijzigd
    actions:
      - action: notify.notify
        data:
          title: "Nieuwe Evides-tarieven ({{ trigger.event.data.jaar }})"
          message: >
            {% for key in trigger.event.data.gewijzigd %}
            {{ key }}: € {{ trigger.event.data.oud[key] }} → € {{ trigger.event.data.nieuw[key] }}
            {% endfor %}
```

## Als het misgaat

- **Reparatiemelding "Evides-tarievenpagina is gewijzigd"**: de integratie vindt één of meer tarieven niet meer op de pagina. De melding noemt welke. Deze verdwijnt vanzelf zodra alles weer gevonden wordt (bijv. na een update van de integratie).
- **Diagnostiek**: via **Instellingen → Apparaten & Services → Evides Tarieven → ⋮ → Diagnostiek downloaden** krijg je een bestand met de laatst opgehaalde data en eventuele foutmelding. Voeg dat toe als je een issue aanmaakt.
- In deze repository draait daarnaast wekelijks een GitHub Action die de echte Evides-pagina test, zodat een wijziging van de pagina snel opvalt.

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

Vereist Home Assistant 2024.11 of nieuwer (het brand-icoon wordt vanaf 2026.3 getoond).

## Hoe de scraper werkt

De pagina heeft geen bruikbare CSS-classes of id's op de tarieventabel, dus de integratie matcht op de Nederlandse rij-labels in de tabel ("Vastrecht", "Variabel tarief", "Belasting op Leidingwater" / "BoL") in plaats van op vaste HTML-selectors. Zie `custom_components/evides_tarieven/coordinator.py` voor de exacte parsing-logica.

## Ontwikkelen en testen

```bash
pip install -r requirements_test.txt
pytest
```

De tests draaien tegen een ingekorte kopie van de echte pagina (`tests/fixtures/tarieven_2026.html`). Verandert de Evides-pagina, werk dan ook deze fixture bij. Bij elke push draaien op GitHub ook `hassfest` (validatie van Home Assistant) en de HACS-validatie.

## Logo / brand-icoon

De integratie heeft een eigen icoon (een blauwe waterdruppel — een eigen ontwerp, geen kopie van het officiële Evides-logo) op `custom_components/evides_tarieven/brand/icon.png`, met `dark_icon.png` als variant voor dark mode. Vanaf Home Assistant 2026.3 wordt dit automatisch herkend en getoond bij het apparaat in **Instellingen → Apparaten & Services** en in de HACS-downloadlijst, zonder dat daar een aparte pull request naar `home-assistant/brands` voor nodig is.

## Versiebeheer

De versie staat op twee plekken en die moeten synchroon lopen:

- `custom_components/evides_tarieven/manifest.json` → veld `"version"` (nu `1.2.0`).
- Een **GitHub release/tag** met exact dezelfde naam (`1.1.0`, zonder `v`-prefix).

HACS bepaalt namelijk welke versie geïnstalleerd is aan de hand van GitHub-releases, niet aan de hand van de manifest alleen. Dus bij elke wijziging:

1. Werk de code bij.
2. Verhoog `version` in `manifest.json` (patch voor bugfixes: `1.0.1`, minor voor nieuwe features: `1.1.0`, major voor breaking changes: `2.0.0`).
3. Voeg een sectie toe boven aan `CHANGELOG.md` met wat er veranderd is.
4. Commit, push, en maak op GitHub een nieuwe **release** met tag `X.Y.Z` (Releases → Draft a new release → tag = versienummer, geen `v`).
5. HACS ziet de nieuwe release vanzelf en biedt hem als update aan.

Huidige versie: **1.2.0** (gestart bij 1.0.0, "versie 1"). Zie `CHANGELOG.md` voor het overzicht per versie.

## Licentie

MIT — vrij te gebruiken en aan te passen voor eigen gebruik. Zie [`LICENSE`](LICENSE).
