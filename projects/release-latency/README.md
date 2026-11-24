# Cloud Release Performance Analysis

This portfolio exercise uses generated request and trace data in local SQLite and Python. The fixture models three regions, two endpoints, and two release groups. It injects a cache delay in the east/catalog canary and generates separate discovery and confirmation requests for every segment. There are no real users, production systems, or cloud credentials involved.

Run `python analyze.py` with NumPy and SciPy installed. The script generates the fixture, joins request events to trace timings and release metadata, validates row counts and unique keys, and reconciles elapsed time against the trace stages. Its SQL projection excludes the synthetic contact field. Outputs are a segment KPI CSV and a JSON record of the test, trace decomposition, and rollback replay.

## Release decision

Should the canary configuration expand, or should the affected segment revert to baseline? The analysis tracks mean and p95 latency and the proportion of requests exceeding 220 ms. The discovery set selects the region and endpoint with the largest canary mean increase. One two-sided Welch t-test then compares independent canary and baseline requests for that segment in the untouched confirmation set. The test concerns the difference in means. The p95 values are descriptive KPIs.

The east/catalog endpoint was selected. Across 1,000 confirmation requests per group, the canary was 69.0 ms slower on average (95% confidence interval 66.8 to 71.2 ms). The cache stage contributed 69.9 ms. The service stage decreased by 1.1 ms, and the network stage increased by 0.3 ms. These stage differences sum to the net difference before rounding. The reported p-value underflows to zero in floating-point arithmetic.

## Recommendation and follow-up

Revert the cache configuration for the affected segment in the simulated scenario. Replaying the same canary request inputs with the baseline cache setting brought p95 from 232.5 ms to 162.5 ms. The baseline confirmation group's p95 was 163.1 ms. This replay recovers the injected delay by construction. Its result illustrates the analysis workflow and should not be used as a forecast of a live rollback.

For a future controlled rollout, monitor p95 and the share of slow requests by endpoint, region, and release group. Set a baseline-relative guardrail with the product and infrastructure teams before launch, verify that cohort routing stays balanced, and confirm a sustained improvement before expanding traffic. A real review would also check repeated requests from the same client and shared infrastructure for dependence, evaluate error rates and traffic shifts, and assess whether trace timings are additive.
