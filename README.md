# Harness Studio · lokal demo

## Start på Windows

1. Pak ZIP-filen ud i en almindelig mappe, hvor du må gemme filer.
2. Python 3.10 eller nyere skal være installeret.
3. Dobbeltklik på `START_WINDOWS.bat`.
4. Browseren åbner programmet. Lad terminalvinduet være åbent, mens du arbejder.

Alternativt, fra terminalen i denne mappe:

```sh
python server.py
```

Åbn http://127.0.0.1:8765 hvis browseren ikke åbner selv. Ved optaget port: `python server.py --port 8766`.
Der skal ikke installeres Python-pakker eller en separat databaseserver. Programmet kræver ingen internetforbindelse.

## Arbejdsgang

- Vælg det medfølgende **Demo Harness**, eller vælg **Nyt** for et tomt net.
- Klik på en M-strækning og ret endepunkter eller føringsfarve i højre side. Længden beregnes fra tegningen.
- Fjern markeringen i **Vis M-linjer** for at skjule alle M-strækninger og M-numre. Valget huskes på computeren.
- Fjern kun markeringen i **Vis M-numre** for at beholde de farvede linjer, men skjule teksten M1, M2 osv.
- Brug musehjulet til at scrolle, `Shift + musehjul` til vandret scroll og `Ctrl + musehjul` til at zoome omkring markøren. Du kan også panorere ved at trække i et tomt område af diagrammet.
- Brug **Vend 180°** for at se og redigere diagrammet fra den modsatte ende. Retningen huskes på computeren og ændrer ikke de gemte mål eller hulplaceringer.
- Knappen **Slet** ved valg af ledningsnet sletter det valgte net efter en tydelig bekræftelse.
- Under **X-punkter** kan hvert X-nummer få et navn eller en beskrivelse og en farve.
- Under **Net & versioner** kan enkelte historiske versioner åbnes som kopi eller slettes.
- Klik på et punkt og skriv hulplaceringen direkte, f.eks. `C29 · 2`, indtast koordinater eller træk punktet på bordet. **Lås til huller** gælder træk og nye punkter. **Til nærmeste hul** flytter det valgte punkt til nærmeste hul. Koordinatfelter tillader placering mellem huller.
- Et X-punkt kan fylde flere huller. Angiv bredde og højde i huller ved punktet; hulplaceringen er feltets øverste venstre hul.
- Ved et X-punkt over flere huller kan **Linje fra kolonne/række** flytte linjens tilslutning til et bestemt hul i X-punktet. Den lille farvede prik viser det valgte tilslutningshul.
- Aktivér **Forbind to punkter**, og træk fra et X- eller P-punkt til et andet punkt. Slipper du på et tomt hul, oprettes et nyt P-punkt og en M-forbindelse automatisk. Det gør det også muligt at forbinde P-punkter ved siden af hinanden.
- Et almindeligt P-punkt kan trækkes direkte fra værktøjsrailen og slippes på diagrammet. Aktivér **Forbind**, og klik derefter på første og andet punkt for at oprette en M-linje uden at trække.
- Diagramværktøjerne sidder i en fast værktøjsrail direkte ved siden af diagrammets scrollområde. Ændringer i det valgte punkts og den valgte M-linjes felter anvendes automatisk, når du forlader feltet eller vælger en ny værdi; der skal ikke trykkes **Anvend**.
- Flyttes et punkt ind på en eksisterende M-linje, deles linjen automatisk ved punktet. Den samlede tegnede længde følger geometrien.
- Tilføj X-punkter til ledningernes ender og P-punkter til fysisk føring. Punkter er ikke elektriske samlinger.
- En M-strækning er lige, medmindre du angiver knæk som `x,y`, ét pr. linje og med decimalpunkt.
- Under **Ledninger** kan du ændre farve, kvadrat, endepunkter, tillæg og ordnet M-rute. **Foreslå rute** finder en sammenhængende vej for den enkelte ledning. Kontrollér den fysisk.
- Under **Ruller** vælger du, hvor mange ens ledningsnet der skal produceres. Beregneren lægger 15 cm til hvert fysisk ledningsstykke, grupperer efter ledningsfarve og mm² og pakker kun hele stykker på hver rulle. En rest bruges kun, hvis hele det næste stykke kan være der. Standardruller er 100 m for 0,75, 1,5 og 2,5 mm² samt 25 m for 16 mm²; længderne kan rettes i visningen.
- Manglende eller brudte ledningsruter findes automatisk, når nettet åbnes eller forbindelser ændres. **Nulstil og beregn alle ruter** sletter først samtlige gamle rutevalg, registrerer punkter på eksisterende M-linjer og beregner derefter alle ruter helt fra bunden via den korteste tegnede vej. Handlingen kan fortrydes.
- **X-kort** afspejler rettelser med det samme. Print alle eller vælg ét X-punkt. Browserens udskrivning kan gemme PDF. Slå browserens egne sidehoveder/fødder fra for rene kort.
- Tryk **Gem ændringer** før du lukker. Ugemte ændringer mistes ved nedbrud. Hver gemning opretter en historisk version.
- Under **Net & versioner** kan du ændre navn og noter, markere nettet gennemgået ved bordet eller åbne en gammel version som et nyt net.
- **Fortryd** gælder ændringer siden seneste gemning. Historikken gælder gemte versioner.
- Det valgte punkt eller den valgte M-strækning kan slettes med **Delete** på tastaturet. Når en strækning slettes, fjernes den automatisk fra de ledningsruter, der bruger den; de berørte ruter skal derefter kontrolleres eller tegnes igen.

