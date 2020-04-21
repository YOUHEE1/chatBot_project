#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/python3
import re

import cv2
import telebot
import json
import time
import datetime
import requests
import emoji
import os
import urllib.request

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract


# 미세먼지 정보 가져오는 부분
def build_url(time, location):
    return f'http://openAPI.seoul.go.kr:8088/<KEY>/json/TimeAverageAirQuality/1/5/{time}/{location}'

def inform_finedust(time, location):
    re = requests.get(build_url(time, location))
    rjson = re.json()
    data = rjson['TimeAverageAirQuality']['row']

    for i in range(0, len(data)):
        return {"MEASURE_DATE":data[i]['MSRDT'], "DISTRICT":data[i]['MSRSTE_NM'], "PM10":str(data[i]['PM10']), "PM25":str(data[i]['PM25'])}

# telebot 연결
bot = telebot.TeleBot('TOKEN')

updates = bot.get_updates()
for i in updates:
    print(i)

# start 커맨드
@bot.message_handler(commands=['start'])
def help_command(message):
    print('TESt')
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton('네이버 날씨 보기', url='https://weather.naver.com/'))
    bot.send_message(message.chat.id,
       '1) 미세먼지 조회는'+''+ emoji.emojize(' :point_right: ', use_aliases=True)+'/dust\n' +
       '2) 사진 속 텍스트 번역은'+''+ emoji.emojize(' :point_right: ', use_aliases=True)+'/translate\n',
       reply_markup=keyboard)

####미세먼지 API
@bot.message_handler(commands=['dust'])
def location_command(message):
    district = [['강남구', '강동구', '강북구'],
                ['강서구', '관악구', '광진구'],
                ['구로구', '금천구', '노원구'],
                ['도봉구', '동대문구', '동작구'],
                ['마포구', '서대문구', '서초구'],
                ['성동구', '성북구', '송파구'],
                ['양천구', '영등포구', '용산구'],
                ['은평구', '종로구', ' 중구'],
                ['중랑구']]

    keyboard = telebot.types.InlineKeyboardMarkup()

    for district_name in district:
        if len(district_name) == 3:
            keyboard.add(telebot.types.InlineKeyboardButton(district_name[0], callback_data=district_name[0]),
                         telebot.types.InlineKeyboardButton(district_name[1], callback_data=district_name[1]),
                         telebot.types.InlineKeyboardButton(district_name[2], callback_data=district_name[2]))
        else:
            keyboard.add(telebot.types.InlineKeyboardButton(district_name[0], callback_data=district_name[0]))


    bot.send_message(
        message.chat.id, '' + emoji.emojize(':earth_asia: ', use_aliases=True) +
                         '조회할 구를 선택하세요 ' +
                         '' + emoji.emojize(':earth_asia: ', use_aliases=True), reply_markup=keyboard)



@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
    current_time = (datetime.datetime.today() - datetime.timedelta(hours=1)).strftime('%Y%m%d%H00')
    result_data = inform_finedust(current_time, query.data)
    bot.answer_callback_query(query.id)


    # 미세먼지 맑음 표시
    if float(result_data["PM10"]) <= 40.0:
        reply_data = result_data["MEASURE_DATE"][:4] + "년 " + result_data["MEASURE_DATE"][4:6] + "월 " + result_data["MEASURE_DATE"][6:8] + "일 " + result_data["MEASURE_DATE"][8:10] + "시 현재\n"
        reply_data += result_data["DISTRICT"] + " 대기상태 : " + emoji.emojize(':smile:\n', use_aliases=True) + '\n'
        reply_data += "미세먼지 : " + result_data["PM10"] + " \n"
        reply_data += "초미세먼지 : " + result_data["PM25"] + ""
    # 미세먼지 보통 표시
    elif 40.0 < float(result_data["PM10"]) <= 75.0:
        reply_data = result_data["MEASURE_DATE"][:4] + "년 " + result_data["MEASURE_DATE"][4:6] + "월 " + result_data["MEASURE_DATE"][6:8] + "일 " + result_data["MEASURE_DATE"][8:10] + "시 현재\n"
        reply_data += result_data["DISTRICT"] + "의 대기상태 : " + emoji.emojize(':open_mouth:\n', use_aliases=True) + '\n'
        reply_data += "미세먼지 : " + result_data["PM10"] + " \n"
        reply_data += "초미세먼지 : " + result_data["PM25"] + ""

    # 미세먼지 나쁨 표시
    elif float(result_data["PM10"]) < 75.0:
        reply_data = result_data["MEASURE_DATE"][:4] + "년 " + result_data["MEASURE_DATE"][4:6] + "월 " + result_data["MEASURE_DATE"][6:8] + "일 " + result_data["MEASURE_DATE"][8:10] + "시 현재\n"
        reply_data += result_data["DISTRICT"] + ":smile:의 대기상태 : " + emoji.emojize(':scream:\n', use_aliases=True) + '\n'
        reply_data += "미세먼지 : " + result_data["PM10"] + " \n"
        reply_data += "초미세먼지 : " + result_data["PM25"] + ""


    send_exchange_result(query.message, reply_data)

