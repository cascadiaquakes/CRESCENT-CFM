import json
from pathlib import Path
from typing import Optional, List, Tuple

import geopandas as gpd


def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def write_json(file_path, data, minify: bool = False):
    with open(file_path, 'w') as file:
        if minify:
            json.dump(data, file, separators=(',', ':'))
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


def load_canada_traces(file_path, skip_ids=()):
    canada_conversion_dict = {
        "id": "fid",
        "name": "name",
        "dip": "dip",
        "dip_dir": "dip_dir",
        "rake": "rake",
        "lower_depth": "lsd",
        "upper_depth": "usd",
    }

    canada_traces = load_cfm_traces(
        file_path, skip_ids=skip_ids, id_column='id'
    )

    out_features = [
        {
            "geometry": feature["geometry"],
            "properties": _convert_properties(
                feature["properties"], canada_conversion_dict
            ),
            "type": "Feature",
        }
        for feature in canada_traces
    ]

    for feature in out_features:
        feature['properties']['source'] = "NRCan Faults"

    return out_features


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

    for feature in out_features:
        feature['properties']['source'] = "US NSHM 2023"

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


def write_cfm_tri_meshes(file_path, tri_meshes, faults, minify: bool = False):
    tri_features = [
        make_3d_tri_multipolygon(fault, tri_mesh)
        for fault, tri_mesh in zip(faults, tri_meshes)
    ]

    tri_mesh_gj = {
        'type': 'FeatureCollection',
        'features': tri_features,
    }

    write_json(file_path, tri_mesh_gj, minify=minify)


def write_cfm_trace_geojson(outfile, cfm_trace_features, minify: bool = False):
    cfm_json = {
        "type": "FeatureCollection",
        "name": "can_cascadia_faults",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
        }

    cfm_json["features"] = cfm_trace_features

    write_json(outfile, cfm_json, minify=minify)
    

def convert_cfm_geojson(cfm_geojson:str, 
                       outfile_types: Tuple[str]=('geopackage',)
                       )->None:
    cfm = gpd.read_file(cfm_geojson)
    cfm_path = Path(cfm_geojson)

    for out_type in outfile_types:
        if out_type == 'geopackage':
            gpkg_outfile = cfm_path.with_suffix('.gpkg')
            cfm.to_file(gpkg_outfile, driver='GPKG')
        

        elif out_type == 'shp':
            shp_outfile = cfm_path.with_suffix('.shp')
            cfm.to_file(shp_outfile)

        else:
            raise NotImplementedError(
                    f"Filetype {out_type} not currently supported."
                    )
