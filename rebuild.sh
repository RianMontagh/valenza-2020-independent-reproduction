#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PROJECT_ROOT="$PWD"
mkdir -p .runtime/cache .runtime/tmp .runtime/matplotlib .runtime/texmf-var .runtime/texmf-config .runtime/texmf-cache data/results report
export TMPDIR="$PROJECT_ROOT/.runtime/tmp"
export XDG_CACHE_HOME="$PROJECT_ROOT/.runtime/cache"
export MPLCONFIGDIR="$PROJECT_ROOT/.runtime/matplotlib"
export PIP_CACHE_DIR="$PROJECT_ROOT/.runtime/pip-cache"
export TEXMFVAR="$PROJECT_ROOT/.runtime/texmf-var"
export TEXMFCONFIG="$PROJECT_ROOT/.runtime/texmf-config"
export TEXMFCACHE="$PROJECT_ROOT/.runtime/texmf-cache"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-16}"
mode="${1:---offline}"
if [[ "$mode" != --offline && "$mode" != --download ]]; then
  echo 'Usage: ./rebuild.sh [--offline | --download]' >&2
  exit 2
fi
if [[ ! -x .runtime/py311/bin/python ]]; then
  python3.11 -m venv .runtime/py311
  .runtime/py311/bin/pip install -r requirements.txt
fi
PYTHON="$PROJECT_ROOT/.runtime/py311/bin/python"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 8
ctest --test-dir build --output-on-failure
build/avulsion selftest data/results/validation.csv
"$PYTHON" scripts/integration_checks.py
if [[ "$mode" == --download ]]; then
  "$PYTHON" scripts/acquire.py --config config/events.json --workers 12
  "$PYTHON" scripts/acquire.py --config config/extended.json --workers 12
  "$PYTHON" scripts/terrain.py
fi
"$PYTHON" scripts/verify_inputs.py
build/avulsion catalog config/sites.csv data/results
for site in B11 B12 V11 V15 B12_wide; do
  build/avulsion analyze "data/raw/$site" "data/derived/$site"
  if [[ -f "config/annotations/$site/polygons.csv" ]]; then
    build/avulsion measure "data/derived/$site" "config/annotations/$site/polygons.csv" "data/derived/$site/event"
  fi
done
build/avulsion statistics config/sites.csv config/channel_measurements.csv data/derived data/results
build/avulsion compare-domains data/derived/B12 data/derived/B12_wide data/results/domain_sensitivity.csv
"$PYTHON" scripts/real_checks.py
"$PYTHON" scripts/plot.py --figure all
for site in B11 B12 V11 V15; do
  "$PYTHON" scripts/inspect_images.py "$site" --years 1986,1991,1995,1996,1998,2000,2010,2017
done
"$PYTHON" scripts/inspect_images.py B12_wide --years 1995,2011,2013,2015,2017
"$PYTHON" scripts/report_data.py
"$PYTHON" scripts/pack_outputs.py
(
  cd report
  pdflatex -interaction=nonstopmode -halt-on-error report.tex
  pdflatex -interaction=nonstopmode -halt-on-error report.tex
)
"$PYTHON" scripts/manifest.py
echo "Rebuild completed: $PROJECT_ROOT/report/report.pdf"
