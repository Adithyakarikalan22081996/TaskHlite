import pyodbc
import pandas as pd

server = 'DESKTOP-KIUV5FS'
database = 'TaskHLite'
username = 'sa'
password = 'Naren@876'
table_name = 'Task_List'
upload_excel = input("Enter the upload excel details: ")

# Create the connection string
connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Establish a connection
connection = pyodbc.connect(connection_string)

# Read the Excel data
df = pd.read_excel(upload_excel)

# Iterate through the rows and insert data
for i, row in df.iterrows():
    center = row["Center"]
    region = row["Region"]
    task = row["Task List"]
    process = row["Process "]
    user = row["User ID"]
    frequency = row["Frequency"]
    deadline = row["Deadline"]
    effective_from = row["effective_from"]
    effective_to = row["effective_to"]

    # Check if the record already exists
    cursor = connection.cursor()
    query = (f"SELECT COUNT(*) FROM {table_name} WHERE Center = ? AND Region = ? AND Task_List = ? AND Process = ? AND "
             f"User_ID = ? AND Frequency = ? AND Deadline = ? AND Effective_from = ? AND Effective_to = ?")
    cursor.execute(query, center, region, task, process, user, frequency, deadline, effective_from, effective_to)
    record_count = cursor.fetchone()[0]

    if record_count == 0:
        # Insert the record if it doesn't exist
        insert_query = (f"INSERT INTO {table_name} (Center, Region, Task_List, Process, User_ID, Frequency, Deadline, "
                        f"Effective_from, Effective_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
        cursor.execute(insert_query, center, region, task, process, user, frequency, deadline, effective_from,
                       effective_to)
        connection.commit()

    # Close the cursor for this iteration
    cursor.close()

# Close the connection after all iterations
connection.close()
print("Data upload completed.")
