#!/bin/bash

# Konfigurasi
DB_USER=${DB_USER}
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
TRUNCATE_SQL=${TRUNCATE_SQL:-/app/converter-json2gml/truncate_all.sql}
BACKUP_FILE=${BACKUP_FILE:-/app/converter-json2gml/backup.dump}
export PGPASSWORD=${DB_PASS}

echo "🧹 Menghapus seluruh isi database..."
psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -f "$TRUNCATE_SQL"
if [ $? -ne 0 ]; then
    echo "❌ Gagal menghapus isi database. Proses dibatalkan."
    exit 1
fi

echo "📦 Melakukan restore dari file backup (.dump)..."
pg_restore -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -c --no-owner --role="$DB_USER" "$BACKUP_FILE"
if [ $? -ne 0 ]; then
    echo "❌ Restore gagal. Silakan periksa kembali file backup atau koneksi database."
    exit 1
else
    echo "✅ Database berhasil di-reset ke kondisi sebelum import."
fi