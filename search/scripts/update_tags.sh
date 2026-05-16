#!/bin/bash

CSV_FILE="../kubeflix_movies_dataset.csv"
TXT_FILE="../unique_tags.txt"

echo "Reading the CSV file and extracting tags..."

cut -d',' -f2- "$CSV_FILE" | tr ',' '\n' | sed 's/\r//' | grep -v '^\s*$' | tr '[:upper:]' '[:lower:]' | sort -u > "$TXT_FILE"

echo "Done! The file $TXT_FILE has been updated with all the tags."