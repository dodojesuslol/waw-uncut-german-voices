# WaW Uncut mit deutscher Sprachausgabe

Zwei kleine Python-Skripte für **Call of Duty: World at War** (Steam, deutsche Version).
Sie machen aus einem bereits eingespielten Uncut-Patch eine Version mit

- **deutschen Voice Lines** auch in den Intro- und Ingame-Dialogen, die der Patch englisch macht, und
- **Abtrennungen / Feuer-Todesanimationen**, die die Skripte bei deutscher Spielsprache sonst abschalten.

Dieses Repo enthält **keine Spieldateien**. Alles wird aus deiner eigenen Installation erzeugt.
Getestet unter Linux mit Proton (Steam-Build 252004). Nur Python-Standardbibliothek nötig.

## Hintergrund

- **Fastfiles (`zone/German/*.ff`)** bestehen aus einem 12-Byte-Header (`IWffu100` + Version) und einem
  zlib-Stream. Sie sind nicht signiert.
- **Gestreamte Dialoge** liegen in `main/localized_german_iw02.iwd` und `iw03.iwd`. Der Patch
  ändert sie nicht, sie bleiben deutsch.
- **Eingebettete Dialoge:** Die Uncut-Fastfiles sind byte-identisch mit den englischen. Deshalb sind die
  *eingebetteten* Dialoge englisch. Betroffen sind 6 Level:
  - `mak` (Semper Fi)
  - `pel1b` (Burn 'em Out)
  - `see1` (Ring of Steel)
  - `sniper` (Vendetta)
  - `ber2` und `ber3` (je eine Lautsprecher-Durchsage)
- **Lange Zeilen** sind nur angespielt eingebettet. Die ersten 0x20C00 Bytes liegen in der `.ff`, der
  Rest wird aus der `.iwd` gestreamt. Das Längenfeld steht direkt vor den Daten oder vor dem eingebetteten
  Dateinamen.
- **`gervo.py`** ersetzt die englischen Daten samt Längenfeld durch die deutschen aus der originalen
  (geschnittenen) `.ff` und korrigiert die Zonengröße im Header. Die deutschen Daten sind überall kleiner,
  die reservierten Speicherblöcke reichen deshalb aus. Alles außer den getauschten Sounds bleibt
  byte-gleich, das Skript prüft das nach dem Schreiben.
- **Abtrennungen:** `do_gib()` in `common.ff` bricht ab, wenn `is_german_build()` wahr ist, also bei
  `GetDvar("language") == "german"`. **`ungerman.py`** ändert diesen einen String auf `"nogerm"`
  (6 Bytes, gleiche Länge). Die Zombie-Freischaltung (`allow_zombies_german`) und der Multiplayer
  bleiben unberührt.

## Anleitung

Voraussetzungen:

- Die deutsche Steam-Version ist installiert.
- Die **Originaldateien** aus `zone/German/` sind gesichert, bevor der Uncut-Patch eingespielt wird.
  Sie liefern die deutschen Stimmen.
- Der Uncut-Patch (deutsche Variante) ist eingespielt.
- Das Spiel ist beendet.

```bash
GAME="$HOME/.local/share/Steam/steamapps/common/Call of Duty World at War/zone/German"
ORIG="$HOME/WaW_Backup_Original/zone/German"   # originale deutsche .ff
SAVE="$HOME/WaW_Backup_Uncut/zone/German"       # Sicherung des Uncut-Stands
mkdir -p "$SAVE" out

# 1. Uncut-Stand sichern
for f in ber2 ber3 mak pel1b see1 sniper common; do cp -a "$GAME/$f.ff" "$SAVE/"; done

# 2. Deutsche Voice Lines einbauen
for f in ber2 ber3 mak pel1b see1 sniper; do
    python3 gervo.py "$SAVE/$f.ff" "$ORIG/$f.ff" "out/$f.ff" "names/$f.names"
done

# 3. Abtrennungen freischalten
python3 ungerman.py "$SAVE/common.ff" out/common.ff

# 4. Installieren
cp out/*.ff "$GAME/"
```

Trage dann in Steam unter Eigenschaften → Startoptionen ein:

```
+set cg_allow_mature 1 +set cg_mature 1
```

**Testen:**

- Das Intro von *Semper Fi* und der Anfang von *Vendetta* sollten deutsch sein.
- Granaten oder Schrotflinte auf Gegner sollten Abtrennungen zeigen.

## Rückgängig machen

- **Zurück zum Uncut-Stand:** `cp -a "$SAVE"/*.ff "$GAME/"`
- **Zurück zum geschnittenen Original:** in Steam „Dateien auf Fehler überprüfen“.

## Hinweise

- Starte in Steam nicht **„Dateien auf Fehler überprüfen“** und ändere die Spielsprache nicht. Beides
  setzt alles zurück.
- Der Uncut-Patch ersetzt auch Multiplayer-Karten. Auf PunkBuster-Servern kann das Probleme machen.
  Diese Skripte ändern am Multiplayer nichts.
- Nutzung auf eigene Gefahr, nur mit der eigenen, legal erworbenen Kopie.
