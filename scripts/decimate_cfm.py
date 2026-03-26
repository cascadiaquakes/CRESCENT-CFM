"""
CFM 3D Fault Surface Decimation Script
Reduces triangle count in GeoJSON fault surfaces for web viewer performance using Open3D.
Includes special boundary-preservation logic for offshore faults and auto-injects viewer IDs.
"""

import json
import argparse
import numpy as np
import open3d as o3d

def triangles_to_mesh(polygons):
    """Convert GeoJSON MultiPolygon triangles to welded numpy arrays."""
    vertices = []
    faces = []
    vertex_map = {}
    
    for poly in polygons:
        ring = poly[0]  # outer ring only
        if len(ring) < 4:
            continue
        
        face_indices = []
        for pt in ring[:3]:  # first 3 points (triangle)
            # Rounding to 5 decimal places (~1.1 meters) ensures the vertices actually weld together
            key = (round(pt[0], 5), round(pt[1], 5), round(pt[2], 5))
            if key not in vertex_map:
                vertex_map[key] = len(vertices)
                vertices.append([pt[0], pt[1], pt[2]])
            face_indices.append(vertex_map[key])
        
        # Only add valid triangles
        if len(face_indices) == 3 and len(set(face_indices)) == 3:
            faces.append(face_indices)
    
    if not vertices or not faces:
        return None, None
    
    return np.array(vertices), np.array(faces)

def mesh_to_multipolygon(vertices, faces):
    """Convert vertices and faces back to GeoJSON MultiPolygon of triangles."""
    polygons = []
    for face in faces:
        triangle = []
        for vi in face:
            triangle.append([
                round(float(vertices[vi][0]), 5),
                round(float(vertices[vi][1]), 5),
                round(float(vertices[vi][2]), 5)
            ])
        triangle.append(triangle[0])  # close the ring
        polygons.append([triangle])
    return polygons

def decimate_feature(feature, ratio):
    """Decimate a single fault feature's mesh using Open3D."""
    geom = feature['geometry']
    
    if geom['type'] != 'MultiPolygon':
        return feature
    
    original_count = len(geom['coordinates'])
    
    if original_count < 10:
        return feature
    
    verts, faces = triangles_to_mesh(geom['coordinates'])
    if verts is None:
        return feature
    
    target_faces = max(4, int(len(faces) * ratio))
    name = feature['properties'].get('name', feature['properties'].get('CFM_ID', 'unknown'))
    
    try:
        # Build Open3D Mesh
        o3d_mesh = o3d.geometry.TriangleMesh()
        o3d_mesh.vertices = o3d.utility.Vector3dVector(verts)
        o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
        
        # Decimate
        decimated = o3d_mesh.simplify_quadric_decimation(target_number_of_triangles=target_faces)
        
        new_faces = np.asarray(decimated.triangles)
        new_verts = np.asarray(decimated.vertices)
        
        if len(new_faces) == 0:
            print(f"  ⚠ {name}: Decimation failed (0 faces left), keeping original")
            return feature
        
        new_coords = mesh_to_multipolygon(new_verts, new_faces)
        
        new_feature = {
            'type': 'Feature',
            # Copy properties so we can safely modify them later
            'properties': dict(feature['properties']),
            'geometry': {
                'type': 'MultiPolygon',
                'coordinates': new_coords
            }
        }
        
        print(f"  ✅ {name}: {original_count} → {len(new_coords)} triangles")
        return new_feature
        
    except Exception as e:
        print(f"  ⚠ {name}: decimation error ({e}), keeping original")
        return feature

def main():
    parser = argparse.ArgumentParser(description='Decimate CFM 3D fault surfaces')
    parser.add_argument('--input', required=True, help='Input GeoJSON file')
    parser.add_argument('--output', required=True, help='Output GeoJSON file')
    parser.add_argument('--ratio', type=float, default=0.1, 
                        help='Base fraction of triangles to keep for onshore faults (default: 0.1 = 10%)')
    args = parser.parse_args()
    
    print(f"📂 Loading {args.input}...")
    with open(args.input) as f:
        data = json.load(f)
    
    if 'crs' in data:
        del data['crs']
    
    features = data['features']
    print(f"📊 {len(features)} faults, base onshore target ratio: {args.ratio}")
    
    total_original = 0
    total_decimated = 0
    decimated_features = []
    
    for i, feat in enumerate(features):
        original_count = len(feat['geometry'].get('coordinates', []))
        total_original += original_count
        
        # Dynamic Ratio Logic: Increase ratio for offshore faults to preserve boundaries
        region = feat.get('properties', {}).get('region', '')
        
        if 'offshore' in region.lower():
            # Give offshore faults 3x the normal ratio, but never let it exceed 50%
            feat_ratio = min(args.ratio * 3, 0.5)
        else:
            feat_ratio = args.ratio
            
        new_feat = decimate_feature(feat, feat_ratio)
        decimated_features.append(new_feat)
        
        new_count = len(new_feat['geometry'].get('coordinates', []))
        total_decimated += new_count
    
    # --- Inject the 'id' property mirroring 'CFM_ID' for viewer compatibility ---
    for feat in decimated_features:
        feat['properties']['id'] = feat['properties'].get('CFM_ID', '')

    output_data = {
        'type': 'FeatureCollection',
        'features': decimated_features
    }
    
    print(f"\n📊 Total: {total_original} → {total_decimated} triangles ({total_decimated/total_original*100:.1f}%)")
    
    print(f"💾 Writing {args.output}...")
    with open(args.output, 'w') as f:
        json.dump(output_data, f, separators=(',', ':'))
    
    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"✅ Done! Output: {size_mb:.1f} MB")

if __name__ == '__main__':
    main()