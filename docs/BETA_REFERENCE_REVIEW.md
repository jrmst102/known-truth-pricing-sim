# Benchmark elasticity investigation (issue draft)

Status: open locally; no external issue has been posted.

The v1.0 observational elasticities were -3.159570873246531 (crackers) and
-3.84815906022416 (tissue). They are descriptive review flags, not exclusions.
Imposed scenario eta defines the known truth. Both original values are preserved
in calibration diagnostics and shown beside the regenerated values in reports.
Changing reference price from the nonpromotion median to the all-week mean
necessarily changes beta * p_bar; this is reported explicitly, not hidden.

Investigate before substantive interpretation:

- Verify unit price is PRICE / QTY (including bundle/multipack conventions).
- Confirm natural logarithms for demand and the beta * p_bar sign convention.
- Check SALE coding, nonpromotion prices, and promotion-depth calculations.
- Review the competing index, eligibility restriction, and weekly weighting.
- Compare observational slopes with and without promotions and competing controls.

Outcome: pending author/domain review. No diagnostic bounds were relaxed and
no observational estimate was substituted for the imposed known truth.
