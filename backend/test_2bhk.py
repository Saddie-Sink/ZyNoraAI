import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.app.ml.floorplan_generator import FloorplanGenerator

gen = FloorplanGenerator()
payload = {
    'property': {'builtUpArea': 2200, 'floors': 2},
    'family': {'rooms': {'bedrooms': 2, 'bathrooms': 2}},
    'location': {'orientation': 'East'}
}
cands = gen.generate_candidates(payload)
print(f"Top Candidate: {cands[0]['code']} - {cands[0]['title']}")
print(f"Bedrooms: {cands[0]['bedrooms']}, Bathrooms: {cands[0]['bathrooms']}")
print("Rooms generated:")
for r in cands[0]['rooms']:
    print(f"  - {r['name']}: {r['area']} sq ft ({r['type']})")
