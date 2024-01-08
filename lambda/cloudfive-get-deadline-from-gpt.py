import json
from openai import OpenAI
import re
import os
import boto3
import time
from datetime import datetime, timedelta

api_key = os.environ['API_KEY']
dynamodb_table = "inha-notice-posts"

class DatabaseAccess():
    def __init__(self):
        # DynamoDB 세팅
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(dynamodb_table)
    
    
    def update_deadline_data(self, contentID, date, deadline):
        self.table.update_item(
            Key={
                'contentID': contentID,
                'date': date
            },
            UpdateExpression='SET deadline = :val',
            ExpressionAttributeValues={
                ':val': deadline
            }
        )

    def get_yesterday_data(self, yesterday):
        response = self.table.scan(
            FilterExpression="#dt = :date_val",
            ExpressionAttributeNames={"#dt": "date"},
            ExpressionAttributeValues={":date_val": yesterday.strftime("%Y.%m.%d.")}
        )
        return response['Items']


def get_deadline_from_gpt(article_title, article_body):
    client = OpenAI(
        api_key=api_key
    )
    
    deadline_system_content = "You print out the deadline in 'YYYY-mm-DD' format if the notice I provide is related to the application and the deadline for application is indicated. Answer 'Yes, MM-dd' if the deadline exists, or 'NO' if it does not exist. 'YYYY-mm-DD' means year, month and day.  Your answer format is only 'Yes, YYYY-mm-DD' or' NO'"
    deadline_user_content = f"Is there a deadline for this notice? Here is the given Article:\\n articleTitle: {article_title} \\n articleBody: {article_body}"
    
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      messages=[
        {"role": "system", "content": deadline_system_content},
        {"role": "user", "content": deadline_user_content}
      ],
      temperature = 0,
    )
    
    answer = completion.choices[0].message.content
    
    pattern = r'\bYes\b.*?(\d{4}-\d{2}-\d{2})'  # "Yes" 다음에 오는 YYYY-mm-DD 형식의 날짜 패턴
    match = re.search(pattern, answer)
    
    if match:
        result = match.group(1)
        print(f"마감날짜 : {result}")
    else:
        result = None
        print("마감날짜가 존재하지 않습니다.")
        
    return result


def put_deadline():
    today = datetime.utcnow().date()
    yesterday = today# - timedelta(days=1)

    deadline_results = []
    db_access = DatabaseAccess()
    items = db_access.get_yesterday_data(yesterday)
    print(f"어제 데이터 : {items}")
    
    for item in items:
        article_title = item.get('articleTitle', '')
        article_body = item.get('articleBody', '')
        deadline = None
        
        if "마감" in article_body or "신청" in article_body or "지원" in article_body or "제출" in article_body:
            print(f"item : {item}")
            deadline = get_deadline_from_gpt(article_title, article_body)
            time.sleep(20)  # 20초 동안 중지
            
            if deadline is not None:
                # deadline 추가
                db_access.update_deadline_data(item['contentID'], item['date'], deadline)
                
        deadline_results.append({
                "article_title" : item['articleTitle'],
                "article_link" : item['articleLink'], 
                "contentID" : item['contentID'],
                "date" : item['date'],
                "deadline" : deadline
            })

    
    return deadline_results


def lambda_handler(event, context):
    #deadline을 dynamoDB에 저장
    results = put_deadline()
    
    return {
        'statusCode': 200,
        'body': {
            "DeadlineResults" : results
        }
    }
