# Calibration elasticity benchmark review

Status: open; author/domain interpretation pending. This is a repository issue record,
not a published GitHub issue.

The original diagnostic values (crackers approximately -3.16, tissue approximately
-3.85) are preserved in `diagnostics.beta_reference_v1_0`. Mean-price recalibration
necessarily changes `beta_reference = beta * p_bar`; current values are reported
without truncation or exclusion. These descriptive observational slopes do not
replace the imposed simulation elasticity.

Code investigation completed:

- Unit price is movement `price / qty`, including promotion weeks. Whether the
  category's retail bundle is the intended economic unit requires domain review.
- Demand and prices use NumPy natural logarithms; no log-base conversion is applied.
- Promotion is any nonblank movement `sale` code. Mapping individual sale codes to
  the chapter's promotion definition still requires source-codebook review.
- The competing index is the equal-weighted weekly mean of UPC-centered log unit
  prices for eligible nonfocal UPCs. It is not volume weighted.
- The regression coefficient on `price - p_bar` is multiplied by `p_bar` to report
  elasticity. The mechanism imposes its own elasticity, independently of this fit.

No benchmark threshold or estimate was adjusted to make a category pass. Reports
print the flag, observed value, and current investigation status. Author follow-up:
verify the economic unit and sale-code semantics before interpreting the benchmark.
