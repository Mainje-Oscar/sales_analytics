# Sales Analytics

This is a Python solution configured to ingest, clean, and analyze messy transaction files using Python's standard library only. Pandas is integrated within a validation gate to confirm data completeness and correctness.

## Implementation approach and cleaning rules
Messy strings encountered within data fields are handled via `parse_number()` rules:
* **Removal of commas:** Standard values such as `"38,999"` have commas stripped before assessment.
* **Truncation of currency prefix:** Values containing local leading string prefixes (e.g., `KES 18999`) have their literal characters omitted to parse the underlying numerical value.
* **Skipped records:** Rows with non-convertible text inputs (such as `"two"`, blank spaces, or `"N/A"`) fail numeric coercion. These items are omitted from analysis and cataloged with explicit error tags:
  * `S-3006`: Skips due to an alpha string entry (`"two"`) in quantity.
  * `S-3030`: Skips due to a null-style placeholder (`"N/A"`) in price.
  * `S-3035`: Skips due to an empty field for quantity.
  * `S-3039`: Skips due to an empty field for unit price.

## Assumptions
* **Tie breaking rule:** Whenever multiple records or aggregate values have matching revenue values during a ranking, alphabetic indexing on keys (e.g., product text names) acts as a secondary tie-breaker.
* Hand-built statistical functions check for zero-length lists and throw a `ValueError`.

## Environment set up and execution
1. Arrange data structure directories:
   ```bash
   sales-analytics/
   ├── sales_analysis.py
   ├── data/
   │   └── electronics_sales.csv
   ├── output/
   │   └── sales_report.txt
   └── requirements.txt
   ```
2. Build and run environment:
   ```bash
   pip install -r requirements.txt
   python sales_analysis.py
   ```
