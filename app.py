from flask import Flask, render_template,request,redirect, session, url_for
import os
import pyodbc
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import string
import random

def generate_secret_key(length=24):
    characters = string.ascii_letters + string.digits
    secret_key = ''.join([random.choice(characters) for _ in range(length)])
    return secret_key

app = Flask(__name__)
app.secret_key = generate_secret_key()


server = 'DESKTOP-KIUV5FS'
database = 'TaskHLite'
username = 'sa'
password = 'Naren@876'
table_name = 'Task_List'
raw_data_table = 'Completed_Raw_data'
connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
connection = pyodbc.connect(connection_string)

user = "KUMARNR"

def pending_dataframe():
    checklist =pd.read_sql(f"select * from {table_name}",connection)
    checklist["User_ID"] = checklist["User_ID"].str.lower()
    checklist = checklist.drop(columns=["id"])
    user_checklist = checklist[checklist["User_ID"]==user.lower()]
    completed = pd.read_sql(f"select * from {raw_data_table}",connection)
    completed = completed.drop(columns=["id"])
    completed["User_ID"] = completed["User_ID"].str.lower()
    completed = completed[completed["User_ID"]==user.lower()]
    today1 = datetime.today()
    thisweek = today1.isocalendar()[1]
    thisyear = today1.year
    thismonth = today1.month
    this_bi_week = ""

    if thisweek % 2 == 0:
        this_bi_week = thisweek
    else:
        this_bi_week = thisweek - 1


    if thismonth<4:
        thisquarter = "Q1"
    elif thismonth<7:
        thisquarter = "Q2"
    elif thismonth<10:
        thisquarter = "Q3"
    else:
        thisquarter = "Q4"

    if thismonth<6:
        thishalfyear = "H1"
    else:
        thishalfyear = "H2"

    completed["Date"] = pd.to_datetime(completed["endtime"])
    completed['WeekNo'] = completed['Date'].dt.isocalendar().week
    completed['MonthNo'] = completed['Date'].dt.month
    completed['Bi-Weekly'] = np.where(completed['WeekNo']%2 ==0, completed['WeekNo'],completed['WeekNo']-1 )
    completed['Quarterly'] = np.where(completed["MonthNo"]<4,"Q1",
                                      np.where(completed["MonthNo"]<7,"Q2",
                                      np.where(completed["MonthNo"]<10,"Q3","Q4")))

    completed['Half Yearly'] = np.where(completed["MonthNo"]<7,"H1","H2")
    completed['Yearly'] = completed['Date'].dt.year
    completed["period"] = ""
    completed["period"] = np.where(completed["Frequency"] == "Bi-Weekly",np.where(completed["Bi-Weekly"] == this_bi_week, "Current", "older"),completed["period"])
    completed["period"] = np.where(completed["Frequency"] == "Weekly",np.where(completed["WeekNo"] == thisweek, "Current", "older"),completed["period"])
    completed["period"] = np.where(completed["Frequency"] == "Daily",np.where(completed["Date"] == today1, "Current", "older"),completed["period"])
    completed["period"] = np.where(completed["Frequency"] == "Monthly",np.where(completed["MonthNo"] == thismonth, "Current", "older"),completed["period"])
    completed["period"] = np.where(completed["Frequency"] == "Quarterly",np.where(completed["Quarterly"] == thisquarter, "Current", "older"),completed["period"])
    completed["period"] = np.where(completed["Frequency"] == "Half Yearly",np.where(completed["Half Yearly"] == thishalfyear, "Current", "older"),completed["period"])
    completed["period"] = np.where(completed["Frequency"] == "Yearly",np.where(completed["Yearly"] == thisyear, "Current", "older"),completed["period"])

    #completed["period"] = np.where(completed["Frequency"] == "Weekly",
    #                               np.where(completed["WeekNo"] == thisweek, "Current", "older"),
    #                               np.where(completed["MonthNo"] == thismonth, "Current", "older"))
    completed = completed[completed["period"] == "Current"]
    column = user_checklist.columns
    pending_checklist = user_checklist.merge(
        completed, on=["User_ID", "Process", "Region", "Center", "Frequency", "Task_List"], how="left")
    pending_checklist = pending_checklist[pending_checklist["Status"] != "Completed"]

    pending_checklist = pending_checklist[['User_ID','Center','Region','Process','Task_List','Frequency','Deadline']]
    return pending_checklist

