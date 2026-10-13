# Changelog

## 0.1.0 - 2026-10-13

Initial implementation of specification v1.0; configs transcribed without changing supplied values.

Pending author approval (not amendments to the missing Pilot Protocol):

- The demand slope is negative. OLS, IV and DoubleML convert a direct price coefficient to elasticity as `coefficient * p_bar`. The spec's M4 negative sign would reverse downward-sloping demand.
- Performance checkpoints 78, 104, 156 are interpreted as absolute weeks (cycles 26, 52, 104), because the loop has only 104 cycles.
- Recommended and deployed regret are percentage points; cumulative regret sums those values.
- Default instrument pass-through 0.20 is provisional until P4 and author approval; P4 explores the supplied grid.
- Cleaning order, competing-price index, cross-fitting splits, decision reliability, and compute-budget ladder cannot be certified against protocol sections that were not provided.
- Stores lacking zones are dropped provisionally, following spec section 14; this requires author confirmation.
- Week dates and store zones can be imported from the public Kilts codebook. Easter indicators use actual Easter dates, not questionable special-event labels in that manual.
- Exact scientific replay excludes wall-clock timings, run IDs and timestamps, which cannot be deterministic.