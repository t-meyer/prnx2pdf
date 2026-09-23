# prnx2pdf

Wandelt DevExpress-Dokumente (`.prnx`) in PDF um – **ohne** DevExpress-Lizenz oder das Programm, mit dem der Bericht erstellt wurde.

`.prnx`-Dateien entstehen, wenn man in einer Druckvorschau auf Basis von DevExpress XtraReports auf „Speichern“ klickt, z. B. in **ZUB Argos** (Wärmebrücken-Berichte). Ohne das Programm lassen sie sich normalerweise nicht öffnen.

## Benutzung (Windows, ohne Python)

1. `prnx2pdf.exe` unter [Releases](../../releases) herunterladen.
2. Die `.prnx`-Datei mit der Maus **auf die `prnx2pdf.exe` ziehen**.
3. Die PDF liegt danach im selben Ordner wie die `.prnx`-Datei (gleicher Name, Endung `.pdf`).

Wer die exe per Doppelklick startet, bekommt ein Fenster zur Dateiauswahl. Es können auch mehrere Dateien auf einmal umgewandelt werden.

> **Hinweis:** Beim ersten Start zeigt Windows möglicherweise „Der Computer wurde durch Windows geschützt“, weil die exe nicht signiert ist. Dann auf **„Weitere Informationen“ → „Trotzdem ausführen“** klicken.

## Benutzung mit Python

```bash
pip install -r requirements.txt
python prnx2pdf.py Bericht.prnx [weitere.prnx ...]
```

## exe selbst bauen

```bash
pip install reportlab pyinstaller
pyinstaller --onefile --console --name prnx2pdf prnx2pdf.py
```

Die exe liegt danach in `dist/`.

## Was wird unterstützt?

Eine `.prnx` ist eine gzip-komprimierte XML-Datei mit fertig gesetzten Seiten. Das Skript zeichnet diese Elemente nach:

- Texte und Beschriftungen (Schrift, Größe, Ausrichtung, Zeilenumbruch)
- Tabellen mit Rahmen und Hintergrundfarben
- Linien
- Bilder und Zeichnungen
- Kopf- und Fußzeilen, Seitenzahlen, Inhaltsverzeichnis

## Einschränkungen

- Getestet nur mit einem Bericht aus ZUB Argos 8 Pro (DevExpress 17.2). Andere Berichte können anders aussehen.
- Die Textbreiten werden etwas anders berechnet als von DevExpress. An engen Stellen können Zahlen daher leicht überstehen oder anders umbrechen.
- RichText-Felder werden nicht dargestellt.
- Läuft nur unter Windows, weil die Schriften (Arial, Times New Roman) aus `C:\Windows\Fonts` geladen werden.

Wer ein Originaldokument vollständig und exakt braucht, sollte es direkt im erzeugenden Programm als PDF exportieren oder über „Microsoft Print to PDF“ drucken.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
