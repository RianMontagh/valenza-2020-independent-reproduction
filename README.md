# Independent river-avulsion analysis

This is a **partial independent reproduction**, not a recovered 63-event
result, of Valenza et al. (2020), *Downstream changes in river avulsion style
are related to channel morphology*, [doi:10.1038/s41467-020-15859-9](https://doi.org/10.1038/s41467-020-15859-9).

Read the [compiled report](report/report.pdf), [LaTeX source](report/report.tex),
and [panel-by-panel record](data/results/panel_record.csv). The report distinguishes
generated observations from missing results. No manuscript image is substituted
for an independently calculated result.

The original C++17 implementation computes quality screening, reflectance
calibration, annual medians, tasseled-cap transforms, percentile signatures,
polygon-restricted duration and area, style ratios, group summaries and
log-space regression. Original Python scripts acquire agency imagery, reproject
it, plot saved C++ output, and assemble the report. This paper describes an
observational analysis, not a forward dynamical model of avulsion.

## Scientific outcome

- Figure 1a–d's site distributions are independently generated from all 63
  user-permitted location records and independent terrain. This reproduces
  the geographic content, not identical cartography or independently discovered
  sites. The locator is partial.
- Independent annual Landsat observations cover B11, B12, V11 and V15. An
  additional larger B12 domain investigates its downstream context.
- B12 has a partial central-reach footprint for 2010–2017, with an independent
  mask and 1995 parent observation. Figure 2a,b and the four lower slots of 2c
  are partial spectral-method attempts; the published parent/new-channel
  relationship and spatial progression have not been verified. High-resolution
  validation remains absent. See the [post hoc comparison](docs/published-comparison.md).
- V11 has a partial, manually bounded 1996–1998 footprint and a separate
  1986 parent observation. Its area ratio is a diagnostic with unequal windows
  and incomplete spatial coverage, not the paper's full-event style ratio.
- Figure 5a,b,d,e and Supplementary Figure 1a–d are partial attempts.
- Figure 2c (all four upper slots), Figure 3a,b, Figure 4,
  Figure 5c, Supplementary Figure 2a,b,c, and Supplementary Figure 3a,b are
  not reproduced. See the ledger for each prerequisite and attempted operation.
- No complete independent event-plus-channel-geometry record exists for
  Figures 3, 4 or S3. The 59 other sites were not locally acquired in this
  attempt. Missing measurements are not replaced by authors' outcomes,
  fabricated channels, digitized points, or synthetic validation fixtures.

## Independence

No authors' code, plotting scripts, outputs, processed images or masks are
used. Only site IDs and coordinates are retained under the user's explicit
metadata exception. An optional extractor reads exactly the location columns;
it is not part of normal rebuilding. No author-provided event dates are inputs.
The assistant had seen the measurement workbook during an earlier feasibility
discussion; [the provenance policy](docs/provenance-policy.md) discloses that
prior exposure. This is not a blinded experiment.

Agency Landsat Collection 2 Level 2 observations are obtained independently
through the Planetary Computer. [Methods and departures](docs/methods.md)
document differences from the paper's retired Collection 1 inputs, cloud
screen, incompletely specified alignment, mixed-sensor treatment, percentile
domains, masks, and observation windows. [Data attribution](docs/data-attribution.md)
identifies provider credits. The user-designated guidance files are under
`guidance/`; no other code from that repository was consulted.

## Full rebuild

Place this checkout under one of `/data/data0` through `/data/data7`. All
commands below run **from its root**. No project files, virtual environments,
temporary files, or TeX/Matplotlib caches need to be written under a home
directory. The verified workspace is
`/data/data2/UW2UCSD_Whidbey_c2chien/rmontagh_valenza2020_independent`.

System requirements: C++17 compiler (tested GCC 8.5), CMake, Python 3.11 with
venv, and pdfLaTeX with `geometry`, `lmodern`, `amsmath`, `graphicx`, `booktabs`,
`longtable`, `xcolor`, `hyperref`, and `microtype`. Python dependencies are
pinned in `requirements.txt`. The script creates `.runtime/py311` if absent
and installs them there; package downloads therefore require network access
on a fresh checkout. `--offline` means the **scientific input acquisition**
is skipped, not that an absent Python environment can be created without
package downloads.

```bash
python3.11 scripts/run_rebuild.py --download
```

This runs `bash rebuild.sh --download`, saves its actual log and outcome,
and recompiles the report with the completed execution record. It:

1. Compiles C++, runs limiting-case and integration checks.
2. Downloads independently sourced imagery using the frozen unsigned catalogs
   and downloads regional terrain. Existing raw arrays are reused by size;
   provenance hashes permit checking them. No credentials are required for
   these provider downloads; short-lived provider tokens stay in memory.
3. Recomputes all saved annual rasters, detections, and the available B12/V11
   partial masks and measurements.
4. Audits all 63 sites, leaving missing statistical records empty.
5. Runs real-data consistency checks, creates all figure attempts and ledger.
6. Compresses and round-trip checks every generated raster array.
7. Compiles `report/report.pdf`, records execution outcome, and hashes artifacts.

Allow approximately 100 GB free disk space for inputs, generated arrays,
archives, the Python environment, and working files. Network acquisition is
the slowest step; the provider may be temporarily unavailable. The four small
domains select 4,097 scene-domain cutouts; the extended B12 domain adds 720.
Some scenes cover more than one domain, so these are not unique scene counts.
The archive is frozen; refreshing it is a deliberate change of inputs.

With the raw agency arrays already cached:

```bash
python3.11 scripts/run_rebuild.py --offline
```

The wrapper records `data/results/rebuild.log`, `rebuild_outcome.json`, and
`report_finalize.log`. A zero exit code denotes a successful computation and
report build. It does **not** denote successful reproduction of every panel.

For individual operations, after building:

```bash
build/avulsion analyze data/raw/V11 data/derived/V11
build/avulsion measure data/derived/V11 config/annotations/V11/polygons.csv data/derived/V11/event
build/avulsion statistics config/sites.csv config/channel_measurements.csv data/derived data/results
.runtime/py311/bin/python scripts/plot.py --figure fig5
```

The panel ledger gives commands for every panel. Commands requiring unavailable
annotations identify unfinished scientific work; they are not invoked by the
successful build. Independent channel measurements follow
[measurement-protocol.md](docs/measurement-protocol.md).

## Generated-data archive and figure-only rebuild

`data/saved_outputs/` contains losslessly compressed NumPy archives of **C++
outputs**, split by array to keep files below GitHub's 100 MB limit. Raw provider
scene cutouts are excluded from version control; their frozen URLs, IDs and
hashes are included. Grid metadata and annual/measurement CSVs remain ordinary
repository files. All raster types are little endian: `.f32` is float32,
`.u16` is unsigned 16-bit, `.u8` is unsigned 8-bit. TCT and RGB files have three
band-major layers; other rasters have one row-major layer. The grid describes
width, height, x/y pixel increments, upper-left coordinates and EPSG code.

To regenerate figures without retrieving raw observations, restore the saved
arrays and run the original plotting and reporting scripts:

```bash
export MPLCONFIGDIR="$PWD/.runtime/matplotlib"
export TMPDIR="$PWD/.runtime/tmp"
export XDG_CACHE_HOME="$PWD/.runtime/cache"
export PYTHONDONTWRITEBYTECODE=1
export TEXMFVAR="$PWD/.runtime/texmf-var"
export TEXMFCONFIG="$PWD/.runtime/texmf-config"
export TEXMFCACHE="$PWD/.runtime/texmf-cache"
mkdir -p "$MPLCONFIGDIR" "$TMPDIR" "$XDG_CACHE_HOME" "$TEXMFVAR" "$TEXMFCONFIG" "$TEXMFCACHE"
.runtime/py311/bin/python scripts/pack_outputs.py --unpack
.runtime/py311/bin/python scripts/plot.py --figure all
.runtime/py311/bin/python scripts/report_data.py
cd report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

This shortcut rebuilds plots from archived generated arrays. It is explicitly
different from reprocessing agency observations. If the local Python
environment is absent, run the setup at the beginning of `rebuild.sh` first,
with its cache variables kept under the project.

## Validation and limitations

Checks cover calibration, cloud exclusion, median/quantile conventions,
constant and missing scenes, linear transforms, pixel area, temporal union,
ratio limits, and a known analytical regression. Real-data checks compare
annual masks with cumulative counts and enforce coverage and threshold bounds.
The full procedure records all results. Synthetic checks never become study
observations or manuscript figures.

Independent event mapping, representative cross sections, local DEM profiles,
mountain-front traces, and commercial high-resolution validation remain the
principal unfinished work. The code does not turn missing observations into
measured values. A later experiment using the researchers' processed images
or masks has not been performed.
