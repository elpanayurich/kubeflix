#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: ./add-movie.sh \"Movie Title\" \"tags\""
    exit 1
fi

MOVIE_TITLE=$1
MOVIE_TAGS=$2

read -sp "Admin Password: " ADMIN_PASS

if [ -s ../data/search/movies.csv ] && [ "$(tail -c1 ../data/search/movies.csv | wc -l)" -eq 0 ]; then
    echo "" >> ../data/search/movies.csv
fi

echo "$MOVIE_TITLE,$MOVIE_TAGS" >> ../data/search/movies.csv

RESPONSE=$(curl -s -X POST http://kubeflix.local/api/add \
   -H "Content-Type: application/json" \
   -H "X-Admin-Token: $ADMIN_PASS" \
   -d "{\"title\": \"$MOVIE_TITLE\", \"tags\": \"$MOVIE_TAGS\"}")

if [[ $RESPONSE != *"added correctly"* ]]; then
    echo -e "\nAPI failed, reverting local file change..."
    sed -i '$d' ../data/search/movies.csv
    echo "$RESPONSE"
    exit 1
fi

echo -e "\n$RESPONSE"