#!/bin/bash

# Base directory containing the input files
BASE_DIR="50/AGA/2025_06_09"
OUTPUT_DIR="50/AGA/2025_06_09"
LOG_FILE="50/AGA/2025_06_09/processing.log"

# Database connection parameters
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="dkj"
DB_SCHEMA="citydb"
DB_USER="postgres"
DB_PASS="admin1234"
IMPEXP_PATH="/Applications/3DCityDB-Importer-Exporter/bin/impexp"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Initialize log file
echo "Processing started at $(date)" > "$LOG_FILE"

# Function to show progress bar
show_progress() {
    local current=$1
    local total=$2
    local filename=$3
    local operation=$4
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    local remaining=$((width - completed))
    
    # Clear line and show progress
    printf "\r\033[K"
    printf "Progress: ["
    printf "%*s" $completed | tr ' ' '='
    printf "%*s" $remaining | tr ' ' '-'
    printf "] %d%% (%d/%d) %s: %s" $percentage $current $total "$operation" "$filename"
}

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Count total JSON files using a more compatible method
echo "🔍 Scanning for JSON files..."

# Create temporary file to store file list
temp_file=$(mktemp)
find "$BASE_DIR" -name "*.json" -type f > "$temp_file" 2>/dev/null

# Count files
total_files=$(wc -l < "$temp_file" | tr -d ' ')

if [ "$total_files" -eq 0 ]; then
    echo "❌ No JSON files found in $BASE_DIR"
    rm -f "$temp_file"
    exit 1
fi

echo "✅ Found $total_files JSON files to process"
echo "📝 Logging to: $LOG_FILE"
echo ""

log_message "Found $total_files JSON files to process"

# Initialize counters
current_file=0
success_count=0
error_count=0

# Process each file
while IFS= read -r json_file; do
    # Skip empty lines
    [ -z "$json_file" ] && continue
    
    current_file=$((current_file + 1))
    
    # Extract filename without path and extension
    filename=$(basename "$json_file" .json)
    
    # Create output filename
    output_file="$OUTPUT_DIR/${filename}.gml"
    
    # Create ID prefix from filename
    id_prefix="${filename}_"
    
    log_message "Processing file $current_file/$total_files: $filename"
    
    # Show progress for import
    show_progress $current_file $total_files "$filename" "Importing"
    
    # Import CityJSON
    $IMPEXP_PATH \
        import \
        -T postgresql \
        -H $DB_HOST \
        -P $DB_PORT \
        -d $DB_NAME \
        -S $DB_SCHEMA \
        -u $DB_USER \
        -p $DB_PASS \
        "$json_file" > /dev/null 2>&1
    
    import_status=$?
    
    if [ $import_status -eq 0 ]; then
        log_message "Import successful for $filename"
        
        # Show progress for export
        show_progress $current_file $total_files "$filename" "Exporting"
        
        # Export to CityGML
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
            --id-prefix "$id_prefix" > /dev/null 2>&1
        
        python bbox.py "$output_file" --no-backup > /dev/null 2>&1

        export_status=$?
        
        if [ $export_status -eq 0 ]; then
            log_message "Export successful for $filename"
            success_count=$((success_count + 1))
        else
            printf "\n❌ Export failed for: %s\n" "$filename"
            log_message "Export failed for $filename"
            error_count=$((error_count + 1))
        fi
    else
        printf "\n❌ Import failed for: %s\n" "$filename"
        log_message "Import failed for $filename"
        error_count=$((error_count + 1))
    fi
    
    # Show progress for database reset
    show_progress $current_file $total_files "$filename" "Resetting DB"
    
    # Reset database after each iteration
    sh resetdb.sh > /dev/null 2>&1
    log_message "Database reset completed for $filename"
    
done < "$temp_file"

# Clean up temporary file
rm -f "$temp_file"

# Final completion message
printf "\n\n✅ Processing completed!\n"
printf "📊 Summary:\n"
printf "   • Total files: %d\n" $total_files
printf "   • Successful: %d\n" $success_count
printf "   • Failed: %d\n" $error_count
printf "📝 Check %s for detailed logs\n" "$LOG_FILE"

log_message "Processing completed. Success: $success_count, Failed: $error_count"
