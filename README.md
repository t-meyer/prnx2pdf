# prnx2pdf

Converts DevExpress documents (`.prnx`) to PDF – **without** a DevExpress license or the program that created the report.

`.prnx` files are created when you click "Save" in a print preview based on DevExpress XtraReports, e.g. in **ZUB Argos** (thermal bridge reports). Without that program they usually can't be opened.

## Usage (Windows, no Python needed)

1. Download `prnx2pdf.exe` from [Releases](../../releases).
2. **Drag the `.prnx` file onto `prnx2pdf.exe`**.
3. The PDF is saved next to the `.prnx` file (same name, `.pdf` extension).

If you start the exe by double-clicking, a file selection dialog opens. Several files can be converted at once.

> **Note:** On first start Windows may show "Windows protected your PC" because the exe is not signed. Click **"More info" → "Run anyway"**.

## Usage with Python

```bash
pip install -r requirements.txt
python prnx2pdf.py report.prnx [more.prnx ...]
```

## Building the exe

```bash
pip install reportlab pyinstaller
pyinstaller --onefile --console --name prnx2pdf prnx2pdf.py
```

The exe is created in `dist/`.

## What is supported?

A `.prnx` file is gzip-compressed XML containing fully laid-out pages. The script redraws these elements:

- Text and labels (font, size, alignment, line wrapping)
- Tables with borders and background colors
- Lines
- Images and drawings
- Headers and footers, page numbers, table of contents

## Limitations

- Only tested with one report from ZUB Argos 8 Pro (DevExpress 17.2). Other reports may look different.
- Text widths are measured slightly differently than by DevExpress, so in tight cells numbers may overflow or wrap differently.
- RichText fields are not rendered.
- Windows only, because the fonts (Arial, Times New Roman) are loaded from the Windows fonts folder.

If you need an exact copy of the original, export it to PDF directly in the program that created it, or print it via "Microsoft Print to PDF".

## License

MIT – see [LICENSE](LICENSE).
