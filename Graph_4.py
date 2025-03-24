# Create HTML dashboard with images in table format
output_html_file = f"{DASHBOARD_FOLDER}/dashboard_{job_name}.html"
with open(output_html_file, "w", encoding="utf-8") as f:
    f.write("<html><head><title>Dashboard</title></head><body>")
    f.write(f"<h1 style='text-align:center;'>Dashboard for {job_name}</h1>")
    
    # Start table
    f.write("<table style='width:100%; border-collapse: collapse; text-align:center;'>")
    
    for i in range(0, len(image_files), 2):  # Looping 2 images at a time
        f.write("<tr>")  # Start row
        
        # Process two images in each row
        for j in range(2):
            if i + j < len(image_files):
                img = image_files[i + j]
                with open(f"{IMAGE_FOLDER}/{img}", "rb") as image_file:
                    base64_str = base64.b64encode(image_file.read()).decode()

                f.write(f"""
                    <td style='padding: 15px;'>
                        <div style="font-weight:bold; margin-bottom: 5px;">{img}</div>
                        <img src="data:image/png;base64,{base64_str}" alt="{img}" style="width:300px; border:1px solid black;">
                    </td>
                """)

        f.write("</tr>")  # End row

    f.write("</table>")  # End table
    f.write("</body></html>")

print(f"Dashboard created: {output_html_file}")
