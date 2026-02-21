import re
import json
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
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


def load_cfm_traces(file_path, skip_ids=(), include_ids=(), id_column='fid'):
    if len(skip_ids) > 0 and len(include_ids) > 0:
        raise ValueError("Cannot use both 'skip_ids' and 'include_ids' parameters")

    cfm_gj = read_json(file_path)

    out_features = []
    if len(skip_ids) == 0 and len(include_ids) == 0:
        return cfm_gj['features']
    elif len(include_ids) > 0:
        for feature in cfm_gj['features']:
            if feature['properties'][id_column] in include_ids:
                out_features.append(feature)
    else:
        for feature in cfm_gj['features']:
            if feature['properties'][id_column] in skip_ids:
                continue
            out_features.append(feature)

    return out_features


def _convert_properties(properties, conversion_dict):

    new_properties = {
        key: properties.get(value, None)
        for key, value in conversion_dict.items()
    }
    return new_properties


def load_canada_traces(file_path, skip_ids=(), include_ids=()):
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
        file_path, skip_ids=skip_ids, include_ids=include_ids, id_column='fid'
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


def load_nshm_traces(file_path, skip_ids=(), include_ids=()):
    # TODO: Check fault traces for right-hand rule
    nshm_conversion_dict = {
        "nshm_id": "FaultID",
        "name": "FaultName",
        "dip": "DipDeg",
        "dip_dir": "DipDir",
        "rake": "Rake",
        "lower_depth": "LowDepth",
        "upper_depth": "UpDepth",
    }

    nshm_traces = load_cfm_traces(
        file_path, skip_ids=skip_ids, include_ids=include_ids, id_column='FaultID'
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

    for i, feature in enumerate(out_features):
        feature['properties']['CFM_ID'] = "us" + str(i+1).zfill(3)
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

_MISSING_STRINGS = {
    "unspecified",
    "unknown",
    "n/a",
    "na",
    "--",
    "none",
    "null",
}


def _is_missing_str(val: Optional[str]) -> bool:
    if val is None:
        return True
    s = str(val).strip()
    if s == "":
        return True
    return s.lower() in _MISSING_STRINGS


def _extract_numbers(text: str) -> List[float]:
    # integers/decimals; metadata are expected to be positive magnitudes
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]


def _parse_mean_of_range(text: str) -> Optional[float]:
    """
    Rules:
      - "A to B" / "A-B" / "Between A and B" -> mean(A,B)
      - "A ± e" / "A+/-e" -> A
      - otherwise, first numeric value
      - "< X" / "Less than X" -> X (bound)
    """
    if _is_missing_str(text):
        return None
    s = str(text).strip()
    s_low = s.lower()
    nums = _extract_numbers(s_low)
    if not nums:
        return None

    if ("±" in s) or ("+/-" in s_low) or ("+/-" in s):
        return nums[0]

    if "between" in s_low and "and" in s_low and len(nums) >= 2:
        return 0.5 * (nums[0] + nums[1])

    if (" to " in s_low or "-" in s_low) and len(nums) >= 2:
        return 0.5 * (nums[0] + nums[1])

    if "<" in s_low or "less than" in s_low:
        return nums[0]

    return nums[0]


def _parse_dip(dip_raw: Optional[str]) -> Tuple[Optional[float], bool]:
    """
    Additional rules:
      - 'vertical' or 'subvertical' -> 90
      - ranges -> mean
      - 'A ± e' -> A
      - 'subvertical to X' -> mean(90, X)
    Returns (dip_deg, is_vertical_or_subvertical).
    """
    if dip_raw is None:
        return None, False
    s = str(dip_raw).strip()
    if _is_missing_str(s):
        return None, False

    s_low = s.lower()
    vertical_hint = ("vertical" in s_low)  # includes "subvertical"
    nums = _extract_numbers(s_low)

    if vertical_hint and not nums:
        return 90.0, True

    if vertical_hint and (" to " in s_low or "-" in s_low) and nums:
        if len(nums) == 1:
            return 0.5 * (90.0 + nums[0]), True
        return 0.5 * (nums[0] + nums[1]), True

    dip = _parse_mean_of_range(s)
    if dip is None:
        return None, vertical_hint
    if vertical_hint and dip >= 80.0:
        return dip, True
    return dip, vertical_hint


def _parse_dip_dir(dip_dir_raw: Optional[str], is_vertical: bool) -> Optional[str]:
    # If dip-dir is missing/unspecified and the fault is (sub)vertical => "Vertical"
    if _is_missing_str(dip_dir_raw):
        return "Vertical" if is_vertical else None
    s = str(dip_dir_raw).strip()
    if _is_missing_str(s):
        return "Vertical" if is_vertical else None
    if s.lower() == "vertical":
        return "Vertical"
    return s


