import pandas as pd
import geopandas as gpd


def add_metadata_to_geojson(geojson_path, metadata_df, cols_to_add, join_key_csv='NSHM ID #', join_key_geojson='nshm_id'):
    """
    Add metadata from a CSV DataFrame to a GeoJSON file by joining on a key column.

    Parameters
    ----------
    geojson_path : str
        Path to the GeoJSON file to update
    metadata_df : pd.DataFrame
        DataFrame containing metadata to add
    cols_to_add : dict
        Dictionary mapping CSV column names (keys) to GeoJSON column names (values)
    join_key_csv : str
        Column name in the CSV to use for joining (default: 'NSHM ID #')
    join_key_geojson : str
        Column name in the GeoJSON to use for joining (default: 'nshm_id')

    Returns
    -------
    None
        Saves the updated GeoJSON back to the original file path
    """
    # Read the GeoJSON file
    gdf = gpd.read_file(geojson_path)

    # Prepare the CSV data for joining
    mdf = metadata_df.copy()

    # Convert join key to float to match geojson type
    mdf[join_key_csv] = pd.to_numeric(mdf[join_key_csv], errors='coerce')

    # Select only the columns we need from the CSV, plus the join key
    csv_columns_to_keep = [join_key_csv] + [k for k in cols_to_add.keys() if k != join_key_csv]
    mdf_subset = mdf[csv_columns_to_keep].copy()

    # Rename columns in the CSV subset according to cols_to_add mapping
    rename_dict = cols_to_add.copy()
    mdf_subset.rename(columns=rename_dict, inplace=True)

    # Get the geojson name for the join key
    join_key_geojson_target = cols_to_add.get(join_key_csv, join_key_csv)

    # Perform left join on the join key to keep all geojson features
    gdf_merged = gdf.merge(
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

    # Save back to the original geojson file
    gdf_merged.to_file(geojson_path, driver='GeoJSON')

    print(f"Successfully updated {geojson_path}")
    print(f"Updated columns: {', '.join([v for v in cols_to_add.values() if v != join_key_geojson_target])}")


if __name__ == "__main__":
    # File paths
    fault_geojson = "../crescent_cfm_files/crescent_cfm_crustal_traces.geojson"
    fault_3d_geojson = "../crescent_cfm_files/crescent_cfm_crustal_3d.geojson"
    metadata_file = "../misc_data/metadata/cfm_metadata.csv"

    # Column mapping
    cols_to_add = {
        #'CFM ID': 'CFM_ID',
        'Region': "region",
        'Primary State/Province': "primary_state/province",
        'Secondary State/Country': "secondary_state/province",
        'Slip sense': "slip_sense",
        'Fault level': "fault_level",
        'NSHM sliprates (MedWgtd)': "NSHM sliprates (MedWgtd)",
        'QfaultsAgeCat': 'QfaultsAgeCat',
        'QfaultsAgeCat.1': 'QfaultsAgeCat.1',
        'Reference**': 'reference',
        '3D Model Constraints': '3D_model_constraints',
        #'NSHM ID #': 'NSHM_ID',
        'Lineage***': 'lineage',
        'Comments': 'comments',
    }

    # Load the metadata CSV once
    mdf = pd.read_csv(metadata_file)

    # Apply to the traces geojson file
    add_metadata_to_geojson(
        fault_geojson,
        mdf,
        cols_to_add,
        join_key_csv='NSHM ID #',
        join_key_geojson='nshm_id'
    )


    # Apply to the ed geojson file
    add_metadata_to_geojson(
        fault_3d_geojson,
        mdf,
        cols_to_add,
        join_key_csv='NSHM ID #',
        join_key_geojson='nshm_id'
    )