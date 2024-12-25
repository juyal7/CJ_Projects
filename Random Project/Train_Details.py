import requests
from datetime import datetime

class IRCTC:
    def __init__(self):
        user_input=input("""Please select one of the following options
                         1- Enter 1 for checking Live train status
                         2- Enter 2 for checking PNR
                         3- Enter 3 for checking train schedule
""")
        if user_input == "1":
            print("You have selected to check Live train status")
            self.Live_train_status()
        elif user_input == "2":
            print("checking PNR")
        else:
            self.tarin_schedule()
    def Live_train_status(self):
            train_number=input("Please enter the train number=")
            Schedule_date=input("Please enter the date in YYYYMMDD=")
            get_status=requests.get(f"https://indianrailapi.com/api/v2/livetrainstatus/apikey/4169fa39d9e8ac65b6f0006538388a9e/trainnumber/{train_number}/date/{Schedule_date}/").json()
            print(get_status)
    def tarin_schedule(self):
        train_no = input("Enter train number=")
        self.fetch_data(train_no)
        
    def fetch_data(self,train_no):
        data=requests.get(f"https://indianrailapi.com/api/v2/TrainSchedule/apikey/4169fa39d9e8ac65b6f0006538388a9e/TrainNumber/{train_no}")
        data=data.json()
        for i in data["Route"]:
            print(f"{i["StationName"]} || {i["ArrivalTime"]} || {i["DepartureTime"]} || {i["Distance"]} ")

obj1=IRCTC()
