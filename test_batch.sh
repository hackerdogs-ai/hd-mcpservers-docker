#!/bin/bash

BATCH_SIZE=50
STATE_FILE=".test_progress"
FAILED_FILE=".test_failures_more"

dirs=(*/test.sh)
TOTAL_SERVERS=${#dirs[@]}

if [ -f "$STATE_FILE" ]; then
    START_IDX=$(cat "$STATE_FILE")
else
    START_IDX=0
    echo "" > "$FAILED_FILE"
fi

if [ "$START_IDX" -ge "$TOTAL_SERVERS" ]; then
    echo "All $TOTAL_SERVERS servers tested! Check $FAILED_FILE for any failures."
    exit 0
fi

END_IDX=$((START_IDX + BATCH_SIZE))
if [ "$END_IDX" -gt "$TOTAL_SERVERS" ]; then
    END_IDX=$TOTAL_SERVERS
fi

echo "Testing servers $((START_IDX + 1)) to $END_IDX (out of $TOTAL_SERVERS)..."

for (( i=START_IDX; i<END_IDX; i++ )); do
    test_path="${dirs[$i]}"
    dir=$(dirname "$test_path")
    server_name=$(basename "$dir")
    
    echo "--- Testing [$((i + 1))/$TOTAL_SERVERS]: $server_name ---"
    
    cd "$dir" || continue
    chmod +x test.sh
    
    # AUTOMATIC FIX: Patch python3 to python for Git Bash
    if grep -q "python3 " test.sh; then
        echo ">>> 🔧 Auto-patching 'python3' to 'python' in test.sh..."
        sed -i 's/python3 /python /g' test.sh
    fi
    
    RESULT_FILE="test-results.txt"
    echo "========== Testing $server_name ==========" > "$RESULT_FILE"
    
    # THE FIX: Tag the image with BOTH the short name and the hackerdogs name
    echo ">>> Building Docker image: $server_name AND hackerdogs/$server_name:latest..."
    if docker build -t "$server_name" -t "hackerdogs/$server_name:latest" . >> "$RESULT_FILE" 2>&1; then
        echo ">>> Running test.sh..."
        if ./test.sh >> "$RESULT_FILE" 2>&1; then
            echo "✅ PASS: $server_name"
            echo -e "\n✅ PASS: $server_name" >> "$RESULT_FILE"
        else
            echo "❌ FAIL (Test): $server_name"
            echo -e "\n❌ FAIL (Test): $server_name" >> "$RESULT_FILE"
            echo "$server_name" >> "../$FAILED_FILE"
        fi
    else
        echo "❌ FAIL (Build): $server_name"
        echo -e "\n❌ FAIL (Build): $server_name" >> "$RESULT_FILE"
        echo "$server_name" >> "../$FAILED_FILE"
    fi
    
    cd ..
done

echo "$END_IDX" > "$STATE_FILE"
echo "Batch done. Progress: $END_IDX / $TOTAL_SERVERS."