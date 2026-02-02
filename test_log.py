from truyen import log_failure
import json
import os

print("Testing log_failure...")

# Test 1: Log a new chapter for an existing comic
log_failure("ta-la-ta-de", 999)

# Test 2: Log a new comic
log_failure("test-comic", 1)
log_failure("test-comic", 2)

# Verify
with open("log_fail.json", "r") as f:
    data = json.load(f)
    print("Current Log Data:", json.dumps(data, indent=4))
    
    assert "999" in data["ta-la-ta-de"]
    assert "1, 2" in data["test-comic"]

print("Test Passed!")
