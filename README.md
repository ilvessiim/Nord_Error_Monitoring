# Nord Error Monitoring

A repository for error monitoring and telemetry analysis tools.

---

## English Guide

This tool analyzes telemetry data from raw CSV files, aggregates error episodes, categorizes issues, and generates summarized statistics and charts.

### How to Run on Another Computer

When you download this repository as a ZIP file (or clone it with Git), all the necessary scripts are packed together:
1. `analyze_telemetry.py` - The main Python script that does the heavy lifting.
2. `run_analysis.command` - Double-clickable launcher for **macOS**.
3. `run_analysis.bat` - Double-clickable launcher for **Windows**.

#### 1. Requirements
* You must have **Python 3** installed on your system. If not, download and install it from [python.org](https://www.python.org/).
* The script automatically installs any missing dependencies (`pandas`, `numpy`, `matplotlib`) on startup using `pip`.

#### 2. Running on macOS
If you downloaded this repository as a ZIP from GitHub, macOS will add a **quarantine flag** to the files because they were downloaded from a web browser. If you try to double-click `run_analysis.command`, macOS will block it stating it is from an unidentified developer.

To bypass this quarantine restriction:
1. Open the **Terminal** application.
2. Type the following command (include a space at the end):
   ```bash
   xattr -d com.apple.quarantine 
   ```
3. Drag and drop the `run_analysis.command` file from your Finder window into the Terminal window (this automatically fills in the path to the file) and press **Enter**.
4. Now you can **double-click** `run_analysis.command` in Finder to run the tool anytime!

#### 3. Running on Windows
* Double-click `run_analysis.bat` in File Explorer.
* The script will open a command window and run the analysis tool automatically.

#### 4. Specifying the Telemetry File Path
If the default file (`raw_telemetry_2ccf67f82f80_combined.csv`) is not found in your `Downloads` directory, the script will interactively ask you to paste or type the absolute path of your CSV telemetry file. You can simply drag and drop the telemetry CSV file into the terminal window to paste its path, then press **Enter**.

---

## Eestikeelne juhend

See tööriist analüüsib telemeetriaandmeid CSV-failidest, koondab veateateid, liigitab probleeme ning genereerib kokkuvõtlikud tabelid ja graafikud.

### Kuidas käivitada teises arvutis

Laadides selle repositooriumi alla ZIP-failina (või kloonides Git-iga), on kõik vajalikud failid koos pakitud:
1. `analyze_telemetry.py` - Peamine Pythoni analüüsiskript.
2. `run_analysis.command` - Topeltklõpsatav käivitaja **macOS-i** jaoks.
3. `run_analysis.bat` - Topeltklõpsatav käivitaja **Windowsi** jaoks.

#### 1. Nõuded
* Sinu arvutisse peab olema paigaldatud **Python 3** ([python.org](https://www.python.org/)).
* Skript paigaldab vajadusel puuduvad teegid (`pandas`, `numpy`, `matplotlib`) automaatselt esimesel käivitamisel.

#### 2. Käivitamine macOS-is
Veebibrauserist alla laaditud failidele lisab macOS turvapiirangu (quarantine flag). Kui üritad `run_analysis.command` faili topeltklõpsata, võib operatsioonisüsteem kuvada hoiatuse.

Turvapiirangu eemaldamiseks:
1. Ava rakendus **Terminal**.
2. Kirjuta järgmine käsk (lõpus peab olema tühik):
   ```bash
   xattr -d com.apple.quarantine 
   ```
3. Lohista `run_analysis.command` fail Finderi aknast Terminali aknasse (see täidab faili asukohatee automaatselt) ja vajuta **Enter**.
4. Nüüd saad käivitamiseks teha failil `run_analysis.command` lihtsalt topeltklõpsu!

#### 3. Käivitamine Windowsis
* Tee failil `run_analysis.bat` topeltklõps.
* Skript avab terminaliakna ning teostab analüüsi automaatselt.

#### 4. Telemeetria faili tee määramine
Kui vaikimisi faili (`raw_telemetry_2ccf67f82f80_combined.csv`) Sinu `Downloads` (Allalaadimised) kaustast ei leita, palub skript Sul sisestada või kopeerida CSV-faili asukoha tee. Saad lihtsalt lohistada oma CSV-faili terminaliaknasse ja vajutada **Enter**.
