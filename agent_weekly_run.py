# import os 
# import pandas as pd 
# import schedule 
# import time 
# import yagmail 
# import traceback 
# from preprocess import build_model_input
# from optimiser import solve_week


# #✉️ set up 
# SENDER_EMAIL = "email address"
# APP_PASSWORD = "password" #use gmail 
# RECEIVER_EMAIL = "recipient email"

# def send_email(subject, body, attachement = None): 
#     yag = yagmail.SMTP(SENDER_EMAIL, APP_PASSWORD)
#     if attachement: 
#         yag.send(to=RECEIVER_EMAIL, subject = subject, contents = body, attachements = attachement)
#     else: 
#         yag.send(to=RECEIVER_EMAIL, subject = subject, contents = body)
        

# def run_agent(): 
#     print("Robot is waking up!")
    
#     try: 
#         #check if both csvs exist 
#         if not (os.path.exists("data/forests.csv") and os.path.exists("data/trucks.csv")): 
#             send_email(
#                 subject = "Please upload your weekly CSVs for truck allocation and profitability maximisation"
#                 body = "Hi your optimization AI agent is ready, pls make sure both forests.csv and trucks.csv are in data folder"
#             )
#             print("Missing files - reminder sent!")
#             return 
        
#         #run optimization 
#         df = build_model_input(
#             forests_csv = "data/forests.csv",
#             trucks_csv = "data/trucks_csv",
#             season = "dry" #change to make it dynamic 
#         )
#         plan = solve_week(df)
        
#         #save result 
#         output_path = "results/weekly_plan.csv"
#         os.makedirs("results", exist_ok= True)
#         plan.to_csv(output_path, index = False)
        
#         #send the report 
#         send_email(
#             subject ="📈 Weekly truck-forest optimization report", 
#             body = "Here's the latest allocation plan for your review",
#             attachement= output_path
#         )
#         print("report generated and emailed")
        
