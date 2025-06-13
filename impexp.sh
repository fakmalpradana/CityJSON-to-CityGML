#!/bin/bash

# Base directory containing the input files
json_file="file.json"
output_file="file.gml"
LOG_FILE="file.log"

# Database connection parameters
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="dkj"
DB_SCHEMA="citydb"
DB_USER="postgres"
DB_PASS="admin1234"
IMPEXP_PATH="/Applications/3DCityDB-Importer-Exporter/bin/impexp"

$IMPEXP_PATH \
    import \
    -T postgresql \
    -H $DB_HOST \
    -P $DB_PORT \
    -d $DB_NAME \
    -S $DB_SCHEMA \
    -u $DB_USER \
    -p $DB_PASS \
    "$json_file" 

$IMPEXP_PATH \
    export \
    -T postgresql \
    -H $DB_HOST \
    -P $DB_PORT \
    -d $DB_NAME \
    -S $DB_SCHEMA \
    -u $DB_USER \
    -p $DB_PASS \
    -o "$output_file" \
    --compressed-format citygml \
    --replace-ids \
    --id-prefix "$id_prefix"

python bbox.py "$output_file" --no-backup

sh resetdb.sh