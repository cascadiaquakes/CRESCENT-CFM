import json
import os
import re

# File paths (relative to the scripts folder)
input_file = '../crescent_cfm_files/crescent_cfm_crustal_3d.geojson'
output_dir = '../crescent_cfm_files/hires_faults/'

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

print(f"📂 Loading full {input_file} (77MB)...")
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ Error: Cannot find {input_file}. Make sure you are running this from the 'scripts' folder.")
    exit(1)

features = data.get('features', [])
print(f"📊 Found {len(features)} faults. Splitting into individual files...")

def clean_filename(name):
    """Fallback cleaner if CFM_ID is entirely missing."""
    clean = re.sub(r'[^\w\s-]', '_', str(name))
    return clean.strip().replace(' ', '_')

saved_count = 0

for i, feat in enumerate(features):
    props = feat.get('properties', {})
    
    # 1. Strictly use CFM_ID for the filename
    fault_id = props.get('CFM_ID')
    
    # 2. Handle missing CFM_ID gracefully (just in case)
    if fault_id is not None:
        # Ensure it's a clean string (eg "1", "25")
        safe_id = str(fault_id).strip()
    else:
        # Fallback only if absolutely necessary
        fault_name = props.get('name', props.get('fault_name', f'fault_{i}'))
        safe_id = clean_filename(fault_name)
        print(f"  ⚠ Warning: Fault missing CFM_ID. Using fallback name: {safe_id}_hires.geojson")
        
    # Inject 'id' for viewer compatibility
    props['id'] = safe_id
        
    # 3. Create the single feature GeoJSON
    single_fault_geojson = {
        "type": "FeatureCollection",
        "features": [feat]
    }
    
    # 4. Save file as <CFM_ID>_hires.geojson (e.g 1_hires.geojson)
    output_filename = os.path.join(output_dir, f"{safe_id}_hires.geojson")
    
    with open(output_filename, 'w', encoding='utf-8') as out_f:
        json.dump(single_fault_geojson, out_f)
        
    saved_count += 1

print(f"\n✅ Success! Created {saved_count} individual high-res fault files in {output_dir}")