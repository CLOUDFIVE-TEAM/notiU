import json
import base64
from urllib.parse import parse_qs, unquote
from urllib import request
import boto3
import os
from collections import Counter
from slack_bolt import App
 
bot_token = os.environ['BOT_TOKEN']
dynamodb_table_kor = "subscribe_bot_db"
dynamodb_table_eng = "subscribe_bot_eng_db"

class DatabaseAccess():
    def __init__(self, TABLE_NAME):
        # DynamoDB 세팅
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(TABLE_NAME)
    
    def put_data(self, input_data):
        self.table.put_item(
            Item = input_data
        )
        print("Putting data is completed!")
    
    def update_data(self, keyword, user_ids):
        # 업데이트된 데이터를 DynamoDB에 반영
        self.table.update_item(
            Key={'keyword': keyword},
            UpdateExpression='SET user_ids = :new_user_ids',
            ExpressionAttributeValues={
                ':new_user_ids': user_ids
            }
        )

    def get_data(self, keyword):
        # DynamoDB에서 해당 keyword를 가진 데이터 조회
        response = self.table.get_item(Key={'keyword': keyword})
        item = response.get('Item')
        return item
        
    def delete_item(self, keyword):
        self.table.delete_item(Key={'keyword': keyword})

    def get_all_item(self):
        response = self.table.scan()
        return response['Items']

class BotService():
    def __init__(self, LANGUAGE):
        if LANGUAGE == "kor" :
            self.db = DatabaseAccess(dynamodb_table_kor)
        elif LANGUAGE == "eng" :
            self.db = DatabaseAccess(dynamodb_table_eng)
        self.lan = LANGUAGE
    
    def put_data(self, keyword):
        self.db.put_data(keyword)
        
    def update_data(self, keyword, user_ids):
        self.db.update_data(keyword, user_ids)
    
    def get_data(self, keyword):
        return self.db.get_data(keyword)
    
    def delete_item(self, keyword):
        self.db.delete_item(keyword)
    
    def get_all_item(self):
        return self.db.get_all_item()
        
    def msg_success_subscribe(self):
        if self.lan == 'kor' :
            return "구독에 성공했습니다."
        elif self.lan == 'eng' :
            return "is subscribed successfully"
            
    def msg_error_subscribe_no_item(self):
        if self.lan == 'kor' :
            return "구독할 항목을 입력해주세요!"
        elif self.lan == 'eng' :
            return "Please enter the keyword to subscribe !"
            
    def msg_error_unsubscribe_no_item(self):
        if self.lan == 'kor' :
            return "구독취소할 항목을 입력해주세요!"
        elif self.lan == 'eng' :
            return "Please enter the keyword to unsubscribe !"
            
    def msg_success_unsubscribe(self):
        if self.lan == 'kor' :
            return "구독을 취소했습니다."
        elif self.lan == 'eng' :
            return "is unsubscribed successfully"
    
    def msg_no_keyword_exist(self):
        if self.lan == 'kor' :
            return "해당 키워드를 구독하지 않았습니다."
        elif self.lan == 'eng' :
            return "You havn't subscribed to this keyword."
    
    def msg_success_keyword_list(self, user_id):
        if self.lan == 'kor' :
            return f"<@{user_id}>님이 구독한 키워드 리스트\n"
        elif self.lan == 'eng' :
            return f"<@{user_id}>'s list of subscribed keywords\n"
    
def lambda_handler(event, context):
    # Slack 이벤트 데이터 파싱
    body = event['body']
    print(f"Received body: {body}")
    if 'isBase64Encoded' in event and event['isBase64Encoded']:
        code_bytes = body.encode('ascii')
        decoded = base64.b64decode(code_bytes)
        body = decoded.decode('UTF-8')
    print(f"Received decoded body: {body}")

    # '&'를 기준으로 문자열을 나누고 '='를 기준으로 key-value 쌍으로 분할하여 딕셔너리 생성
    data = {}
    key_value_pairs = body.split('&')
    for pair in key_value_pairs:
        key, value = pair.split('=')
        data[key] = unquote(value)  # URL 디코딩
    body = data

    print(f"Parsed body: {body}")
    
    user_id = body['user_id']
    if 'command' in body and (body['command'] == '/탐색' or body['command'] == '/explore') :
        return get_keywords(user_id)
        
    elif 'command' in body and (body['command'] == '/도움' or body['command'] == '/help') :
        db_access =  BotService('kor') if body['command'] == '/도움' else BotService('eng')
        return get_top_5_keywords(db_access)
  
    
    # 메시지 이벤트 처리
    if 'command' in body and (body['command'] == '/구독' or body['command'] == '/subscribe'):
        db_access = BotService('kor') if body['command'] == '/구독' else BotService('eng')
        
        if 'text' in body and len(body['text']) > 0:
            keyword = body['text']
            return save_info(keyword, user_id, db_access)
        else:
            return {
                "statusCode" : 200,
                "body" : db_access.msg_error_subscribe_no_item()
            }
    elif 'command' in body and (body['command'] == '/구독취소' or body['command'] == '/unsubscribe') :
        db_access = BotService('kor') if body['command'] == '/구독취소' else BotService('eng')
        
        if 'text' in body and len(body['text']) > 0:
            keyword = body['text']
            return delete_info(keyword, user_id, db_access)
        else:
            return {
                "statusCode" : 200,
                "body" :  db_access.msg_error_unsubscribe_no_item()
            }
  
    return {
        "statusCode" : 500,
        "body" : "오류가 발생했습니다."
    }



