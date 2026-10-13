# Independent manual measurements

Coordinates in config/sites.csv are permitted identifiers, not measured
outcomes. The regional map can use those coordinates directly. Reproducing
Figures 3, 4 and S3 additionally requires the following independently derived
observations for each event:

1. Parent and event channel polygons, including exclusion of persistent
   ponds, unrelated flooding and channels. Review annual reflectance scenes
   before inspecting the resulting style ratio.
2. Separate initiation and completion dates. An unfinished event must remain
   unfinished. Do not choose dates to reproduce the published ratio.
3. Width near initiation, with pixel endpoints and representative cross
   sections preserved. Resolve bankfull channel belt versus water-only width
   explicitly. Landsat cannot reliably resolve subpixel widths.
4. An independently traced channel-belt centerline connecting the avulsion to
   an independently identified mountain front. Straight-line separation is
   not an acceptable substitution for along-channel distance.
5. An elevation profile along a documented reach. Regional visualization
   terrain resampled to kilometre scales must not be substituted for the
   paper's 5--10 km local channel-belt slope measurement.
6. Flow-thread counts at multiple cross sections, then classification as
   multithreaded, transitional or single-threaded. Do not import the
   authors' morphology labels or derive them from the desired ratio.

Annotations are CSV polygon vertices in output-grid pixel-edge coordinates,
with columns role,x_pixel,y_pixel. Pixel centers are tested for membership.
Role is parent, avulsion or exclude. A file years.txt in the same directory
contains parent_start parent_end event_start event_end. Each annotation must
also have a note identifying the imagery inspected, date, uncertainty,
and whether the observed feature exits the acquired domain.

The statistical command accepts config/channel_measurements.csv only after
these measurements have been documented. Missing rows stay missing. The
command emits a complete 63-site audit even when no relationships can be
calculated. It never estimates missing geometries from publication values.

The regression implementation uses ordinary least squares in log10 space
and the published D/w > 60 subset. The text calls this a best-fit line but
does not fully specify the regression convention; log-space OLS is an
explicit assumption. A fitted value is not emitted with fewer than three
usable observations or zero variance. Box summaries use linear-interpolated
quartiles and range whiskers, rather than the common 1.5-IQR default.
