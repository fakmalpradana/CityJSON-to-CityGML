/Applications/3DCityDB-Importer-Exporter/bin/impexp \
    import \
    -T postgresql \
    -H localhost \
    -P 5432 \
    -d dkj \
    -S citydb \
    -u postgres \
    -p admin1234 \
    50/AH_03/AH_03_B/AH_03_B.json \

/Applications/3DCityDB-Importer-Exporter/bin/impexp \
    export \
    -T postgresql \
    -H localhost \
    -P 5432 \
    -d dkj \
    -S citydb \
    -u postgres \
    -p admin1234 \
    -o 50/CityGML/AH_30_B.gml \
    --compressed-format citygml \
    --replace-ids \
    --id-prefix AH_30_B_

sh resetdb.sh