def update_Task(center,region,task_List,process,user,frequency,deadline,effective_from,effective_to):


    # Create a connection string
    connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()

    query = f"SELECT COUNT(*) FROM {table_name} WHERE Center = ? AND Region = ? AND Task_List = ? AND Process = ? AND User_ID = ? AND Frequency = ? AND Deadline = ? AND Effective_from = ? AND Effective_to = ?"
    cursor.execute(query, center, region, task_List, process, user, frequency, deadline, effective_from, effective_to)
    if cursor.fetchone()[0] == 0:
        insert_query = f"INSERT INTO {table_name} (Center, Region, Task_List, Process, User_ID, Frequency, Deadline, Effective_from, Effective_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(insert_query, center, region, task_List, process, user, frequency, deadline, effective_from,
                       effective_to)
        connection.commit()
        cursor.close()
        connection.close()
        notification = 'Data uploaded successfully!'
        return notification
    else:
        cursor.close()
        connection.close()
        notification = 'Data already exists, not uploaded.'
        return notification


def task_status(user,starttime,endtime,center,region,process,task,frequency,status):

    cursor = connection.cursor()
    insert_query = f"INSERT INTO {raw_data_table} (User_ID, starttime, endtime, Center, Region, Process, Task_List, Frequency, Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    cursor.execute(insert_query, user, starttime, endtime, center, region, process, task, frequency,status)
    connection.commit()
    cursor.close()
    connection.close()
    notification = 'Data uploaded successfully!'
    return notification

@app.route('/')
@app.route('/home')
def hello_world():
    # put application's code here
    return render_template('Homepage.html', user= user)

@app.route('/Raw_Data_Downloader', methods=["POST","GET"])
def Raw_Data_Downloader():
    if request.method =="POST":
        user = request.form['user']
        StartDate = request.form['StartDate']
        EndDate = request.form['EndDate']
        return render_template('Raw_Data_Download.html') # ,user=user,StartDate = StartDate,EndDate = EndDate
    else:
        return render_template('Raw_Data_Download.html')


@app.route('/Task_List_Update', methods=["GET","POST"])
def Task_List_Update():
    if request.method == "POST":

        center = request.form['Center']
        region = request.form['Region']
        task_List = request.form['Task_List']
        process = request.form['Process_']
        frequency = request.form['Frequency']
        deadline = request.form['Deadline']
        effective_from = request.form['effective_from']
        effective_to = request.form['effective_to']
        note = update_Task(center, region, task_List, process, user, frequency, deadline, effective_from, effective_to)

        return render_template('Task_List_Update.html', notification=note, user= user)
    else:
        return render_template('Task_List_Update.html', notification="")


@app.route('/pending_task', methods=["POST","GET"])
def pending_task():
    if request.method == "Post":
        #selected_index = request.form.get('row_index')
        #selected_row = pending_checklist.iloc[selected_index]
        #user = selected_row['User_ID']
        #Center = selected_row['Center']
        ##Region = selected_row['Region']
        #Process = selected_row['Process']
        #Task = selected_row['Task_List']
        #Frequency = selected_row['Frequency']
        user = request.form['User_ID']
        Center = request.form['Center']
        Region = request.form['Region']
        Process = request.form['Process']
        Task = request.form['Task_List']
        Frequency = request.form['Frequency']


        print(user)
        print(Center)
        print(Region)
        print(Process)
        print(Task)
        print(Frequency)

        #session['user'] = user
        #session['Center'] = Center
        #session['Region'] = Region
        #session['Process'] = Process
        #session['Task'] = Task
        #session['Frequency'] = Frequency

        #return render_template('pendin_test.html', pending_checklist=pending_checklist)
        return redirect(url_for ('/activity_tracker',user=user,Center =Center, Region = Region,Process =  Process,Task = Task,Frequency= Frequency))
    else:
        return render_template('pendin_test.html', pending_checklist=pending_checklist)


@app.route('/activity_tracker', methods=["POST","GET"])
def activity_tracker():
    #user = session.get('user')
    #Center = session.get('Center')
    #Region = session.get('Region')
    #Process = session.get('Process')
    #Task = session.get('Task')
    #Frequency = session.get('Frequency')

    if request.method == "POST":
        starttime = request.form['starttime']
        endtime = request.form['endtime']
        Center = request.form['Center']
        Region = request.form['Region']
        Process= request.form['Process']
        Task = request.form['Task']
        Frequency = request.form['Frequency']
        Status = request.form['Status']
        note = task_status(user,starttime,endtime,Center,Region,Process,Task,Frequency,Status)
        return redirect(url_for('/pending_task'))

    else:

        return render_template('/activity_tracker',user=user,Center =Center, Region = Region,
                               Process =  Process,Task = Task, Frequency= Frequency)


if __name__ == '__main__':
    app.run()