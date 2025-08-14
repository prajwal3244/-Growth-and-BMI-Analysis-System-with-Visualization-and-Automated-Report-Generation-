To run the Growth and BMI Analysis System, 

Install Python – Ensure Python is installed on your system.

Install Required Libraries – Run:

pip install numpy pandas matplotlib openpyxl scipy reportlab jinja2 weasyprint


Install WeasyPrint Dependencies –

Windows: Install GTK from WeasyPrint.org.

Linux: Run sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libjpeg-dev libgif-dev


Prepare Dataset Files – Place male0-20 csv.csv and female0-20 csv.csv in the same folder as your Python script.

Prepare HTML Template – Add report_template.html in the same folder for PDF generation.

Save Your Code – Save the script as growth_bmi_analysis.py.

Open Terminal – Navigate to the folder containing the script and files.

Run the Script – Execute:

python growth_bmi_analysis.py


Provide Input – Follow prompts to enter gender, age, name, weight, and height.

View Output – The script will:

Display BMI charts.

Analyze BMI and health category.

Generate report.pdf with results and reference data.


*********************************************************************************************************************************************************************************************************



Takes gender and age as input.

Reads growth reference data from CSV (different for male/female).

Accepts weight and height, calculates BMI, and classifies it.

Displays results with graphs (pie chart + dotted plot).

Generates a custom PDF report using Jinja2 + WeasyPrint.

It’s basically a personal health analysis and report generation tool for children/young adults.
