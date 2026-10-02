import urllib.request, json

data = json.dumps({
  "id": "proj-001",
  "property": {"builtUpArea": 2200, "floors": 2},
  "family": {"rooms": {"bedrooms": 2, "bathrooms": 2}},
  "location": {"orientation": "East"},
  "style": {"architecturalStyle": "Modern"}
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/floorplans/generate",
    data=data,
    headers={"Content-Type": "application/json"}
)
r = urllib.request.urlopen(req)
result = json.loads(r.read())
cands = result["data"]["candidates"]

print("Generated:", result["data"]["count"], "candidates")
print("RF R2:", result["data"]["rfR2Score"])
print()
print(f"Top candidate: {cands[0]['code']} ({cands[0]['title']})")
print(f"Bedrooms: {cands[0]['bedrooms']}, Bathrooms: {cands[0]['bathrooms']}")
print("Rooms list:")
for r in cands[0]["rooms"]:
    print(f"  - {r['name']}: {r['area']} sq ft ({r['type']})")
