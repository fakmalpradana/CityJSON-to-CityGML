# CityJSON to CityGML Converter
Aplikasi untuk konversi CityJSON menuju CityGML. Cara penggunaan sebagai berikut

## Single Processing

Jalankan dalam shell/git bash

```bash
sh impexp.sh
```
Untuk konfigurasi file, silahkan edit di file `impexp_batch.sh` seperti dibawah ini
```bash
json_file="file.json"
output_file="file.gml"
LOG_FILE="file.log"
```
    
## Batch Processing

Jalankan dalam shell/git bash

```bash
sh impexp_batch.sh
```
Untuk konfigurasi file, silahkan edit di file `impexp_batch.sh` seperti dibawah ini
```bash
BASE_DIR="50/AGA/2025_06_10"
OUTPUT_DIR="50/AGA/2025_06_10"
LOG_FILE="50/AGA/2025_06_10/processing.log"
```
    
## DB config

Pastikan sebelum menggunakan CLI app ini, konfigurasi DB dalam file `impexp.sh` atau `impexp_batch.sh` sudah benar

```bash
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="dkj"
DB_SCHEMA="citydb"
DB_USER="postgres"
DB_PASS="admin1234"
IMPEXP_PATH="/Applications/3DCityDB-Importer-Exporter/bin/impexp"
```