def send_exchange_result(message, reply_message):

    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(
    message.chat.id, reply_message, parse_mode='HTML')


########### 번역 ###########
@bot.message_handler(commands=['translate'])
def translate(message):
    set = [['/en', '/de'], ['/ja', '/zh-cn'], ['/es','/ko']]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)

    for i in set:
        if len(i) == 2:
            markup.row(i[0], i[1])
        else:
            markup.add(i[0])

    bot.send_message(message.chat.id,
                     ''+ emoji.emojize(':cherry_blossom: ', use_aliases=True) +
                     ' welcome to ' + '번역기' +
                     '' + emoji.emojize(' :cherry_blossom:\n', use_aliases=True) + '\n' +
                     '' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '번역할 언어를 선택해주세요',
                     reply_markup=markup)

    bot.send_message(message.chat.id,
                     '' + emoji.emojize(':gb:', use_aliases=True) + '-> KO : 한국어\n' +
                     '' + emoji.emojize(':gb:', use_aliases=True) + '-> EN : 영어\n' +
                     '' + emoji.emojize(':de:', use_aliases=True) + '-> DE : 독일어\n'+
                     '' + emoji.emojize(':ja:', use_aliases=True) + '-> JA : 일본어\n' +
                     '' + emoji.emojize(':es:', use_aliases=True) + '-> ES : 스페인어\n' +
                     '' + emoji.emojize(':cn:', use_aliases=True) + '-> zh-CN : 중국어 간체\n'
                     )

#선택 언어별 message_handler
@bot.message_handler(commands=['en'])
def send_welcome(message):
    bot.send_message(message.chat.id,'' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '텍스트가 포함된 사진을 보내주세요\n' )

    dir_now = os.path.dirname(os.path.abspath(__file__))
    @bot.message_handler(content_types=['photo'])
    #사진 저장
    def get_photo(message):
        tmp = message.json["photo"][0]
        file_path = os.path.join(dir_now, 'from_telegram.png')

        photo_id = tmp["file_id"]

        photo_file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        path = 'C:\\Users\\i\\Desktop\\photo\\' + "test.jpg"
        #path ='/home/ubuntu'+'test.jpg'
        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        print('PHOTO SAVED')

        #OCR : test.jpg
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        noise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(noise, lang='eng+kor')
        a = re.split('\n', text)
        text = " ".join(a)
        print(text)

        #NVER API request
        language = check_language(text)
        target = 'en'
        result = call_naver_api_papago_nmt(text, language, target)

        bot.send_message(message.chat.id, '추출 텍스트: \n' + text)
        bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['ja'])
def send_welcome(message):
    bot.send_message(message.chat.id,'' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '텍스트가 포함된 사진을 보내주세요\n' )

    dir_now = os.path.dirname(os.path.abspath(__file__))
    @bot.message_handler(content_types=['photo'])
    #사진 저장
    def get_photo(message):
        tmp = message.json["photo"][0]
        file_path = os.path.join(dir_now, 'from_telegram.png')

        photo_id = tmp["file_id"]
        photo_file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        path = 'C:\\Users\\i\\Desktop\\photo\\' + "test.jpg"
        #path ='/home/ubuntu'+'test.jpg'

        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        print('PHOTO SAVED')

        #OCR : test.jpg
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        noise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(noise, lang='eng+kor')
        #print('text: ', text)
        a = re.split('\n', text)
        text = " ".join(a)
        print(text)

        #NVER API request
        language = check_language(text)
        target = 'ja'
        result = call_naver_api_papago_nmt(text, language, target)

        bot.send_message(message.chat.id, '추출 텍스트: \n' + text)
        bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['de'])
def send_welcome(message):
    bot.send_message(message.chat.id,'' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '텍스트가 포함된 사진을 보내주세요\n' )

    dir_now = os.path.dirname(os.path.abspath(__file__))
    @bot.message_handler(content_types=['photo'])
    #사진 저장
    def get_photo(message):

        tmp = message.json["photo"][0]
        file_path = os.path.join(dir_now, 'from_telegram.png')
        photo_id = tmp["file_id"]
        photo_file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        path = 'C:\\Users\\i\\Desktop\\photo\\' + "test.jpg"
        #path ='/home/ubuntu'+'test.jpg'

        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        print('PHOTO SAVED')

        #OCR : test.jpg
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        noise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(noise, lang='eng+kor')
        a = re.split('\n', text)
        text = " ".join(a)
        print(text)

        #NVER API request
        language = check_language(text)
        target = 'de'
        result = call_naver_api_papago_nmt(text, language, target)

        bot.send_message(message.chat.id, '추출 텍스트: \n' + text)
        bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['es'])
