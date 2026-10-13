# Written specification and departures

Valenza et al. (2020), doi:10.1038/s41467-020-15859-9, Methods describes an
observational remote-sensing workflow, not a forward dynamical model. No
governing equation predicts river avulsion from arbitrary initial conditions.
Its site selection, channel geometry, and time windows require observations
and visual interpretation.

## Equations and units

For each sensor, annual band reflectance is the median of clear valid
observations at each 30 m pixel. Brightness, greenness, and wetness are
T_j = sum_b C_jb rho_b. Coefficients C are from Supplementary Table 2, in
physical-band order blue, green, red, near infrared, SWIR1, SWIR2. Landsat 8
physical bands are 2,3,4,5,6,7; the table's reused Landsat 5 band labels are
interpreted as a labeling error, not a reason to include OLI's coastal band.

For each annual composite across the analysis domain,
B = (TCB > Q_0.90(TCB)) and (TCG < Q_0.50(TCG)),
W = (TCW > Q_0.75(TCW)) and (TCG < Q_0.50(TCG)).
Inequalities are strict. Quantiles use linear interpolation at index (n-1)p,
after removing missing values. This convention is specified here because the
written paper does not prescribe a quantile interpolation convention.

An event fingerprint is F(x)=sum_{y=y_start}^{y_end} I_y(x), inside an
independently drawn event polygon and outside identified pre-existing water
or unrelated disturbances. N_A counts pixels with F>0. Parent-channel counts
N_P are calculated identically in a separately drawn parent polygon and
time window. S_R=N_A/N_P is dimensionless. A=N*|dx*dy| has units m^2. No S_R
is emitted when the parent count is zero. Both spectral signatures are kept;
the smaller avulsion area selects the signature, with brightness selected
in an exact tie. Selecting by smallest ratio instead would be a different
rule and is not silently substituted.

Normalized downstream distance is D/w with both lengths in metres. Slope is
elevation difference / along-channel distance. Width and flow-thread count
require cross sections; mountain-front position requires an independently
documented geomorphic interpretation. They cannot be inferred from the style
ratio itself. Correlations and morphology distributions require independently
measured site records, not the authors' tabulated outcomes.

## Specified parameters

The paper's archive period is 1986--2017, spatial sampling is 30 m, and missions
are Landsat 5, 7, 8. Its cloud-score cutoff is 0.20. Annual medians are
calculated before the tasseled-cap transform. Published thresholds are 0.90,
0.50,0.75. Parent and event windows should be as short and as comparable as
the observations allow. Each retained year needs a coverage audit.

## Explicit adaptations requiring partial status

1. USGS Collection 2 replaces the retired Collection 1 archive. DN calibration
   is rho=0.0000275 DN-0.2; zero DN is missing. No reflectance clipping is done.
2. The available input is surface reflectance; the paper invokes GEE simple
   cloud score but does not fully specify how that operation is applied to
   these inputs. We use the provider's documented QA_PIXEL cloud, shadow,
   cirrus (OLI), snow, fill and dilated-cloud bits, and reject nonzero
   QA_RADSAT. This is an explicit alternate cloud screen, not the original
   20-percent rule. Its effect must not be hidden.
3. For mixed-sensor years, use the sensor with most clear pixel-observations
   over the acquired domain, with larger sensor number breaking ties. The
   initial reconnaissance used scene count; inspection showed this could
   favor images whose footprints missed most of the site. All final results
   use clear pixel-observation count. This avoids mixing sensor coefficient
   systems. It differs from an unspecified radiometric alignment procedure.
4. Provider-calibrated reflectances are reprojected by nearest neighbour to
   a fixed local UTM grid. No extra radiometric alignment is fitted, because
   the written alignment rule is incomplete.
5. The initial unused geographic configuration specified 90 m. All acquired
   imagery uses 30 m sampling. Reconnaissance capped scenes at two or four
   per year; final analyses use every scene in the pinned provider catalog.
6. Percentile domain is the configured geographic rectangle. Domain size can
   affect thresholds. Sensitivity to domain and cloud screening should be
   kept distinct from agreement with the paper.
7. Missing years remain missing. No temporal interpolation, generated river
   geometry, or invented values fill observational gaps.

Sources: paper Methods; Supplementary Table 2; USGS Collection 2 surface
reflectance and quality-assessment documentation; Google Earth Engine
Collection 1 removal notice. URLs are recorded in the report bibliography.

## Catalog and domain-comparison diagnostics

The catalog preserves the permitted latitude and longitude pairs. Its optional
Cartesian columns use a sphere of radius 6,371,008.8 m, with
x=R*cos(latitude)*cos(longitude), y=R*cos(latitude)*sin(longitude), and
z=R*sin(latitude). These columns do not estimate along-channel distance and
are not used by the map's longitude/latitude axes.

The nested-domain diagnostic compares physical pixels only when the projected
grids share EPSG code, 30 m sampling, integer origin offsets, and complete
nesting. On jointly valid pixels it reports intersection/union of binary
detections, agreement including background, and mean absolute RGB difference
in reflectance units. Empty foreground unions give undefined overlap. This
is an internal sensitivity check, not comparison with a published mask.
