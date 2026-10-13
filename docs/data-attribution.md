# Data and written specifications

Landsat Collection 2 Level 2 surface reflectance and quality bands are supplied
by the U.S. Geological Survey, retrieved independently through Microsoft's
Planetary Computer. This project's derived imagery is not an official USGS
product. Agency atmospheric correction precedes our computation.

The regional elevation context is resampled from public Terrain Tiles hosted
on AWS (the Mapzen terrain project). Global SRTM and GMTED2010 data are courtesy
of the U.S. Geological Survey. Global ETOPO1 data are from NOAA / NESDIS / NCEI.
The zoom-7 tiles combine sources; this project does not assert a per-pixel
source attribution or use the regional context as a local river slope.

Provider attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
Dataset: https://registry.opendata.aws/terrain-tiles/

The only author-derived data retained are the user-permitted 63 site IDs and
coordinates, attributed to Valenza et al. (2020), Nature Communications 11,
2116, doi:10.1038/s41467-020-15859-9, supplementary information. The written
paper is licensed CC BY 4.0. No published image is included in this repository.

The two guidance files are supplied by Brad Lipovsky at the user-designated
vdv-damage repository. They are retained for provenance; no model or plotting
code from that repository has been consulted.