## Hvad der er med

Den medfølgende seed-fil indeholder kun få, syntetiske demonstrationspunkter og ledninger. Den repræsenterer ikke et rigtigt produkt eller produktionsnet.

Bordet vises i kompakte diagramkoordinater, men alle tegnede længder beregnes med **3,5 cm fra hulmidte til hulmidte**. Der er 46 kolonner og 91 rækker fordelt A1–A30, B1–B31 og C1–C30.

Demoens kolonner vises med **46 til venstre og 1 til højre**. En indtastet huladresse bruger samme retning.

Farvede ringe angiver destinations-X-punktets farve, ikke lederens isolationsfarve. Farven kan ændres ved at vælge X-punktet på bordet. En rute med forkerte forbindelser får ingen beregnet længde.

## Tegnede længder

- Skitsen importeres som **Kladde**. Knapplaceringer og foreslåede ruter er ikke bekræftet ved bordet.
- Tidligere indtastede og fælles mål er fjernet. Diagrammets geometri er den eneste længdekilde.
- Flytning af punkter ændrer geometrien, men aldrig indtastede mål.
- Der er **ikke** lagt 20 cm tillæg til. Et eksplicit tillægsfelt på hver ledning lægges én gang til hele dens beregnede længde. Tillæg for hele produktionen er ikke implementeret.
- Ændring af en M-forbindelse kan gøre eksisterende ruter ugyldige. De skal rettes i ledningslisten. En kladde må gemmes med manglende mål/ruter, men kan ikke markeres gennemgået, før længderne kan beregnes.
- Ingen automatisk elektrisk kontrol, strømberegning eller påstand om at et gennemgået net er certificeret.

## Gemning og backup

Databasen oprettes automatisk som `data/harness.sqlite`. Den indeholder nettet, punkter, strækninger, ledninger, ruter og versionshistorik. Bevar den fil, når du opdaterer programmet.

**Eksportér JSON** gemmer det åbne net inklusive aktuelle rettelser. **Importér som nyt net** opretter en ny kladde. JSON indeholder ikke hele versionshistorikken. For fuld backup: luk programmet og kopiér `data/harness.sqlite` til et andet sted.

To åbne faner kan ikke stiltiende overskrive hinandens gemninger: serveren afviser en forældet version. Eksportér JSON før genindlæsning, hvis du får den besked.

## Teknisk grundlag

Denne første udgave er lokal og bruger Python-standardbibliotekets HTTP-server og SQLite, med en SVG/JavaScript-editor i browseren. Den er ikke en PostgreSQL/FastAPI/React-implementering. Målet er at afprøve den konkrete arbejdsgang før flere dependencies og serverdrift introduceres.

- `server.py`: API, validering, længdeberegning, SQL-transaktioner og versionskontrol.
- `static/`: brugerfladen.
- `seed.json`: den importerede skitse. Bruges kun ved oprettelse af en tom database.
- `test_app.py`: regressionstest af gemning, mål og dataintegritet.

SQL-tabeller: `harness`, `point`, `segment`, `wire`, `route_step` og `revision`. Fremmednøgler er aktiveret. Gemning af et net og dets historik sker atomisk. Længder og koordinater er i cm i denne første udgave.

Programmet lytter kun på denne computer (127.0.0.1). Det er ikke en internetserver eller en flerbrugerløsning med login. PostgreSQL, FastAPI, adgangskontrol og fælles drift kan tilføjes senere; det er ikke nødvendigt for at prøve denne udgave ved bordet.

Kør test:

```sh
python -m unittest discover -v
```
