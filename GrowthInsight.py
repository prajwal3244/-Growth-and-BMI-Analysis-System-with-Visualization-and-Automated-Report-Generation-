import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
from scipy import stats
from scipy import constants
from reportlab.pdfgen import canvas 
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.pdfbase import pdfmetrics 
from reportlab.lib import colors
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
gender=input("Enter the gender M(male)/F(female):")
if(gender=='M'):
    age=(input("Enter the age(Months/Year):"))
    df = pd.read_csv('male0-20 csv.csv')
    df.head()
    print(df[df["Age"] == age].head())
    
    def calculate_bmi(weight, height):
    
    # Calculate BMI using the formula: BMI = weight / (height * height)
        bmi = weight / (height ** 2)
        return bmi

    def determine_bmi_category(bmi):
     #Determine the BMI category based on BMI value.
       if bmi < 18.5:
         return "Underweight"
       elif 18.5 <= bmi < 24.9:
         return "Normal Weight"
       elif 25 <= bmi < 29.9:
         return "Overweight"
       else:
         return "Obesity"


    #''Main function to get user input, calculate BMI, and display the result.'''
    # Get user input for weight and height
    name=input("Enter the Name:")
    weight = float(input("Enter your current weight (in kilograms): "))
    height = float(input("Enter your current height (in meters): "))
    
    # Calculate BMI
    bmi = calculate_bmi(weight, height)

    # Determine the BMI category
    category = determine_bmi_category(bmi)

    # Display the results
    print(f"Name: {name}")
    print(f"Weight: {weight}")
    print(f"Height: {height:1f}")
    print(f"BMI: {bmi:.1f}")
    print(f"Category: {category}")
    y = np.array([bmi, weight, height])
    mylabels = ["BMI", "WEIGHT", "HEIGHT"]
      
    plt.subplot(1, 2, 1)
    plt.pie(y, labels = mylabels)
      
    plt.subplot(1, 2, 2)
    plt.plot(y, linestyle = 'dotted')
      
    plt.show()
    
    
    def generate_pdf_report(output_filename, template_filename, context):
    # Set up the Jinja2 environment
             env = Environment(loader=FileSystemLoader('.'))
             template = env.get_template(template_filename)
    
    # Render the template with the provided context
             html_content = template.render(context)
    
    # Convert the rendered HTML to a PDF
             HTML(string=html_content).write_pdf(output_filename)
             print(f"PDF report generated: {output_filename}")

    if __name__ == "__main__":
    # Define the data for the report
             context = {
             'title': 'Height And Weight Analysis Report',
             'subtitle': 'December 2024',
             'content': 'This report provides an overview of physical health.',
             'items': [f"Name: {name}",f"Weight: {weight}",f"Height: {height:1f}",f"BMI: {bmi:.1f}",f"Category: {category}",df[df["Age"] == age].head()],
             'date': datetime.now().strftime('%B %d, %Y'),
              }
    
    
# Generate the PDF report
             generate_pdf_report('report.pdf', 'report_template.html', context)

else:
    age=input("Enter the age:")
    df = pd.read_csv('female0-20 csv.csv')
    df.head()
    print(df[df["Age"] == age].head())
    def calculate_bmi(weight, height):
    
    # Calculate BMI using the formula: BMI = weight / (height * height)
        bmi = weight / (height ** 2)
        return bmi

    def determine_bmi_category(bmi):
     #Determine the BMI category based on BMI value.
       if bmi < 18.5:
         return "Underweight"
       elif 18.5 <= bmi < 24.9:
         return "Normal Weight"
       elif 25 <= bmi < 29.9:
         return "Overweight"
       else:
         return "Obesity"


    #''Main function to get user input, calculate BMI, and display the result.'''
    # Get user input for weight and height
    name=input("Enter the Name:")
    weight = float(input("Enter your current weight (in kilograms): "))
    height = float(input("Enter your current height (in meters): "))
    
    # Calculate BMI
    bmi = calculate_bmi(weight, height)

    # Determine the BMI category
    category = determine_bmi_category(bmi)

    # Display the results
    print(f"Name: {name}")
    print(f"Weight: {weight}")
    print(f"Height: {height:1f}")
    print(f"BMI: {bmi:.1f}")
    print(f"Category: {category}")
    y = np.array([bmi, weight, height])
    mylabels = ["BMI", "WEIGHT", "HIGHT"]
      
    plt.subplot(1, 2, 1)
    plt.pie(y, labels = mylabels)
      
    plt.subplot(1, 2, 2)
    plt.plot(y, linestyle = 'dotted')
      
    plt.show()
    
    
    def generate_pdf_report(output_filename, template_filename, context):
    # Set up the Jinja2 environment
             env = Environment(loader=FileSystemLoader('.'))
             template = env.get_template(template_filename)
    
    # Render the template with the provided context
             html_content = template.render(context)
    
    # Convert the rendered HTML to a PDF
             HTML(string=html_content).write_pdf(output_filename)
             print(f"PDF report generated: {output_filename}")

    if __name__ == "__main__":
    # Define the data for the report
             context = {
             'title': 'Height And Weight Analysis Report',
             'subtitle': 'December 2024',
             'content': 'This report provides an overview of physical health.',
             'items': [f"Name: {name}",f"Weight: {weight}",f"Height: {height:1f}",f"BMI: {bmi:.1f}",f"Category: {category}",df[df["Age"] == age].head()],
             'date': datetime.now().strftime('%B %d, %Y'),
              }
    
# Generate the PDF report
             generate_pdf_report('report.pdf', 'report_template.html', context)
