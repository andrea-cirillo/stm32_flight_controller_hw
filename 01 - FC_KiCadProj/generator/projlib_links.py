# Schematic side of make_projlib.py: footprint fields point to the project library ACwing.pretty.
import sys, re, json, os
SCH = sys.argv[1]
s = open(SCH).read()
s2, n = re.subn(r'\(property "Footprint" "(?!DimaQuad:)[^":]+:([^"]+)"', r'(property "Footprint" "DimaQuad:\1"', s)
open(SCH, 'w').write(s2)
pj = SCH + '.parts.json'
p = json.load(open(pj))
for v in p.values():
    if v.get('fp') and ':' in v['fp']:
        v['fp'] = 'DimaQuad:' + v['fp'].split(':', 1)[1]
json.dump(p, open(pj, 'w'), indent=0)
print('schematic footprint links -> DimaQuad:', n)
