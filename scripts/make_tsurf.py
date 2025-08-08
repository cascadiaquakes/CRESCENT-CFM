import numpy as np
import json
import pyproj as pj

boilerplate = ("""GOCAD TSurf 1
HEADER {
""",
"""name:{}
""",
"""*visible:true
*solid*color:0.977372 0.860067 0.877517 1
}
GOCAD_ORIGINAL_COORDINATE_SYSTEM
NAME Default
AXIS_NAME "X" "Y" "Z"
AXIS_UNIT "m" "m" "m"
ZPOSITIVE Elevation
END_ORIGINAL_COORDINATE_SYSTEM
TFACE
""")


def make_tsurf(feature, epsg=32611, return_data=False, outfile=None):
    vertices = {}
    trgls = []
    for tri in feature['geometry']['coordinates']:
        pts = tri[0]
        for pt in pts:
            tp = tuple(pt)
            if tp not in vertices:
                vertices[tp] = len(vertices) + 1
        trgls.append([vertices[tuple(pts[0])],
                      vertices[tuple(pts[1])],
                      vertices[tuple(pts[2])]])
    if return_data:    
        return vertices, trgls
    
    vert_rev = {v:k for k, v in vertices.items()}
    trans = pj.Transformer.from_crs(4326, epsg, always_xy=True)
    
    bp = boilerplate
    lines = [bp[0], bp[1].format(feature['properties']['name']), bp[2]]
    for i in sorted(vertices.values()):
        ee, nn, zz = trans.transform(*vert_rev[i])
        line = f"VRTX {i}  {ee} {nn} {zz}\n"
        lines.append(line)
        
    for trgl in trgls:
        lines.append(f"TRGL {trgl[0]} {trgl[1]} {trgl[2]}\n")
        
    lines.append("END")
    
    if outfile:
        with open(outfile, "w") as f:
            for line in lines:
                f.write(line)
    else:
        return lines

# do crustal faults
gj_file = "../crescent_cfm_files/crescent_cfm_crustal_3d.geojson"

with open(gj_file) as f:
    gj = json.load(f)


fs = gj['features']

names = {}
for feat in fs:
    name = feat['properties']['name'].replace(' ', '_')
    feat['properties']['name'] = name
    if name not in names:
        names[name] = 0
    else:
        names[name] += 1
        name = name + f"_{names[name]}"
        
    outfile = f"../crescent_cfm_files/tsurf/{name}.ts"
    make_tsurf(feat, outfile=outfile)

# do subduction zones
subduction_zone_meshes = [
    "../crescent_cfm_files/casie21_plate_boundary_multipart.geojson",
    "../crescent_cfm_files/mccrory_2012_cascadia_interface.geojson",
    "../crescent_cfm_files/slab2_cascadia_interface_multipart.geojson"
]

for szf in subduction_zone_meshes:
    with open(szf) as f:
        gj = json.load(f)
        for feat in gj['features']:
            name = feat['properties']['name']
            outfile = f"../crescent_cfm_files/tsurf/{name}.ts"
            make_tsurf(feat, outfile=outfile)

