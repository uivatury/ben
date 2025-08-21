#!/bin/bash
accepted=0
rejected=0

for i in {1..20}; do
    result=$(curl -s "http://127.0.0.1:8085/claim?hand=AKQ.AKQ.AKQ.AKQ6&dummy=432.432.432.5432&dealer=S&seat=S&vul=&ctx=7N------&played=SJ&tricks=13&user=uday7nt")
    
    if echo "$result" | grep -q '"accepted":true'; then
        accepted=$((accepted+1))
        echo "Test $i: ACCEPTED"
    else
        rejected=$((rejected+1))
        echo "Test $i: REJECTED"
    fi
done

echo "=== FINAL RESULTS ==="
echo "Accepted: $accepted"
echo "Rejected: $rejected"
echo "Total: $((accepted+rejected))"