def save_info(keyword, user_id, db_access):
    print("키워드 구독")
    item = db_access.get_data(keyword)
    
    if not item:
        print("키워드가 존재하지 않습니다.")
        # 키워드가 존재하지 않는 경우: 새로운 아이템 생성
        item_data = {
            'keyword': keyword,
            'user_ids': [user_id],
        }
        db_access.put_data(item_data)
    else:
        print("키워드가 이미 존재합니다.")
        # 키워드가 이미 존재하는 경우: user_ids 업데이트
        user_ids = item.get('user_ids', [])
        print(f"기존 user_ids : {user_ids}")
        # 중복을 제외한 새로운 user_ids 추가
        if user_id not in user_ids:
            user_ids.append(user_id)
        
        print(f"새로운 user_ids : {user_ids}")
        db_access.update_data(keyword, user_ids)
    
    return {
        "statusCode" : 200,
        "body" : f"\"{keyword}\" " + db_access.msg_success_subscribe()
    }
    

def delete_info(keyword, user_id, db_access):
    print("키워드 구독취소")
        
    item = db_access.get_data(keyword)
    
    if not item:
        return {
            "statusCode" : 200,
            "body" : db_access.msg_no_keyword_exist()
        }
    else:
        user_ids = item.get('user_ids', [])
        # user_id_to_delete를 user_ids에서 제외
        if user_id in user_ids:
            if len(user_ids) == 1:
                print(f"deleted keyword : {keyword}")
                db_access.delete_item(keyword)
            else:
                user_ids.remove(user_id)
                # DynamoDB 항목 업데이트
                db_access.update_data(keyword, user_ids)
        else:
            return {
                "statusCode" : 200,
                "body" : db_access.msg_no_keyword_exist()
            }

    return {
        "statusCode" : 200,
        "body" : f"\"{keyword}\" " + db_access.msg_success_unsubscribe()
    }

def get_keywords(user_id):
    print(f"{user_id}의 전체 키워드 탐색")
    
    db_access = BotService('kor')
    db_eng_access = BotService('eng')
    try:
        items = db_access.get_all_item()
        items_eng = db_eng_access.get_all_item()
        print(f"전체 아이템 : {items}")
        # 선택한 user_id를 포함하는 keyword 찾기
        keywords = []
        for item in items:
            user_ids = item.get('user_ids', [])  # user_ids 배열 가져오기
            if user_id in user_ids:
                keywords.append(item['keyword'])
        
        keywords_eng = [] 
        for item in items_eng:
            user_ids = item.get('user_ids', [])
            if user_id in user_ids:
                keywords_eng.append(item['keyword'])
        
        print(f"구독한 키워드 : {keywords}")
        print(f"구독한 키워드 : {keywords_eng}")
        
        body = ""
        if len(keywords) > 0 :
            body += db_access.msg_success_keyword_list(user_id) + f"{keywords}\n"
        if len(keywords_eng) > 0 :
            body += db_eng_access.msg_success_keyword_list(user_id) + f"{keywords_eng}"
        
        return {
            'statusCode': 200,
            'body': body
        }
    except Exception as e:
        print(f"키워드 탐색 에러 : {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
        
#written by hyunjun
#도움 이벤트 제작
def get_top_5_keywords(db_access):
    try:
        items = db_access.get_all_item()
        
        # 각 키워드별 user_ids 개수 세기
        count_user_ids = {item.get('keyword'): len(item.get('user_ids', [])) for item in items}
        
        # user_ids 개수가 많은 순서대로 다섯 개 키워드 추출
        top_five_keywords = dict(Counter(count_user_ids).most_common(5))

        return {"statusCode": 200, "body": ', '.join(list(top_five_keywords.keys()))}
    except Exception as e:
        print(f"도움 에러 : {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
        
