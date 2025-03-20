import os
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import oracledb
from db_config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_SERVICE

# Create necessary folders
image_folder = "report_images"
dashboard_folder = "dashboards"
os.makedirs(image_folder, exist_ok=True)
os.makedirs(dashboard_folder, exist_ok=True)

# Establish connection to OracleDB
def get_db_connection():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)
    return conn

# Fetch data from OracleDB with distinct job_names and sorted ordering
def fetch_data():
    conn = get_db_connection()
    query = """
        SELECT job_name, rule_name, TO_CHAR(date_column, 'YYYY-MM-DD') AS date, actual_result_value
        FROM your_table_name
        ORDER BY job_name, rule_name, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    df['date'] = pd.to_datetime(df['date'])
    return df

# Function to plot trends for each rule
def plot_rule_trends(job_name, rule_name, data):
    rule_data = data[data['rule_name'] == rule_name]

    plt.figure(figsize=(10, 5))
    plt.plot(rule_data['date'], rule_data['actual_result_value'], marker='o', linestyle='-', linewidth=2, markersize=6, label=rule_name, color='blue')

    # Identify points where value becomes zero
    zero_mask = rule_data['actual_result_value'] == 0
    plt.scatter(rule_data['date'][zero_mask], rule_data['actual_result_value'][zero_mask], label="Values become zero", color='red', zorder=3, s=78)

    # Annotate points with values
    for x, y in zip(rule_data['date'], rule_data['actual_result_value']):
        plt.annotate(f"{y}\n{x.strftime('%m-%d')}", xy=(x, y), textcoords="offset points", xytext=(10, 10), ha='left', fontsize=8, color='black')

    # Plot settings
    plt.title(f"Trend for {rule_name}", fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=10)
    plt.ylabel("Actual Result Value", fontsize=10)
    plt.grid(visible=True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=10)

    # Save the plot
    plot_filename = f"{image_folder}/output_plot_{job_name}_{rule_name}.png"
    plt.savefig(plot_filename)
    plt.close()

# Generate dashboards for each distinct job_name
def generate_dashboards(df):
    unique_jobs = df['job_name'].unique()

    for job_name in unique_jobs:
        job_data = df[df['job_name'] == job_name]

        # Plot graphs for each rule in the job
        for rule in job_data['rule_name'].unique():
            plot_rule_trends(job_name, rule, job_data)

        # Get image files for this job
        image_files = [f for f in os.listdir(image_folder) if f.startswith(f"output_plot_{job_name}_") and f.endswith(".png")]

        # Create HTML dashboard
        output_html_file = f"{dashboard_folder}/dashboard_{job_name}.html"
        with open(output_html_file, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Dashboard</title></head><body>")
            f.write(f"<h1 style='text-align:center;'>Dashboard for {job_name}</h1>")
            f.write("<div style='display: flex; flex-wrap: wrap; justify-content: center;'>")

            for img in image_files:
                with open(f"{image_folder}/{img}", "rb") as image_file:
                    base64_str = base64.b64encode(image_file.read()).decode()
                    f.write(f'<div style="margin: 10px;"><img src="data:image/png;base64,{base64_str}" alt="{img}" style="width:300px;"><br>{img}</div>')

            f.write("</div></body></html>")

        print(f"Dashboard created: {output_html_file}")

# Main Execution
df = fetch_data()
generate_dashboards(df)
