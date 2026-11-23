#This script serves two functions. First, it attributes fault properties from the metadata table to the corresponding fault features in the CFM GeoJSON. Then it sorts the faults in order of increasing CFM_ID number.

import pandas as pd
import geopandas as gpd
import json

def add_metadata_to_geojson(input_geojson_path, metadata_df, output_geojson_path, cols_to_add, join_key_csv='CFM ID', join_key_geojson='CFM_ID'):
    """
    Add metadata from a CSV DataFrame to a GeoJSON file by joining on a key column.

    Parameters
    ----------
    input_geojson_path : str
        Path to the GeoJSON file to update
    metadata_df : pd.DataFrame
        DataFrame containing metadata to add
    output_geojson_path : str
        Path to write attributed GeoJSON file to
    cols_to_add : dict
        Dictionary mapping CSV column names (keys) to GeoJSON column names (values)
    join_key_csv : str
        Column name in the CSV to use for joining (default: 'NSHM ID #')
    join_key_geojson : str
        Column name in the GeoJSON to use for joining (default: 'nshm_id')

    Returns
    -------
    Attributed GeoJSON file
    """
    # Read the input GeoJSON file
    gdf = gpd.read_file(input_geojson_path)

    # Prepare the CSV data for joining
    mdf = metadata_df.copy()

    # Convert join key to float to match geojson type
    #mdf[join_key_csv] = pd.to_numeric(mdf[join_key_csv], errors='coerce')
    
    # Remove rows from CSV where the join key is null/NaN
    mdf = mdf[mdf[join_key_csv].notna()].copy()
   
    # Select only the columns we need from the CSV, plus the join key
    csv_columns_to_keep = [join_key_csv] + [k for k in cols_to_add.keys() if k != join_key_csv]
    mdf_subset = mdf[csv_columns_to_keep].copy()

    # Rename columns in the CSV subset according to cols_to_add mapping
    rename_dict = cols_to_add.copy()
    mdf_subset.rename(columns=rename_dict, inplace=True)

    # Get the geojson name for the join key
    join_key_geojson_target = cols_to_add.get(join_key_csv, join_key_csv)

    # Split the geodataframe into two parts:
    # 1. Rows with valid join key (can be merged)
    # 2. Rows without valid join key (keep as-is)
    gdf_with_key = gdf[gdf[join_key_geojson].notna()].copy()
    gdf_without_key = gdf[gdf[join_key_geojson].isna()].copy()

    # Perform left join only on rows with valid join key
    gdf_merged = gdf_with_key.merge(
        mdf_subset,
        left_on=join_key_geojson,
        right_on=join_key_geojson_target,
        how='left',
        suffixes=('', '_csv')
    )

    # For each column to add, use the CSV value if available, otherwise keep the original
    for csv_col, geojson_col in cols_to_add.items():
        if csv_col == join_key_csv:
            # Skip the join key
            continue

        csv_version = geojson_col + '_csv' if geojson_col + '_csv' in gdf_merged.columns else None

        if csv_version and geojson_col in gdf_merged.columns:
            # Update existing column: use CSV value where not null, otherwise keep original
            mask = gdf_merged[csv_version].notna()
            gdf_merged.loc[mask, geojson_col] = gdf_merged.loc[mask, csv_version]
            # Drop the temporary _csv column
            gdf_merged.drop(columns=[csv_version], inplace=True)
        elif csv_version:
            # Column doesn't exist yet, rename _csv version to final name
            gdf_merged.rename(columns={csv_version: geojson_col}, inplace=True)

    # Drop the duplicate join key column if it was added
    if join_key_geojson_target in gdf_merged.columns and join_key_geojson_target != join_key_geojson:
        gdf_merged.drop(columns=[join_key_geojson_target], inplace=True)

    # Combine the merged rows with the non-merged rows
    if len(gdf_without_key) > 0:
        # Add the new columns to rows without join key (fill with None/NaN)
        for csv_col, geojson_col in cols_to_add.items():
            if csv_col == join_key_csv:
                continue
            if geojson_col not in gdf_without_key.columns and geojson_col in gdf_merged.columns:
                gdf_without_key[geojson_col] = None

        gdf_final = pd.concat([gdf_merged, gdf_without_key], ignore_index=True)
    else:
        gdf_final = gdf_merged

    # Ensure the geometry column is preserved correctly
    gdf_final = gpd.GeoDataFrame(gdf_final, geometry='geometry', crs=gdf.crs)

    # Save to the output geojson output file
    gdf_final.to_file(output_geojson_path, driver = 'GeoJSON')
    print(f"Successfully attributed {input_geojson_path}")
    print(f"  Rows with join key: {len(gdf_with_key)}")
    print(f"  Rows without join key: {len(gdf_without_key)}")
    print(f"Updated columns: {', '.join([v for v in cols_to_add.values() if v != join_key_geojson_target])}")


input_geojson_path = "../crescent_cfm_files/crescent_cfm_crustal_3d.geojson"
metadata_file ="../misc_data/metadata/cfm_metadata.csv"
output_geojson_path = "../crescent_cfm_files/crescent_cfm_crustal_3d_attributed.geojson"
mdf = pd.read_csv(metadata_file)
cols_to_add = {
    'Fault Name' : 'name',
    'CFM ID': 'CFM_ID',
    'Region': "region",
    'Primary State/Province': "primary_state/province",
    'Secondary State/Province': "secondary_state/province",
    'Average Dip (degrees)': "avg_dip",
    'Dip Direction': 'dip_dir',
    'Rake (degrees)': 'rake',
    'Slip Sense': "slip_sense",
    'Fault Level': "fault_level",
    'NSHM23 sliprates (mm/yr)': "NSHM23_sliprates",
    'QFFDAgeCatBin': 'QFFDAgeCatBin',
    'QFFDAgeCat': 'QFFDAgeBin',
    'UpDepth (km)': 'upper_depth',
    'Upper Depth Constraint' : 'upper_depth_constraint',
    'LowDepth (km)': 'lower_depth',
    'Lower Depth Constraint' : 'lower_depth_constraint',
    '3D Model Constraints': '3D_model_constraints',
    'Reference': 'reference',
    'NSHM23 ID #': 'nshm23_id',
    'Lineage***': 'lineage',
    'USGS QFFD #': 'usgs_qffd_#',
    'Comments': 'comments',
}
    

add_metadata_to_geojson(input_geojson_path, mdf, output_geojson_path, cols_to_add, join_key_csv='Fault Name', join_key_geojson='name')

##Next sort
#Sort the faults in the attributed GeoJSON file so that the faults are in order accroding to CFM_ID
with open(output_geojson_path, 'r') as json_file:
    data = json.load(json_file)
    
def get_ref(feature):
    return int(feature['properties']['CFM_ID'])

data['features'].sort(key=get_ref)

with open(output_geojson_path, 'w') as json_file:
    json.dump(data, json_file)









