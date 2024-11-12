# CRESCENT-CFM

**CRESCENT-CFM** is a repository developed to support the Community Fault Model ([CFM](https://cascadiaquakes.org/cfm/)) of the [CRESCENT project](https://cascadiaquakes.org/). This repository is designed to provide data and tools for researchers, scientists, and geophysicists working with CFM data.

## Features

**Data Files** 

The data files are all vector GIS files. They are located in the 
`crescent_cfm_files` folder. Additional scripts and resources within the 
repository are provided to aid in building and working with the CFM.

There are a number of files here, representing the CFM:
- `crescent_cfm_crustal_traces` This is the GIS file of crustal fault traces. 
  It is available in GeoJSON, GeoPackage, and KML formats.
- `crescent_cfm_crustal_3d` This GIS file has 3D representations of the crustal 
  faults. The 3D surfaces are triangular meshes.
- `casie21_plate_boundary.geojson` This is the Cascadia plate boundary from 
  Carbotte et al., 2024, represented as a triangular mesh. In this version, 
  each triangle is a separate GIS feature.
- `casie21_plate_boundary_multipart.geojson` This is the Cascadia plate 
  boundary from Carbotte et al., 2024, represented as a triangular mesh. In 
  this version, the entire surface is represented as a single multipart GIS 
  feature, which is optimized for many purposes, but cannot store information 
  element-wise.
- `slab2_cascadia_interface.geojson` This is the Cascadia plate boundary from 
  Slab2 (Hayes et al., 2018), represented as a triangular mesh. In this 
  version, each triangle is a separate GIS feature.
- `slab2_cascadia_interface_multipart.geojson` This is the Cascadia plate 
  boundary from Slab2 (Hayes et al., 2018), represented as a triangular mesh. 
  In this version, the entire surface is represented as a single multipart GIS 
  feature, which is optimized for many purposes, but cannot store information 
  element-wise.
- `mcrory_2012_cascadia_interface.geojson` This is the Cascadia plate boundary 
  from McRory et al., 2012. This is created as a mesh from the contours 
  provided by McRory, so it is somewhat lower resolution than the slab 
  geometries created from the Casie21 and Slab2 projects. It is a multipart GIS 
  feature.
- `cascadia_subduction_interface_temp.geojson` This is a mesh from Graham et 
  al., 2018, created from data of uncertain provenance.

The onshore (crustal) faults are taken from two sources: The USGS National
Seismic Hazard Map (NSHM 23) project (Hatem et al., 2022), and in-progress
collaborative research by Natural Resources Canada and the GEM Foundation
(Hobbs et al., *in prep*; Styron et al.,, *in prep*).

Hatem, A. E., Collett, C. M., Briggs, R. W., Gold, R. D., Angster, S. J., Field, E. H., & Powers, P. M. (2022). Simplifying complex fault data for systems-level analysis: Earthquake geology inputs for US NSHM 2023. Scientific data, 9(1), 506.

**Fault Model Visualization**  
A 3D mapping web interface for visualizing fault surfaces and traces is accessible through the [CFM web interface](https://cfm.cascadiaquakes.org/).

## Contact and Support

For questions or assistance with the CFM or this repository, please refer to 
the process below to ensure prompt support:

1. (For general questions, not technical issues): Send an email to 
   [crescentcfm@gmail.com](mailto:crescentcfm@gmail.com).

2. Go to the **Issues Page**  Visit the repository’s `Issues` section to log 
   any inquiries or support requests.

3. **Create a New Issue**  On the `Issues` page, click `New issue` to start a 
   new submission or request.

4. **Provide Relevant Details**  When creating an issue, please include:

   - A brief description of your question or problem.
   - Links or attachments for any relevant files (e.g., images, data).

5. **Submit**  After completing the details, submit your issue. Our team will 
   review it and respond as soon as possible.

We're here to help with any questions or requests related to the CRESCENT-CFM!
