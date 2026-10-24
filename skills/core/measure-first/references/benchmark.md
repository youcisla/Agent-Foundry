# Benchmark rules

- Warm up, then drop the first measured sample.
- Separate wall time from provider-reported time.
- Regression: ratio > 1.05 AND delta >= 0.8 ms.
- Key by model, load bucket, and format version.
- Refresh the baseline with an explicit command; review the diff.
