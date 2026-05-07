#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: ./delete-movie.sh \"Movie Title\""
    exit 1
fi

MOVIE_TITLE=$1

read -sp "Admin Password: " ADMIN_PASS
echo -e "\nSending delete request..."

cp ../data/search/movies.csv ../data/search/movies.csv.bak

sed -i "/^$MOVIE_TITLE,/d" ../data/search/movies.csv

RESPONSE=$(curl -s -X DELETE http://kubeflix.local/api/delete \
     -H "Content-Type: application/json" \
     -H "X-Admin-Token: $ADMIN_PASS" \
     -d "{\"title\": \"$MOVIE_TITLE\"}")

if [[ $RESPONSE != *"deleted successfully"* ]]; then
    echo "API failed, reverting local file change..."
    mv ../data/search/movies.csv.bak ../data/search/movies.csv
    echo "$RESPONSE"
    exit 1
else
    rm ../data/search/movies.csv.bak
fi

echo -e "\n$RESPONSE"