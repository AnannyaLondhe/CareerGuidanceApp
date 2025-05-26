import pandas as pd

# Load the CSV file
df = pd.read_csv("your_file.csv")  # Replace with your actual CSV file path

for index, row in df.iterrows():
    report_type = str(row[3]).strip().lower()

    if report_type == "missing":
        exception_query = str(row[4])
        missing_query = str(row[5])

        # Extract FROM and WHERE parts from exception_query
        ex_query_lower = exception_query.lower()
        ex_from_index = ex_query_lower.find("from")
        ex_where_index = ex_query_lower.find("where")

        if ex_from_index != -1 and ex_where_index != -1:
            ex_table = exception_query[ex_from_index + 5 : ex_where_index].strip()
            ex_where = exception_query[ex_where_index + 6 :].strip()
        else:
            ex_table = None
            ex_where = None
            print(f"⚠️ Row {index + 2}: FROM or WHERE missing in EXCEPTION_DTLS_QUERY")

        # Extract FROM and WHERE parts from missing_query
        miss_query_lower = missing_query.lower()
        miss_from_index = miss_query_lower.find("from")
        miss_where_index = miss_query_lower.find("where")

        if miss_from_index != -1 and miss_where_index != -1:
            miss_table = missing_query[miss_from_index + 5 : miss_where_index].strip()
            miss_where = missing_query[miss_where_index + 6 :].strip()
        else:
            miss_table = None
            miss_where = None
            print(f"⚠️ Row {index + 2}: FROM or WHERE missing in MISSING_RECS_QUERY")

        # Compare
        tables_match = ex_table == miss_table
        where_match = ex_where == miss_where

        print(f"\nRow {index + 2} - Report Type: Missing")
        print(f"  Tables Match: {tables_match} ➜ '{ex_table}' vs '{miss_table}'")
        print(f"  WHERE Match: {where_match} ➜ '{ex_where}' vs '{miss_where}'")

        if not tables_match or not where_match:
            print("  ❌ Mismatch Found!")
