import re
import json

# Data is downloaded from https://maps.massgis.digital.mass.gov/MassMapper/MassMapper.html
# Using layer: Massachusetts Municipalities Multipar Polygons
# and exported as lat/lon as shapefile in WGS84
# Downloaded data is passed to https://mapshaper.org/ 
# and simplified to > 5 % of the original file size, fixing any line crossings.
# The resulting data is saved as MA_towns.json into this repository.
with open('MA_towns.json') as f:
    data = json.load(f)

for i, f in enumerate(data['features']):
    f['id'] = f['properties']['town']

# Parse input data in three files
stretch_code_table = re.compile("(?P<name>[a-zA-Z\ ]+)\ [0-9\,]+[a-zA-Z\ ]+[0-9/]+\ (?P<date>[0-9/]+)")
specialized_code_table = re.compile("(?P<name>[a-zA-Z\ ]+)\ (?P<date>[0-9/]+)")

# Stretch code
stretch_code = {}
with open('stretch_code.dat') as f:
    for line in f:
        out = stretch_code_table.search(line)
        if out is not None:
            stretch_code[out.group('name')] = out.group('date')

# Specialized opt-in stretch code
specialized_opt_in = {}
with open('specialized_opt_in.dat') as f:
    for line in f:
        out = specialized_code_table.search(line)
        if out is not None:
            specialized_opt_in[out.group('name')] = out.group('date')

# Approved list of fossil-fuel free pilot towns
fossil_fuel_free = []
with open('fossil_fuel_free.dat') as f:
    for line in f:
        fossil_fuel_free.append(line.strip())

# Now we add that information into the geojson file
for town in data['features']:
    name = town['properties']['town'].title()
    town['properties']['stretchcode'] = stretch_code.get(name, 'not yet')
    town['properties']['optinstretchcode'] = specialized_opt_in.get(name, 'not yet')
    town['properties']['fossilfuel'] = 'fossil fuel ban pilot' if name in fossil_fuel_free else ''
    if name in specialized_opt_in:
        code_color = 2
    elif name in stretch_code:
        code_color = 1
    else:
        code_color = 0
    if name in fossil_fuel_free:
        code_color += 10
        
    town['properties']['code_color'] = code_color

# And write it into docs/MA_energy_codes_town.js such that it's read directly as a javascript file
# That way, we get a file very similar to https://leafletjs.com/examples/choropleth/
with open('docs/MA_energy_codes_town.js', 'w') as f:
    f.write('var townsData = ' + json.dumps(data) + ';')