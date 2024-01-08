from slack_bolt import App
from urllib import parse
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta
import boto3
import json
import os
import base64

bot_token = os.environ['BOT_TOKEN']
user_token = os.environ['USER_TOKEN']
app = App(token=bot_token)

class DatabaseAccess():
    def __init__(self, crawling_table):
        self.dynamodb = boto3.resource('dynamodb')
        self.crawling_table = self.dynamodb.Table(crawling_table)

    def update_deadline(self, contentID, date, deadline):
        # 업데이트할 속성과 값을 지정
        update_expression = "SET deadline = :deadline"
        
        expression_attribute_value = {
            ':deadline': deadline
        } 
        
        response = self.crawling_table.update_item(
            Key={
                'contentID': contentID,
                'date' : date
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_value
        )
        
def set_slack_reminder(reminder_text, reminder_time, user_id):
    response = app.client.reminders_add(
        token=user_token,
        text=reminder_text,
        time=reminder_time,
        user=user_id
    )
    print(f"response : {response}")

    if response["ok"]:
        return{ "text" : response['reminder']['text'], "time" : response['reminder']['time'] }
    else:
        return{ "error" : response['error'] }

def reminder_click(value, user_id):
    # 이벤트 내용으로부터 리마인더 설정에 필요한 정보 구하기
    dict_data = value.split('[AND]')
    title = dict_data[0].replace('+',' ')
    deadline = dict_data[1]
    
    # (마감날짜-3) -> 유닉스 시간으로 변경
    days_ago_date = datetime.strptime(deadline, "%Y-%m-%d") - timedelta(days=3)
    unix_timestamp = int(days_ago_date.timestamp())
    
    # a = datetime(year=2023, month=12, day=28, hour=3, minute=35)
    # u = int(a.timestamp())
    # print(u)
    # set_slack_reminder(title, u, user_id)
    # 리마인더 생성
    set_slack_reminder(title, unix_timestamp, user_id)

def view(data):
    return {
        "type": "modal",
        "private_metadata" : f"{data[0]},{data[1]}",
        "submit": {
		    "type": "plain_text",
		    "text": "Submit",
		    "emoji": True
	    },
	    "close": {
		    "type": "plain_text",
		    "text": "Cancel",
		    "emoji": True
	    },
	    "title": {
		    "type": "plain_text",
		    "text": "마감기한 수정하기",
		    "emoji": True
	    },
	    "blocks": [
		    {
			    "type": "section",
			    "text": {
				    "type": "plain_text",
				    "text": f"contentID : {data[0]}, date : {data[1]}",
				    "emoji": True
			    }
		    },
		    {
			    "type": "divider"
		    },
		    {
			    "type": "input",
			    "label": {
				    "type": "plain_text",
				    "text": "마감기한 수정 날짜 (Format : yyyy-MM-dd)",
				    "emoji": True
			    },
			    "element": {
				    "type": "plain_text_input",
				    "multiline": False
			    },
			    "optional": True
		    }
	    ]
    }

def open_modals(body):
    article = body['actions'][0]['value']

    res = app.client.views_open(
        trigger_id=body["trigger_id"],
        view=view(article.split(","))
    )
    return {
        "statusCode" : 200
    }

def handle_view_submission(body):
    database = DatabaseAccess('inha-notice-posts')
    
    private_metadata = body['view']['private_metadata']
    block_id = body['view']['blocks'][2]['block_id']
    action_id = body['view']['blocks'][2]['element']['action_id']
    value = body['view']['state']['values'][block_id][action_id]['value']
    
    private_metadata = private_metadata.split(",")
    
    database.update_deadline(private_metadata[0], private_metadata[1], value)
    
    return {
        "statusCode" : 200 
    }
    
    
def lambda_handler(event, context):
    print("called")
    # 액션 이벤트 디코딩
    data = base64.b64decode(event['body']).decode("utf-8")
    data = parse.unquote(data, encoding="utf-8")
    data = data[8:]
    json_data = json.loads(data)
    print(f"JSONDATA: {json_data}")
    
    # 콜백 아이디와 유저 아이디 저장
    event_type = json_data['type']
    
    if event_type == "interactive_message":
        callback_id = json_data['callback_id']
        user_id = json_data['user']['id']
    
        print(f"callback_id: {callback_id}")
        # 이벤트 분기 처리
        if callback_id=='reminder_click':
            reminder_click(json_data['actions'][0]['value'], user_id)
        else:
            open_modals(json_data)
    else:
        handle_view_submission(json_data)
        
    # 슬랙으로 응답 전송
    return {
        'statusCode': 200
    }
