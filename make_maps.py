import re
import json
import copy
from datetime import date, timedelta, datetime

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
stretch_code_table = re.compile("(?P<name>[a-zA-Z\ ]+)\ [0-9\,]+ (?P<date>[0-9/]+)")
specialized_code_table = re.compile("(?P<name>[a-zA-Z\ ]+)\ [0-9\,]+ (?P<date>[0-9/]+) (?P<specialdate>[0-9/]*)")

# Stretch code
stretch_code = {}
specialized_opt_in = {}
with open('code_dates.dat') as f:
    for line in f:
        out = stretch_code_table.search(line)
        if out is not None:
            stretch_code[out.group('name')] = out.group('date')
        out = specialized_code_table.search(line)
        if out is not None:
            specialized_opt_in[out.group('name')] = out.group('specialdate')

# Approved list of fossil-fuel free pilot towns
fossil_fuel_free = []
with open('fossil_fuel_free.dat') as f:
    for line in f:
        fossil_fuel_free.append(line.strip())

print(f'Number of municipalities in geojson file: {len(data["features"])}')
print(f'Number of municipalities with base code: {len(data["features"]) - len(stretch_code)}')
print(f'Number of municipalities with stretch code (incl. those with opt-in stretch code): {len(stretch_code) - len(specialized_opt_in)}')
print(f'Number of municipalities with specialized opt-in stretch code: {len(specialized_opt_in)}')
print(f'Number of municipalities with fossil-fuel free: {len(fossil_fuel_free)}')

def USdate_to_ISO(datestr, subtractdays=0):
    return (datetime.strptime(datestr, '%m/%d/%Y') -
            timedelta(days=subtractdays)).isoformat()

# Now we build up the geojson file with the data we want to display
featurelist = []

for town in data['features']:
    name = town['properties']['town'].title()
    town['properties']['stretchcode'] = stretch_code.get(name, 'not yet')
    town['properties']['optinstretchcode'] = specialized_opt_in.get(name, 'not yet')
    town['properties']['fossilfuel'] = 'Fossil Fuel Free prioritized community (draft)' if name in fossil_fuel_free else ''

    dates = [('01/01/2009', 0), ('01/02/2025', None)]
    if name in stretch_code:
        dates.append((stretch_code.get(name), 1))
    if name in specialized_opt_in:
        dates.append((specialized_opt_in.get(name), 1))
    if name in fossil_fuel_free:
        dates.append(('07/01/2024', 10))

    dates.sort(key=lambda x: datetime.strptime(x[0], '%m/%d/%Y'))

    feature = {'type': 'Feature',
               'geometry': town['geometry'],
               'properties': town['properties']}
    feature['properties']['stretchcode'] = stretch_code.get(name, 'not yet')
    feature['properties']['optinstretchcode'] = specialized_opt_in.get(name, 'not yet')
    feature['properties']['fossilfuel'] = 'Fossil Fuel Free prioritized community (draft)' if name in fossil_fuel_free else ''

    codecolor = 0
    for i, d in enumerate(dates[:-1]):
        codecolor = codecolor + d[1]
        code = copy.deepcopy(feature)
        code['properties']['code_color'] = codecolor
        code['properties']['start'] = USdate_to_ISO(d[0])
        code['properties']['end'] = USdate_to_ISO(dates[i + 1][0], subtractdays=1)
        featurelist.append(code)

    outdata = {'type': 'FeatureCollection', 'features': featurelist}


# And write it into docs/MA_energy_codes_town.js such that it's read directly as a javascript file
# That way, we get a file very similar to https://leafletjs.com/examples/choropleth/
with open('docs/MA_energy_codes_town.js', 'w') as f:
    f.write('var townsData = ' + json.dumps(outdata) + ';')

base_code = []
for town in data['features']:
    name = town['properties']['town'].title()
    if name not in stretch_code:
         base_code.append(name)
base_code.sort()

for name in base_code:
    print(name)

print(len(base_code))

