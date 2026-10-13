# Independence and scope

This project starts at USGS Level-2 Landsat observations obtained from an
independent public provider. Provider atmospheric correction is accepted, as
it is in the paper. No Valenza repository, author implementation, author
processed imagery, masks, spreadsheet measurements, plotted coordinates, or
figure files are inputs. No published plot is digitized.

Before this project was requested, the assistant inspected the paper's
supplementary spreadsheet during a feasibility discussion. That prior exposure
cannot be undone. None of those measurements is copied into this project's
inputs. This is an independent implementation with disclosed prior exposure,
not a claim of a blinded clean-room experiment.

Published written methods and transformation coefficients are scientific
specifications. Published outcome values may be cited only as comparison
targets and must not enter analysis or data-selection code. The user subsequently explicitly permitted site-location metadata only.
The 63 identifiers and geographic coordinates are projected from the published
spreadsheet into config/sites.csv; no other spreadsheet columns are retained.
Initial geographic reconnaissance used separately obtained OpenStreetMap
river names. Reconnaissance domains are not author masks.

Acquisition scripts save provider scene IDs, source URLs without access tokens,
hashes of downloaded arrays, geographic grids, failures, and scene-selection
rules. Short-lived provider access tokens never belong in the repository.

All intermediate files, dependencies, caches, and reports stay within this
project under /data/data2. GitHub authentication, if supplied externally, is
read but not copied into tracked files.

The requested external AGENTS.md and academic guide are saved verbatim under
guidance/. Only these two files were fetched from the guidance repository.