def _rake_from_slip_sense(slip_sense_raw: Optional[str]) -> Optional[float]:
    """
    Map Slip_Sense strings to Aki-Richards rake (degrees).

    Convention used:
      - left-lateral strike-slip: 0
      - right-lateral strike-slip: 180
      - reverse: 90
      - normal: -90
      - oblique combinations use 45-degree offsets.
    """
    if _is_missing_str(slip_sense_raw):
        return None
    s = str(slip_sense_raw).strip().lower()
    if _is_missing_str(s) or "uncertain" in s:
        return None

    has_left = "left" in s
    has_right = "right" in s
    has_reverse = ("reverse" in s) or ("south-side up" in s)
    has_normal = ("normal" in s) or ("extensional" in s)
    has_oblique = "oblique" in s
    has_strike = ("strike-slip" in s) or ("strike slip" in s)

    if has_reverse and has_right:
        return 135.0
    if has_reverse and has_left:
        return 45.0
    if has_normal and has_right:
        return -135.0
    if has_normal and has_left:
        return -45.0

    if has_reverse:
        return 90.0
    if has_normal:
        return -90.0

    if has_right:
        return 180.0
    if has_left:
        return 0.0
    if has_strike:
        return 0.0  # unspecified strike-slip sense

    if has_oblique:
        return None
    return None


def _parse_strike(ave_strike_raw: Optional[str]) -> Optional[float]:
    if _is_missing_str(ave_strike_raw):
        return None
    s = str(ave_strike_raw).strip()
    if _is_missing_str(s):
        return None
    s_low = s.lower()

    if s_low in {"e-w", "ew"}:
        return 90.0
    if s_low in {"n-s", "ns"}:
        return 0.0

    nums = _extract_numbers(s_low)
    if not nums:
        return None
    return nums[0] % 360.0


def _parse_slip_rate_mm_yr(slip_rate_raw: Optional[str]) -> Optional[float]:
    # Best-effort parsing; keep raw separately.
    if _is_missing_str(slip_rate_raw):
        return None
    s = str(slip_rate_raw).strip()
    if _is_missing_str(s):
        return None
    if "unknown" in s.lower():
        return None
    return _parse_mean_of_range(s)


def load_nrcan_traces(file_path, skip_ids=(), include_ids=()):
    """
    Loader for / WesternCanada_QuaternaryFaults_elev.geojson

    - Parses Dip (+ vertical/subvertical rules + ranges/±)
    - Sets dip_dir="Vertical" if missing and (sub)vertical
    - Converts Slip_Sense -> rake (Aki-Richards)
    - Sets source='NRCan'
    """
    conversion_dict = {
        "CFM_ID": "fid",
        "name": "Fault_Name",
        # keep raw strings for provenance/debugging
        "dip_raw": "Dip",
        "dip_dir_raw": "Dip_Direct",
        "slip_sense_raw": "Slip_Sense",
        "slip_rate_raw": "Slip_Rate",
        "ave_strike_raw": "Ave_Strike",
        "class": "Class",
        "location": "Location",
        "last_rupt": "Last_Rupt",
        "reference": "Reference",
    }

    traces = load_cfm_traces(file_path, skip_ids=skip_ids, include_ids=include_ids, id_column="fid")

    out_features = [
        {
            "geometry": feature["geometry"],
            "propz": _convert_properties(feature["properties"], conversion_dict),
            "properties": {},
            "type": "Feature",
        }
        for feature in traces
    ]

    for feature in out_features:
        props = feature["properties"]
        propz = feature["propz"]

        props["CFM_ID"] = propz["CFM_ID"]
        props["name"] = propz["name"]
        dip, is_vertical = _parse_dip(propz.get("dip_raw"))
        props["dip"] = dip
        props["dip_dir"] = _parse_dip_dir(propz.get("dip_dir_raw"), is_vertical)

        props["rake"] = _rake_from_slip_sense(propz.get("slip_sense_raw"))

        # optional numeric fields (keeps raw alongside)
        #props["strike"] = _parse_strike(props.get("ave_strike_raw"))
        #props["slip_rate_mm_yr"] = _parse_slip_rate_mm_yr(props.get("slip_rate_raw"))

        # keep compatibility with other loaders
        props.setdefault("lower_depth", None)
        props.setdefault("upper_depth", None)

        props["source"] = "NRCan"
        props["reference"] = propz["reference"]
        props["region"] = "ForearcIntraarc_BC"
        props["slip_sense"] = propz["slip_sense_raw"]
        props["fault_level"] = 1
        props["3D_model_constraints"] = "trace extended at constant dip"
        props["lineage"] = "unmodified"


        del feature["propz"]

    return out_features
