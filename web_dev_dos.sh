#!/bin/bash

URL="https://d2yjm0oiyxkgds.cloudfront.net/"

# Make 20 rapid requests (no delay)
for i in {1..30}
do
    echo "Request #$i"
    curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" "$URL" &
done

wait  # Wait for all curls to complete