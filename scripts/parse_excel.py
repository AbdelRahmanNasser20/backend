import sys
import os
import re
import pandas as pd
import difflib
from datetime import datetime

# Add the parent directory to the system path before importing `app`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Employee, Event

# Print the current working directory
print("Current Directory:", os.getcwd())

config_name = os.getenv('FLASK_ENV')
app = create_app(config_name)

SQLALCHEMY_DATABASE_URI = "postgres://u7rjm4v00r7o80:p29318c85fd890024aabb5af0d2eee671f3b489fceb0846bc261184455c66a610@cb5ajfjosdpmil.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcbccjj9ki7jbl"

MOE_EMAIL = "m.fouladi99@gmail.com"

# Updated pattern to match the provided formats
PATTERN = r"((\w+ [\w-]+\.? \(\w+ \d\.\d{1,2}\))|(Moe))( & (\w+ [\w-]+\.? \(\w+ \d\.\d{1,2}\)|Moe))* @ .+"

def parse_event_summary(string):
    """
    Parses a string to extract teacher names, roles, and hours worked.
    """
    LEAD = "Teacher - Lead"
    ASSISTANT = "Teacher - Assistant"

    names_part = string.split('@')[0]

    names = [part.split('(')[0].strip() for part in names_part.split('&')]

    extracted_info_revised = []

    for part in names_part.split('&'):
        # print(part)
        if part.lower().strip() == "moe":            
            print("TRUEEEE MOEEE ", part)
            continue
        info_parts = part.split()
        name = ' '.join(info_parts[:2])
        role_letter = info_parts[2][1]  # Getting the letter inside the parentheses
        
        role = LEAD if role_letter == "L" else ASSISTANT if role_letter == "A" else "OTHER"
        hours_worked = float(info_parts[3][:-1])

        extracted_info_revised.append([name, role, hours_worked])
        
    return extracted_info_revised

def find_closest_employee(name, employees, similarity_threshold=0.5):
    """
    Finds the employee with the name most similar to the given name, 
    only if the similarity is above the specified threshold.
    """
    if not employees:
        return None, None, None

    closest_names = difflib.get_close_matches(name, employees.keys(), n=1, cutoff=similarity_threshold)
    
    if closest_names:
        closest_name = closest_names[0]
        employee_info = employees[closest_name]
        return closest_name, employee_info['email'], employee_info['id']
    else:
        return None, None, None

def retrieve_employees():
    """
    Retrieves all employees from the database and stores them in a dictionary.
    """
    employees = {}
    with app.app_context():
        all_employees = Employee.query.all()
        for employee in all_employees:
            employees[employee.name] = {'id': employee.id, 'email': employee.email}
    return employees

def upload_excel(file_path):
    df = pd.read_excel(file_path)
    
    correct_entries = []
    incorrect_entries = []

    for index, entry in df.iterrows():
        print(entry)
        subject = entry.iloc[0]
        if re.match(PATTERN, subject):
            correct_entries.append(entry)
        else:
            incorrect_entries.append(entry)

    total_entries = len(df)
    incorrect_count = len(incorrect_entries)

    print("Incorrect Entries:")
    # for entry in incorrect_entries:
    #     print(entry)
    print(f"\nTotal Entries: {total_entries}")
    print(f"Incorrect Entries: {incorrect_count}\n")

    with app.app_context():
        employees_dict = retrieve_employees()
        
        for entry in correct_entries:
            subject = entry.iloc[0]
            date = entry.iloc[1].strftime('%m-%d-%Y')
            
            location = entry.iloc[2]
            organizer = entry.iloc[3]

            # Convert the date string to a datetime object
            # event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            # print(date, type(date))
            parsed_info = parse_event_summary(subject)
            if not parsed_info:
                continue

            for info in parsed_info:
                name, position, hours = info
                employee_name, employee_email, employee_id = find_closest_employee(name, employees_dict)

                if employee_id is None:
                    print(f"Employee not found for: {name}")
                    continue

                event = Event(
                    employee_id=employee_id,
                    name=employee_name,
                    date=date,
                    hours=hours,
                    position=position,
                    location=location
                )                
                # print(event)
                db.session.add(event)


        db.session.commit()
        db.session.rollback()


if __name__ == '__main__':
    print("hello world")
    print(os.getcwd())
    upload_excel('data/December_2023_events.xlsm')
    # upload_excel('data/July 2024.xlsm')
