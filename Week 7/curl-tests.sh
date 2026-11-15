#!/bin/bash
# Week 7 API tests for PropertyLite serverless read path
BASE_URL="https://08xbwl2f0i.execute-api.us-east-1.amazonaws.com"

echo "Existing listing (expect the full JSON row):"
curl -s "$BASE_URL/properties/R100234"
echo
echo

echo "Second listing:"
curl -s "$BASE_URL/properties/R100235"
echo
echo

echo "Nonexistent listing (expect {}):"
curl -s "$BASE_URL/properties/FAKE"
echo
