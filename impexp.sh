#!/bin/bash

# Base directory containing the input files
BASE_DIR=${BASE_DIR}
OUTPUT_DIR=${OUTPUT_DIR}
LOG_FILE=${LOG_FILE}

# Database connection parameters
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_SCHEMA=${DB_SCHEMA}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
IMPEXP_PATH=${IMPEXP_PATH}
BBOXPY_PATH=${BBOXPY_PATH:-/app/converter-json2gml/bbox.py}
RESETDB_PATH=${RESETDB_PATH:-/app/converter-json2gml/resetdb.sh}

# Export password untuk psql dan pg_restore
export PGPASSWORD=${DB_PASS}

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

python "$BBOXPY_PATH" "$output_file" --no-backup

sh "$RESETDB_PATH"