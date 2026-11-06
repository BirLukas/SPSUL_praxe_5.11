# Extrakce strukturovaných dat z bug reportů

## Popis úlohy
Nástroj slouží k automatickému zpracování a strukturování hlášení chyb (bug reportů) od uživatelů a testerů do formátu JSON. Z nestrukturovaného textu v češtině extrahuje zasaženou komponentu systému, odhadnutou závažnost problému, informaci o reprodukovatelnosti a případnou konkrétní chybovou hlášku nebo chybový kód. Usnadňuje tím třídění (triage) hlášenek a jejich automatické směrování do správného týmu.

## Schéma výstupu (JSON)

Každý výstup modelu musí být validní JSON objekt s následující strukturou:

```json
{
  "komponenta": "frontend | backend | databaze | auth | platby | jine",
  "zavaznost": "nizka | stredni | vysoka | kriticka",
  "reprodukovatelny": true,
  "chybova_hlaska": "string nebo null"
}
```

### Popis jednotlivých polí:
- `komponenta` (string, povinné): Jedna z hodnot:
  - `frontend`: Problémy s UI, tlačítky, rozložením, zobrazením v prohlížeči, CSS, formuláři na webu.
  - `backend`: Chyby API, serverové timeouty, padání backend služeb, výpočetní chyby.
  - `databaze`: Chyby dotazů, zámky, neukládání dat, migrace, spojení s DB.
  - `auth`: Přihlašování, registrace, obnova hesla, oprávnění, tokeny, 2FA.
  - `platby`: Platební brána, zpracování plateb, fakturace, košík při placení.
  - `jine`: Ostatní nebo obecné chyby, které nelze jednoznačně zařadit.
- `zavaznost` (string, povinné): Jedna z hodnot:
  - `nizka`: Kosmetické vady, překlepy, drobné vizuální glitche bez vlivu na funkčnost.
  - `stredni`: Funkce nepracuje optimálně, ale existuje náhradní řešení (workaround), aplikace nepadá.
  - `vysoka`: Klíčová funkce nefunguje více uživatelům, blokuje běžnou práci.
  - `kriticka`: Celý systém nebo klíčová služba je nedostupná (výpadek, ztráta dat, bezpečnostní incident).
- `reprodukovatelny` (boolean nebo null):
  - `true`: Pokud text uvádí, že se chyba děje opakovaně, vždy, nebo uvádí kroky k reprodukci.
  - `false`: Pokud text uvádí, že se chyba stala jen jednou a znovu se nepodařilo nasimulovat.
  - `null`: Pokud v textu není o reprodukovatelnosti žádná zmínka.
- `chybova_hlaska` (string nebo null):
  - `string`: Přesné nebo zkrácené znění chybové zprávy, stack trace nebo HTTP status kódu (např. `"500 Internal Server Error"`, `"TypeError: undefined is not a function"`, `"ERR_CONNECTION_REFUSED"`).
  - `null`: Pokud v textu žádná konkrétní chybová hláška ani kód uvedeny nejsou.

---

## Pravidla porovnávání (Evaluation Rules)

Odpověď modelu je porovnávána s referenční hodnotou (*gold standard*) pole po poli:

1. **`komponenta`**:
   - Porovnání řetězců case-insensitive, s oříznutím bílých znaků (`strip().lower()`).
   - Musí přesně odpovídat jedné z definovaných kategorií.
2. **`zavaznost`**:
   - Porovnání řetězců case-insensitive, s oříznutím bílých znaků (`strip().lower()`).
   - Musí přesně odpovídat jedné z definovaných kategorií.
3. **`reprodukovatelny`**:
   - Striktní typová i hodnotová shoda (`true` / `false` / `null`).
   - V případě, že model vrátí string `"true"` / `"false"`, parser provede normalizaci na boolean.
4. **`chybova_hlaska`**:
   - Pokud je referenční hodnota `null`, model musí vrátit `null` (nebo prázdný řetězec, který je normalizován na `null`).
   - Pokud je referenční hodnota string: porovnává se case-insensitive; shoda je uznána, pokud extrahovaný text odpovídá nebo obsahuje klíčovou část chybového kódu/hlášky.

---

## Testovací sada (Fáze 2)

Sada obsahuje celkem 25 testovacích případů ve formátu JSONL, rozdělených podle zadání na:
- `data/dev.jsonl`: 15 případů (ID 1–15) určených pro ladění promptu.
- `data/test.jsonl`: 10 případů (ID 16–25) určených pro finální evaluační měření (nedotčeno při vývoji).

### Záludné případy (`tezky: true`)
Sada obsahuje 10 záludných případů (5 v dev, 5 v test) pokrývajících:
- **Chybějící údaje (`null`)**: Případy bez explicitní chybové hlášky nebo bez zmínky o reprodukovatelnosti (např. ID 6, 13, 22).
- **Dva systémy v jednom textu / zavádějící kontext**: Uživatel kliká v UI nebo provádí přihlašování, ale skutečným kořenovým problémem je pád databáze nebo transakce (např. ID 9, 21).
- **Překlepy, hovorový styl a slang**: Rychle sepsané hlášení s chybějící diakritikou a slangem (např. ID 8).
- **Ironie a sarkasmus**: Stížnost se sarkastickým tónem (např. ID 7, 19).
- **Nezařaditelná komponenta (`jine`)**: Hlášení problémů mimo standardní softwarové vrstvy, např. tiskárna v kanceláři nebo přehřátí racku v serverovně (např. ID 10, 24).
- **Chybový kód v textu**: Extrakce stavových kódů a hlášení (např. ID 20).

---

## Návod ke spuštění (Fáze 0)

Skript je napsán v čistém Pythonu bez nutnosti instalovat externí knihovny (využívá standardní knihovnu).

### Konfigurace prostředí
1. V této složce vytvoř soubor `.env` (pokud ještě nemáš) ze vzoru `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Doplň do `.env` své API klíče (např. `GROQ_API_KEY`).

### Spuštění evaluace
```bash
python src/eval.py --provider groq --model openai/gpt-oss-120b --dataset dev --prompt v1
```

---

## Výsledky experimentů (Fáze 4)
*(Bude doplněno v rámci Fáze 4)*

---

## Rozbor chyb a reflexe (Fáze 5)
*(Bude doplněno v rámci Fáze 5)*
