"""
Sales Analytics Without Pandas
"""
import csv
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data")/"electronics_sales.csv"


def read_sales(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Read the CSV with the csv module and return the raw rows."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at: {path}.")
    
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)
        print("--- Data summary ---")
        print(f"Columns found: {columns}")
        print(f"Total raw records read: {len(rows)}\n")
        return rows


def parse_number(value: str) -> float | None:
    """Convert a messy numeric string to a float, or return None if it cannot be trusted."""
    if value is None:
        return None
    value = str(value).strip().replace(",", "")
    if value.upper().startswith("KES"):
        value = value.replace("KES", "").strip()
    if value == "" or value.upper() in ("N/A", "NULL", "NONE"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return (clean_rows, skipped_rows). Clean rows have numeric quantity, unit price and revenue."""
    clean_rows = []
    skipped_rows = []
    
    for row in rows:
        quantity_check = parse_number(row.get("quantity", ""))
        price_check = parse_number(row.get("unit_price_kes", ""))
        
        if quantity_check is None:
            skipped_rows.append({"row": row, "reason": "Invalid or missing quantity"})
        elif price_check is None:
            skipped_rows.append({"row": row, "reason": "Invalid or missing unit price"})
        else:
            cleaned_row = dict(row)
            cleaned_row["quantity"] = int(quantity_check)
            cleaned_row["unit_price_kes"] = price_check
            cleaned_row["revenue"] = quantity_check * price_check
            clean_rows.append(cleaned_row)

    return clean_rows, skipped_rows


def total_revenue(rows: list[dict]) -> float:
    return sum(row["revenue"] for row in rows)


def revenue_by(rows: list[dict], field: str) -> dict[str, float]:
    """Total revenue grouped by any column (product, store, payment_method...)."""
    totals = {}
    for row in rows:
        value = row.get(field)
        if value:
            totals[value] = totals.get(value, 0.0) + row["revenue"]
    return totals        


# Helper sorting function for top_n
def get_sort_key(pair):
    product_name, revenue_value = pair
    # Negative revenue puts highest numbers first.
    # Product name handles ties alphabetically (A to Z).
    return (-revenue_value, product_name)


def top_n(totals: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Return the n highest (key, value) pairs, highest first."""
    pairs = list(totals.items())
    # FIX 2: Use a clean sorting key to handle ties gracefully and predictably
    sorted_list = sorted(pairs, key=get_sort_key)
    return sorted_list[:n]


def high_value(rows: list[dict], threshold: float) -> list[dict]:
    """Transactions whose revenue is at or above threshold (use a comprehension)."""
    # FIX 3: Replaced the manual loop with a required list comprehension!
    return [row for row in rows if row["revenue"] >= threshold]


# Reusable statistics - implement these yourself, no statistics module.
def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Empty list, can't find mean")
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate median of an empty list")
    sorted_values = sorted(values)
    length = len(sorted_values)
    mid = length // 2
    if length % 2 == 1:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2.0


def minimum_maximum(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("List empty, can't find min/max")
    minimum = maximum = values[0]
    for value in values:
        if value < minimum:
            minimum = value
        if value > maximum:
            maximum = value
    return minimum, maximum    


def verify_with_pandas(path: Path, my_results: dict) -> dict:
    """Recompute the headline numbers with pandas and check if they match."""
    df = pd.read_csv(path)
    
    df['quantity_clean'] = df['quantity'].apply(parse_number)
    df['price_clean'] = df['unit_price_kes'].apply(parse_number)
    
    df_clean = df.dropna(subset=['quantity_clean', 'price_clean'])
    
    pandas_revenue = df_clean['quantity_clean'] * df_clean['price_clean']
    
    pd_total = pandas_revenue.sum()
    pd_mean = pandas_revenue.mean()
    pd_median = pandas_revenue.median()
    
    # Check if the Total Revenue matches
    if round(my_results["total_revenue"], 2) == round(pd_total, 2):
        total_match = "MATCH"
    else:
        total_match = "MISMATCH"
        
    # Check if Mean and Median match
    if round(my_results["mean"], 2) == round(pd_mean, 2) and round(my_results["median"], 2) == round(pd_median, 2):
        stats_match = "MATCH"
    else:
        stats_match = "MISMATCH"
        
    # Group product revenue with pandas and check if the dictionary matches
    df_clean_with_rev = df_clean.copy()
    df_clean_with_rev['revenue'] = pandas_revenue
    
    pd_prod_series = df_clean_with_rev.groupby('product')['revenue'].sum()
    pd_prod_dict = pd_prod_series.to_dict()
    
    product_match = "MATCH"
    for product_name, amount in pd_prod_dict.items():
        my_amount = my_results["prod_revenue"].get(product_name, 0.0)
        if round(my_amount, 2) != round(amount, 2):
            product_match = "MISMATCH"
            
    pd_top3_list = sorted(pd_prod_dict.items(), key=get_sort_key)[:3]
    if my_results["top_3"] == pd_top3_list:
        top3_match = "MATCH"
    else:
        top3_match = "MISMATCH"

    return {
        "Total revenue": total_match,
        "Revenue by product": product_match,
        "Top 3": top3_match,
        "Mean / median": stats_match
    }


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    
    raw_data = read_sales()
    clean, skipped = convert_rows(raw_data)
    
    tot = total_revenue(clean)
    by_product = revenue_by(clean, "product")
    top3_products = top_n(by_product, 3)
    
    threshold_value = 50000.0
    high_val_tx = high_value(clean, threshold_value)
    
    rev_list = []
    for row in clean:
        rev_list.append(row["revenue"])
        
    avg_rev = mean(rev_list)
    med_rev = median(rev_list)
    min_rev, max_rev = minimum_maximum(rev_list)
    
    metrics = {
        "total_revenue": tot,
        "prod_revenue": by_product,
        "top_3": top3_products,
        "mean": avg_rev,
        "median": med_rev
    }
    verification = verify_with_pandas(DATA_PATH, metrics)
    
    skipped_items_list = []
    for s in skipped:
        sale_id = s["row"].get("sale_id", "UNKNOWN")
        reason = s["reason"]
        skipped_items_list.append(f"{sale_id}: {reason}")
    
    skipped_formatted = ", ".join(skipped_items_list)
    
    report_lines = []
    
    report_lines.append("=== Sales report: September 2026 ===")
    report_lines.append(f"Rows read          : {len(raw_data)}")
    report_lines.append(f"Rows used          : {len(clean)}")
    report_lines.append(f"Rows skipped       : {len(skipped)}   ({skipped_formatted})")
    report_lines.append("")
    report_lines.append(f"Total revenue (KES): {tot:,.2f}")
    report_lines.append("")
    
    report_lines.append("Revenue by product (KES)")

    all_products_sorted = sorted(by_product.items(), key=get_sort_key)
    for item in all_products_sorted:
        prod_name = item[0]
        prod_rev = item[1]
        report_lines.append(f"  {prod_name}            {prod_rev:,.2f}")
        
    report_lines.append("")
    report_lines.append("Top 3 products")
    counter = 1
    for item in top3_products:
        prod_name = item[0]
        prod_rev = item[1]
        report_lines.append(f"  {counter}. {prod_name} - KES {prod_rev:,.2f}")
        counter += 1
        
    report_lines.append("")
    report_lines.append(f"High-value transactions (>= KES {threshold_value:,.2f}): {len(high_val_tx)}")
    for tx in high_val_tx:
        t_id = tx['sale_id']
        t_date = tx['sale_date']
        t_store = tx['store']
        t_prod = tx['product']
        t_rev = tx['revenue']
        report_lines.append(f"  {t_id}  {t_date}  {t_store}  {t_prod}  KES {t_rev:,.2f}")
        
    report_lines.append("")
    report_lines.append("Transaction revenue statistics")
    report_lines.append(f"  mean   : {avg_rev:,.2f}")
    report_lines.append(f"  median : {med_rev:,.2f}")
    report_lines.append(f"  min    : {min_rev:,.2f}")
    report_lines.append(f"  max    : {max_rev:,.2f}")
    report_lines.append("")
    
    report_lines.append("=== pandas verification ===")
    report_lines.append(f"Total revenue      : {verification['Total revenue']}")
    report_lines.append(f"Revenue by product : {verification['Revenue by product']}")
    report_lines.append(f"Top 3              : {verification['Top 3']}")
    report_lines.append(f"Mean / median      : {verification['Mean / median']}")
    
    report = "\n".join(report_lines) + "\n"
    
    with open("output/sales_report.txt", "w", encoding="utf-8") as out_file:
        out_file.write(report)
        
    print("Report compiled successfully and written to 'output/sales_report.txt'.")


