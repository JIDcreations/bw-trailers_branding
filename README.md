# BW huisstijlpagina

Statische pagina (HTML, CSS, vanilla JS) voor `bwtrailers.be/branding/`.

## Structuur

- `branding/`: **de site**, het enige wat Netlify publiceert (zie `netlify.toml`)
  - `index.html`: gegenereerd, niet met de hand aanpassen
  - `assets/`: css, js, fonts (woff2), img (AVIF + WebP), logos (SVG/PNG/JPG)
  - `bw-trailers-huisstijl.zip`: het downloadpakket (logo's, fonts + licentie, LEESMIJ)
- `src/copy/nl.json`: **alle tekst** (ook URL's, alt-teksten, LEESMIJ van het pakket)
- `src/template.html`: opbouw van de pagina
- `src/package-fonts/`: TTF's en licenties voor het ZIP-pakket
- `tools/`: buildscripts
- `nieuwe huisstijl 2026/`: brondocumenten, **niet in git** (te zwaar, zie `.gitignore`)

## Opnieuw bouwen

```sh
python3 tools/build.py          # index.html + zip (alleen standaardbibliotheek)
```

Nieuwe taal: kopieer `src/copy/nl.json` naar `fr.json`, vertaal, en draai
`python3 tools/build.py fr`. Dat schrijft `branding/fr/index.html` met dezelfde assets.

Logo's en beelden opnieuw exporteren uit `bw huisstijl.ai` (vraagt de lokale map
`nieuwe huisstijl 2026/` en `pymupdf`, `fonttools`, `pillow`):

```sh
python3 tools/extract_logos.py
python3 tools/build_images.py
```

## Fonts

- Michroma: SIL OFL 1.1, self-hosted
- Lato: SIL OFL 1.1 met Reserved Font Name. Daarom de ongewijzigde woff2-subsets van Google Fonts, niet zelf gesubset
- Peridot PE (Adobe Fonts) is alleen voor drukwerk en mag niet self-hosted worden
