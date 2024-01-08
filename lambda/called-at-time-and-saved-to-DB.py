import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import boto3
import json
import os
import logging
import datetime
from botocore.exceptions import ClientError

class DatabaseAccess():
    def __init__(self, TABLE_NAME):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(TABLE_NAME)
    
    def get_data(self):
        res = self.table.scan()
        items = res['Items']
        count = res['Count']
        return items, count
        
    def put_data(self, input_data):
        self.table.put_item(
            Item = input_data
        )
    
def send_sqs_message(sqs_queue_url, msg_body):
    # Send the SQS message
    sqs_client = boto3.client('sqs')
    try:
        msg = sqs_client.send_message(QueueUrl=sqs_queue_url,
                                      MessageBody=msg_body)
    except ClientError as e:
        logging.error(e)
        return None
    return msg
    
def school_notice():
    baseUrl = "https://www.inha.ac.kr"
    mainUrl = "https://www.inha.ac.kr/kr/950/subview.do"

    response = requests.get(mainUrl)

    if response.status_code == 200:
        #전날 올라온 공지만 크롤링하기
        now=datetime.datetime.now()
        now.year, now.month, now.day
        date_str = str(now.year) + "." + str(now.month).zfill(2) + "." + str(now.day).zfill(2) + "."
        
        html = response.text
        soup = BeautifulSoup(html,'html.parser')

        soup = soup.find('table', attrs={"class": "artclTable artclHorNum1"})
        soupTrList = soup.find_all("tr", attrs={"class" : ""})[1:]

        articles = []
        for soupTr in soupTrList :
            #작성날짜
            articleDate = soupTr.find("td", attrs={"class":"_artclTdRdate"}).get_text().replace("\n","")
            if articleDate < date_str : 
                break
                
            elif articleDate==date_str :
                #글 번호
                articleNum = soupTr.find("td", attrs={"class":"_artclTdNum"}).get_text().replace("\n","")
                
                #본문 링크
                articleLink = soupTr.find("td", attrs={"class":"_artclTdTitle"}).find("a", attrs={"class":"artclLinkView"})["href"]
                articleHtml = urlopen(baseUrl+articleLink) #본문 링크 타고 들어가서 내용 빼오기
                articleSoup = BeautifulSoup(articleHtml,'html.parser')
                
                #제목
                articleTitle = articleSoup.find("h2", attrs={"class":"artclViewTitle"}).get_text().strip()
                
                #작성날짜
                articleDate = soupTr.find("td", attrs={"class":"_artclTdRdate"}).get_text().replace("\n","")
                
                #본문 이미지 list
                imgs = articleSoup.find_all("img")
                articleImgs = []
                for img in imgs :
                    #배열에 저장
                    articleImgs.append(img["src"])
                    
                    #SQS에 보냄
                    value = {
                        'contentID' : articleNum,
                        'articleImg' : img["src"],
                        'date' : articleDate
                    }
                    msg_body = json.dumps(value)
                    msg = send_sqs_message(os.environ['SQS_QUEUE'], msg_body)
            
                #본문
                articleBody = articleSoup.find("div", attrs={"class":"artclView"}).get_text().replace("\n","").replace("\xa0"," ")
                
                #작성자
                articleWriter = soupTr.find("td", attrs={"class":"_artclTdWriter"}).get_text().replace("\n","").replace("\t","")
    
                article = {
                    "contentID" : articleNum,
                    "articleLink" : baseUrl + articleLink,
                    "articleTitle" : articleTitle,
                    "articleImgs" : articleImgs,
                    "articleBody" : articleBody,
                    "articleWriter" : articleWriter,
                    "date" : articleDate
                }
            
                # DynamoDB에 보냄
                db_access = DatabaseAccess('inha-notice-posts')
                db_access.put_data(article)
                    
    else :
        print(response.status_code)

    
def lambda_handler(event, context):
    school_notice()
