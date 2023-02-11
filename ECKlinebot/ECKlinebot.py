from __future__ import unicode_literals
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import datetime
import json
import pandas as pd


app = Flask(__name__)

# LINE 聊天機器人的基本資料
line_bot_api = LineBotApi('4YkIpvd31wX4BeYY8wYo6PkW+jwICu+c3PbqN4aNMbg2BqHXy1UKVJEENIqNOB9kLZ17fhunp+P40247zrIBH8BJPNiXzHpV+IJlKlg22Axtm1ixpanngFKm7fB+ppkQcJB+l/ayfPwYG+S2cbBrcwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('567ac1865b2d6aa4a2e2b13bc390c2c4')

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# 爬蟲的部分

def cal_age(Birthday):
  now = datetime.datetime.now()
  now.strftime("%Y/%m/%d")
  Birthday = datetime.datetime.strptime(Birthday, "%Y/%m/%d")
  age = now.year - Birthday.year
  # print(age)
  return age

# 取得當下時間 
datetime_format = datetime.datetime.today().strftime("%Y/%m/%d %H:%M")

header = {
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
'Cookie': 'IsLogin=IsLogin',
'Authorization': 'Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJVc2VySUQiOiIwMjAwMyIsIlVzZXJOYW1lIjoi6Zmz54eB5pmoIiwiU3RhZmZLZXkiOiIwMjAwM1x1MDAyNumZs-eHgeaZqCIsIlBlcm1pc3Npb24iOiJSZW9wZW5DYXNlQW55UmVjb3JkLCBWaWV3QW55UmVjb3JkLCBFZGl0QW55UmVjb3JkLCBEZWxldGVBbnlSZWNvcmQifQ.jEXzWvmsbaBmzyZav10kAzkQKSnFaiVBY9NhPQiUvEVRqfjDKna--cIQwrBLYQl0WRvuzlCnQsIyQlKiKT03-g'
}

  
def pat_info(ChartNo):# 取得病人基本資料
    payload = {
    'ChartNo': ChartNo, # "0009370516" 測試用，之後要改成變數CharNo
    'QueryDate': datetime_format
    }
    pat_info = requests.post('http://172.20.110.161/ECK_AIM_WEB/ShareComponent/GetHISPatientInfo', headers = header, data = payload)
    pat_info = json.loads(pat_info.text)
    PatientName = pat_info["PatientName"]
    Sex = pat_info["Sex"]
    Birthday = pat_info["Birthday"]
    try:
        Hieght = pat_info["Height"]
        Weight = pat_info["Weight"]
    except:
        Hieght = "NaN"
        Weight = "NaN"
    PatientInfo = {"PatientInfo": [PatientName, Sex, Birthday, cal_age(Birthday), Hieght, Weight]}
    PatientInfo = pd.DataFrame(PatientInfo)
    PatientInfo.index = ["PatientName", "Sex", "Birthday", "Age", "Hieght", "Weight"]
    # print(PatientInfo)
    return PatientInfo

def get_data(ChartNo):
    payload = {
    'ChartNo': ChartNo, # "0009370516" 測試用，之後要改成變數CharNo
    'QueryDate': datetime_format
    }
    blood_check = requests.post('http://172.20.110.161/ECK_AIM_WEB/PinPin/PIN/GetBloodCheckViewModel', headers = header, data = payload)
    blood_check = json.loads(blood_check.text)
    bioChem_check = requests.post('http://172.20.110.161/ECK_AIM_WEB/PinPin/PIN/GetBiochemistryCheckViewModel', headers = header, data = payload)
    bioChem_check = json.loads(bioChem_check.text)
    blood_check_df = pd.DataFrame(blood_check)
    bioChem_check_df = pd.DataFrame(bioChem_check)
    df = pd.concat([blood_check_df, bioChem_check_df], ignore_index=True)
    # print(df['LabDataList'])
    LabData_df = []
    for i in df['LabDataList']:
        if i['IsNormal'] == True:
            data = [i['ItemName'],i['ItemValue'],i['CheckDate']]
            LabData_df.append(data)
        else:
            data = [i['ItemName'],"*"+i['ItemValue'],i['CheckDate']]
            LabData_df.append(data)
    LabData_df = pd.DataFrame(LabData_df)
    LabData_df.columns = ["ItemName", "ItemValue", "CheckDate"]
    # LabData_df.set_index("ItemName", inplace=True)
    # LabData_df.columns = ["ItemValue", "CheckDate"]
    # print(LabData_df)

    df_c = LabData_df[(LabData_df["ItemName"]=="GPT (ALT)")|(LabData_df["ItemName"]=="Creatinine")|(LabData_df["ItemName"]=="K")|(LabData_df["ItemName"]=="Hb")|(LabData_df["ItemName"]=="Platelet")|(LabData_df["ItemName"]=="PT")|(LabData_df["ItemName"]=="APTT")]
    df_c.reset_index(inplace = True, drop = True)
    df_c.set_index("ItemName", inplace=True)
    # print(df_c)

    df1 = {"column": [0,0,0,0,0,0,0]}
    df1 = pd.DataFrame(df1)
    df1.index = ["GPT (ALT)", "Creatinine", "K", "Hb", "Platelet", "PT", "APTT"]

    DF = pd.concat([df1, df_c], axis=1)
    DF = DF.drop(["column"], axis = 1)
    # print(DF)
    return DF

    LabData_df.set_index("ItemName", inplace=True)
    # print(LabData_df)

# 爬蟲的部分


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    ChartNo = event.message.text
    ChartNo = ChartNo.zfill(10)
    # print(pat_info(ChartNo)["PatientInfo"])
    # print(get_data(ChartNo)["ItemValue"])
    info_content = ""
    data_content = ""
    for i in pat_info(ChartNo).loc[:, ["PatientInfo"]]:
        info_content += f'{pat_info(ChartNo)}\n'
    for j in get_data(ChartNo).loc[:, ["ItemValue"]]:
        data_content += f'{get_data(ChartNo)["ItemValue"]}\n'
    # print(info_content)
    # print(data_content)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text = info_content + data_content))

if __name__ == "__main__":
    app.run()