import json

# from typing import Optional, List


def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def write_json(file_path, data, minify:bool=False):
    with open(file_path, 'w') as file:
        if minify:
            json.dump(data, file, separators=(',',':'))
        else:
            json.dump(data, file, indent=2)
        


def load_cfm_traces(file_path, skip_ids=(), id_column='fid'):
    cfm_gj = read_json(file_path)

    out_features = []
    if len(skip_ids) == 0:
        return cfm_gj['features']
    else:
        for feature in cfm_gj['features']:
            if feature[id_column] in skip_ids:
                continue
            out_features.append(feature)

    return out_features


def _convert_properties(properties, conversion_dict):

    new_properties = {
        key: properties.get(value, None)
        for key, value in conversion_dict.items()
    }
    return new_properties


def load_nshm_traces(file_path, skip_ids=()):
    # TODO: Check fault traces for right-hand rule
    nshm_conversion_dict = {
        "id": "FaultID",
        "name": "FaultName",
        "dip": "DipDeg",
        "dip_dir": "DipDir",
        "rake": "Rake",
        "lower_depth": "LowDepth",
        "upper_depth": "UpDepth",
    }

    nshm_traces = load_cfm_traces(
        file_path, skip_ids=skip_ids, id_column='FaultID'
    )

    out_features = [
        {
            "geometry": feature["geometry"],
            "properties": _convert_properties(
                feature["properties"], nshm_conversion_dict
            ),
            "type": "Feature",
        }
        for feature in nshm_traces
    ]

    return out_features


def make_3d_tri_multipolygon(fault, tri_mesh):
    feature = {}
    feature['type'] = 'Feature'
    feature['geometry'] = {
        'type': 'MultiPolygon',
        'coordinates': [[t] for t in tri_mesh],
    }
    feature['properties'] = fault['properties']
    return feature


def write_cfm_tri_meshes(file_path, tri_meshes, faults, minify:bool=False):
    tri_features = [
        make_3d_tri_multipolygon(fault, tri_mesh)
        for fault, tri_mesh in zip(faults, tri_meshes)
    ]

    tri_mesh_gj = {
        'type': 'FeatureCollection',
        'features': tri_features,
    }

    write_json(file_path, tri_mesh_gj, minify=minify)
