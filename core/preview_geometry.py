"""Read authored Custom node locations instead of inventing an outline."""
from __future__ import annotations
import math
import re
import xml.etree.ElementTree as ET


def node_ranges(value):
    nodes = set()
    for token in value.split(','):
        token = token.strip()
        if not token:
            continue
        if re.fullmatch(r'\d+-\d+', token):
            a, b = map(int, token.split('-'))
            nodes.update(range(min(a,b), max(a,b)+1))
        elif token.isdigit():
            nodes.add(int(token))
        else:
            raise ValueError('Unsupported node range: ' + token)
    return nodes


def custom_nodes(model):
    """Return (node number, world XYZ), retaining repeated AC bulb addresses."""
    attrs = model.attrib
    cells = []
    compressed = attrs.get('CustomModelCompressed', '')
    if compressed:
        for entry in compressed.split(';'):
            if entry.strip():
                n, row, col, depth = map(int, entry.split(','))
                if n > 0:
                    cells.append((n, col, -row, -depth))
    else:
        for z, layer in enumerate(attrs.get('CustomModel', '').split('|')):
            for y, row in enumerate(layer.split(';')):
                for x, value in enumerate(row.split(',')):
                    if value.strip().isdigit() and int(value) > 0:
                        cells.append((int(value), x, -y, -z))
    if not cells:
        return []
    # xLights centers the occupied bounding box, then scales/rotates/translates.
    center = [(min(c[i] for c in cells)+max(c[i] for c in cells))/2 for i in (1,2,3)]
    result = []
    for n, x, y, z in cells:
        p = [(v-center[i])*float(attrs.get('Scale'+'XYZ'[i], '1')) for i,v in enumerate((x,y,z))]
        for i, j, axis in ((1,2,'X'), (2,0,'Y'), (0,1,'Z')):
            angle = math.radians(float(attrs.get('Rotate'+axis, '0')))
            a, b = p[i], p[j]
            p[i], p[j] = a*math.cos(angle)-b*math.sin(angle), a*math.sin(angle)+b*math.cos(angle)
        result.append((n, tuple(p[i]+float(attrs.get('WorldPos'+axis, '0')) for i,axis in enumerate('XYZ'))))
    return result


def authored_geometry(path):
    geometry, faces = {}, {}
    for model in ET.parse(path).findall('models/model'):
        name = model.get('name')
        nodes = custom_nodes(model) if model.get('DisplayAs') == 'Custom' else []
        if not nodes:
            continue
        geometry[name] = tuple(p[:2] for _,p in nodes)
        by_node = {}
        for number, point in nodes:
            by_node.setdefault(number, []).append(point[:2])
        def selected_points(selected):
            return tuple(point for number in sorted(selected) for point in by_node.get(number, ()))
        for sub in model.findall('subModel'):
            selected = set().union(*(node_ranges(v) for k,v in sub.attrib.items() if k.startswith('line')))
            geometry[name+'/'+sub.get('name','')] = selected_points(selected)
        for face in model.findall('faceInfo'):
            for key, value in face.attrib.items():
                if key.startswith('Mouth-') and value:
                    selected = node_ranges(value)
                    alias = name+'/@face/'+face.get('Name','')+'/'+key[6:]
                    geometry[alias] = selected_points(selected)
                    faces[(name, face.get('Name',''), key[6:].lower())] = alias
    return geometry, faces
