import pandas as pd

# Load the Excel file
df = pd.read_excel("your_excel_file.xlsx")

# Loop through each row
for index, row in df.iterrows():
    report_type = row[3]
    exception_query = str(row[4])
    missing_query = str(row[5])

    # Extract table name and WHERE clause from exception_query
    ex_query_lower = exception_query.lower()
    ex_from_index = ex_query_lower.find("from")
    ex_where_index = ex_query_lower.find("where")

    if ex_from_index != -1 and ex_where_index != -1:
        ex_table = exception_query[ex_from_index + 5 : ex_where_index].strip()
        ex_where = exception_query[ex_where_index + 6 :].strip()
    else:
        ex_table = None
        ex_where = None

    # Extract table name and WHERE clause from missing_query
    miss_query_lower = missing_query.lower()
    miss_from_index = miss_query_lower.find("from")
    miss_where_index = miss_query_lower.find("where")

    if miss_from_index != -1 and miss_where_index != -1:
        miss_table = missing_query[miss_from_index + 5 : miss_where_index].strip()
        miss_where = missing_query[miss_where_index + 6 :].strip()
    else:
        miss_table = None
        miss_where = None

    # Compare table name and where clause
    match_table = ex_table == miss_table
    match_where = ex_where == miss_where

    print(f"\nRow {index + 2} - Report Type: {report_type}")
    print(f"  Tables Match: {match_table} -> '{ex_table}' vs '{miss_table}'")
    print(f"  WHERE Match: {match_where}")
    
    if not match_table or not match_where:
        print("  ❌ Mismatch Found!")
