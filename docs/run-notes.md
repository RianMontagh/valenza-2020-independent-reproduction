# Execution notes

The final documented run invokes `python3.11 scripts/run_rebuild.py --download`.
The independent agency cutouts had already been acquired when this verification
run began. Download mode reused that cache, rewrote the frozen provenance,
checked every input hash, and recalculated the analysis, figures and PDF.
It is not a claim to have tested a second fresh network download of every byte.
The original acquisitions completed for all 4,817 selected scene-domain cutouts
with no remaining failures. One long B12 acquisition process ended with signal
143 before completing; rerunning acquisition reused completed files and fetched
the remaining scenes. No scene was silently replaced or temporally filled.

An initial metadata extractor encountered a repeated site label outside the
location rows. It was corrected to require populated A/B/C location cells and
exactly 63 records before writing. Only these permitted columns were retained.
The first raster read exposed Windows CSV line endings; the C++ parser now
removes the trailing carriage return. The end-to-end checks use actual CSV
writer output and exercise that path.

Early scene-capped reconnaissance missed parts of domains and retained scan
gaps. Final acquisition includes every selected catalog scene. Mixed-sensor
selection was changed from scene count to clear pixel-observation count before
the final analysis. Final results do not use the preliminary annual outputs.

A preliminary LaTeX invocation from the repository root failed to resolve
relative figure paths. The documented procedure compiles from `report/` and
completed a preliminary 25-page PDF. The final run regenerates the report with
updated measurements, comparison notes, and execution outcome. Its actual
exit status and duration are in `data/results/rebuild_outcome.json`; this file
is authoritative if a later run differs.

The recorded end-to-end run finished with exit code 0 in 1,063.72 seconds.
The final typography review disabled typewriter-font ligatures so copying
double-hyphen CLI options from the PDF preserves the command spelling. The
report was then compiled twice again; no numerical input, analysis, or plotted
data changed in this final formatting correction.

Post hoc inspection of published Figures 2 and 5 informed only comparison
text. It did not change independent polygons, observation windows, percentile
thresholds, or scene selection. The temporary reference images were removed
and were never placed in version control or used by a plotting script.