def send_welcome(message):
    bot.send_message(message.chat.id,'' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '텍스트가 포함된 사진을 보내주세요\n' )

    dir_now = os.path.dirname(os.path.abspath(__file__))
    @bot.message_handler(content_types=['photo'])
    #사진 저장
    def get_photo(message):
        tmp = message.json["photo"][0]
        file_path = os.path.join(dir_now, 'from_telegram.png')
        photo_id = tmp["file_id"]
        photo_file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        path = 'C:\\Users\\i\\Desktop\\photo\\' + "test.jpg"
        #path ='/home/ubuntu'+'test.jpg'
        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        print('PHOTO SAVED')

        #OCR : test.jpg
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        noise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(noise, lang='eng+kor')
        a = re.split('\n', text)
        text = " ".join(a)
        print(text)

        #NVER API request
        language = check_language(text)
        target = 'es'
        result = call_naver_api_papago_nmt(text, language, target)

        bot.send_message(message.chat.id, '추출 텍스트: \n' + text)
        bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['zh-cn'])
def send_welcome(message):
    bot.send_message(message.chat.id,'' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '텍스트가 포함된 사진을 보내주세요\n' )

    dir_now = os.path.dirname(os.path.abspath(__file__))
    @bot.message_handler(content_types=['photo'])
    #사진 저장
    def get_photo(message):
        tmp = message.json["photo"][0]
        file_path = os.path.join(dir_now, 'from_telegram.png')

        photo_id = tmp["file_id"]

        photo_file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        path = 'C:\\Users\\i\\Desktop\\photo\\' + "test.jpg"
        #path ='/home/ubuntu'+'test.jpg'
        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        print('PHOTO SAVED')

        #OCR : test.jpg
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        noise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(noise, lang='eng+kor')
        a = re.split('\n', text)
        text = " ".join(a)
        print(text)

        #NVER API request
        language = check_language(text)
        target = 'zh-CN'
        result = call_naver_api_papago_nmt(text, language, target)

        bot.send_message(message.chat.id, '추출 텍스트: \n' + text)
        bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['ko'])
def send_welcome(message):
    bot.send_message(message.chat.id,'' + emoji.emojize(':heavy_exclamation_mark:', use_aliases=True) + '텍스트가 포함된 사진을 보내주세요\n' )

    dir_now = os.path.dirname(os.path.abspath(__file__))
    @bot.message_handler(content_types=['photo'])
    #사진 저장
    def get_photo(message):
        tmp = message.json["photo"][0]
        file_path = os.path.join(dir_now, 'from_telegram.png')

        photo_id = tmp["file_id"]

        photo_file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        path = 'C:\\Users\\i\\Desktop\\photo\\' + "test.jpg"
        #path ='/home/ubuntu'+'test.jpg'
        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        print('PHOTO SAVED')

        #OCR : test.jpg
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        noise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(noise, lang='eng+kor')
        a = re.split('\n', text)
        text = " ".join(a)
        print(text)

        #NVER API request
        language = check_language(text)
        target = 'ko'
        result = call_naver_api_papago_nmt(text, language, target)

        bot.send_message(message.chat.id, '추출 텍스트: \n'+ text)
        bot.send_message(message.chat.id, result)


def check_language(text):
    global langauge
    #문자열을 url용으로 인코딩
    encQuery = urllib.parse.quote(text)
    data = "query=" + encQuery

    #언어 감지 주소
    url = "https://openapi.naver.com/v1/papago/detectLangs"

    #인증정보추가
    check_lang_client_id = '<KEY>'
    check_lang_client_secret = '<KEY>'

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", check_lang_client_id)
    request.add_header("X-Naver-Client-Secret", check_lang_client_secret)
    try:
        # api 요청!
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        # 결과 코드 받기
        rescode = response.getcode()

        # 성공이면(200)
        if(rescode==200):
            response_body = json.loads(response.read())
            #print(response_body)

            language = response_body['langCode']
            return language
        else:
            print("Error Code:" + rescode)
    except urllib.error.HTTPError as e:
        #예외 처리!
        print(e.code)
        print(e.read())
    return None

def call_naver_api_papago_nmt(text, language, target):
    MyData = {'source': language, 'target': target, 'text': text.encode("utf-8")}
    url = "https://openapi.naver.com/v1/papago/n2mt"

    client_id = '<KEY>'
    client_secret = '<KEY>'

    MyHeader = {'X-Naver-Client-Id': client_id, 'X-Naver-Client-Secret': client_secret}
    response = requests.post(url, headers=MyHeader, data=MyData)
    rescode = response.status_code

    if (rescode == 200):
        response_body = response.json()
        # print(response_body) 값 확인
        # 번역 결과 출력
        result = response_body['message']['result']['translatedText']
        return result
    else:
        result = 'error 발생'
        return result

while True:
    try:
        bot.polling()
    except Exception:
        time.sleep(15)
