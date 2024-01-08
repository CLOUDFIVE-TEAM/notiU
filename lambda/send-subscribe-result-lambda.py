from slack_bolt import App
from openai import OpenAI
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta
import json
import os


bot_token = os.environ['BOT_TOKEN']
gpt_model = os.environ['GPT_MODEL']
app = App(token=bot_token)
failure = []
client = OpenAI(
    api_key=os.environ['API_KEY']
)

class DatabaseAccess():
    def __init__(self, crawling_table, keyword_table, keyword_eng_table):
        self.dynamodb = boto3.resource('dynamodb')
        self.crawling_table = self.dynamodb.Table(crawling_table)
        self.keyword_table = self.dynamodb.Table(keyword_table)
        self.keyword_eng_table = self.dynamodb.Table(keyword_eng_table)

    def get_subscribers(self):
        response = self.keyword_table.scan()
        return response['Items']
    
    def get_subscribers_eng(self):
        response = self.keyword_eng_table.scan()
        return response['Items']

    def contains_keyword_in_text(keyword, *texts):
        return any(keyword in text for text in texts)

    def get_crawlings(self, yesterday):
        response = self.crawling_table.scan(FilterExpression=Attr("date").eq(yesterday))
        return response['Items']
        

class BotServiceByLanguage() :
    def __init__(self, language):
        self.language = language

    def get_result(self, keyword) :
        if self.language == 'kor' :
            return f"\n*📌 키워드 : {keyword}*\n"
        elif self.language == 'eng' :
            return f"\n*📌 keyword : {keyword}*\n"

    def msg_no_articles(self) :
        if self.language == 'kor' :
            return "오늘은 관련 내용이 없습니다.\n"
        elif self.language == 'eng' :
            return "There are no related notices today.\n"
    
    def create_message(self, article):
        article_link = article['articleLink']
        text = ''
        reminder_text = ''
        if self.language == 'kor' :
            text = '🌐 글 보러가기'
            reminder_text = '🗓️ 3일 전 리마인더 생성'
            article_title = article['articleTitle']
        elif self.language == 'eng' :
            text = '🌐 Check the article'
            reminder_text = '🗓️ Create a reminder 3 days ago'
            article_title = article['articleTitleEng']
        
        if ('deadline' in article) and (article['deadline']):
            deadline = article['deadline']
            return {
                'color': '#8CC7F0',
                'text': f"<{article_link}|{article_title}>",
                'callback_id': 'reminder_click',
                "attachment_type": "default",
                "actions": [
                    {
                        "name": "url_button",
                        "text": text,
                        "type": "button",
                        "url": article_link
                    },
                    {
                        "name": "reminder_button",
                        "text": reminder_text,
                        "type": "button",
                        "value": f"{article_title}[AND]{deadline}",
                    }
                ]
            }
        
        else:
            return {
                'color': '#8CC7F0',
                'text': f"<{article_link}|{article_title}>",
                'actions': [
                    {
                        'type': 'button',
                        'text': text,
                        'url': article_link
                    }
                ]
            }
        
        
def make_result(total_count, message_count,failure_text):
    if len(failure_text) == 0:
        failure_text = '없음'
    return {
        'mrkdwn_in': ['text'],
        'color': '#483D8B',
        'title' : '알림 전송 결과',
        'text': f"\n∙ 전송해야할 알림 개수 : {total_count}" \
             f"\n∙ 전송 성공 개수 : {message_count}" \
             f"\n∙ 전송 실패 원인 : {failure_text}"
    }
    
def send_dm_to_admin(daily_articles_count, total_count, message_count):
    failure_text = '\n'.join(failure)
    messages = []
    messages.append(make_result(total_count, message_count,failure_text))
    app.client.chat_postMessage(
        channel=admin_channel,
        text=f"📢어제 올라온 공지사항 개수 : *{daily_articles_count}*\n",
        attachments=json.dumps(messages)
    )

def send_dm_to_users(subscriber, articles, language):
    global app, failure

    botService = BotServiceByLanguage(language) # kor, eng 언어 지정
    success_count = 0
    keyword = subscriber.get('keyword')
    user_ids = subscriber.get('user_ids')
        
    result = botService.get_result(keyword)
    
    message_strings = []
    if articles:
        for article in articles:
            message = botService.create_message(article)
            message_strings.append(message)
    else:
        result += botService.msg_no_articles()
    for user_id in user_ids:
        try:
            response = app.client.chat_postMessage(
                channel=user_id,
                text=result,
                attachments=json.dumps(message_strings)
            )
            if response.get('ok'):
                success_count += 1
        except Exception as e:
            failure.append(f"Failure Keyword : {keyword}, UserId : {user_id}")
    return success_count


def calculateYesterday():
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    yesterday = yesterday.strftime("%Y.%m.%d.")
    return yesterday

def check_context(daily_article, keyword) :
    article_title_kr = daily_article.get('articleTitle', '')
    article_body_kr = daily_article.get('articleBody', '')
    article_title_eng =  daily_article.get('articleTitleEng', '')
    article_body_eng = daily_article.get('articleBodyEng', '')
    
    article_list = [
        {"article_title": article_title_kr, "article_body": article_body_kr},
        {"article_title": article_title_eng, "article_body": article_body_eng}]

    result = False
    
    for article in article_list:
      system_content = "I wonder if anyone interested in a particular keyword will be interested in any university notice article. To do this, you should check whether the given keyword and the given university notice article are related. I will provide you with a 'university notice article' and a 'keyword.' Then answer 'YES' if you think it's related, or 'NO' if you think it's not. In other words, you can answer my question in the form of 'YES or NO'. Please do not give me any other answers. Here, the association should be related to the corresponding text by the person who is interested in the word, beyond simply being included in the text. For example, when a notice is given that includes the keyword 'graduation' and the sentence 'Application Eligibility: Graduation(scheduled), completion of 4 or more semesters(rest of students),' those who are interested in the keyword will be interested in the corresponding article. Therefore, there will be a connection between the keyword and the writing. However, when a notice is given that includes the keyword 'graduation' and the sentence 'No application for graduation(scheduled) candidates,' there will be no connection because those who are interested in the keyword 'graduation' will not be interested in the corresponding article."
      user_content = f"Are articles and words relevant? \\n Here is the given Article:\\n articleTitle: {article['article_title']}\\n articleBody: {article['article_body']} \\n Here is the customer keyword: {keyword}"
    
      stream = client.chat.completions.create(
          model=gpt_model,
          messages=[
              {"role": "system", "content": system_content},
              {"role": "user", "content": user_content}],
          stream=True,
      )
    
      for chunk in stream:
          if chunk.choices[0].delta.content is not None:
              answer = chunk.choices[0].delta.content
              if answer == "YES":
                result = True
                break
      if result:
        break
    
    return result
    
def extract_articles_by_keyword(daily_articles, keyword):
    extracted_articles_by_keyword = []

    for daily_article in daily_articles:
        article_imgs_texts = daily_article.get('articleImgsTextData', [])
        
        if check_context(daily_article, keyword) :
            extracted_articles_by_keyword.append(daily_article)
        elif any(keyword in img_texts for img_texts in article_imgs_texts):
            extracted_articles_by_keyword.append(daily_article)

    return extracted_articles_by_keyword


def lambda_handler(event, context):
    global failure
    failure = []
    
    database = DatabaseAccess('inha-notice-posts', 'subscribe_bot_db', 'subscribe_bot_eng_db')
    # 키워드 별로 구독한 userId 정보 가져오기
    subscribers = database.get_subscribers() # 한글 구독 정보
    subscribers_eng =database.get_subscribers_eng() # 영어 구독 정보
    print(subscribers)
    print(subscribers_eng)
    
    # 보내야할 메세지 개수 체크 -> 관리자 전송용
    # todo 영어 count 추가 필요
    total_count = sum(len(subscriber.get('user_ids')) for subscriber in subscribers) + sum(len(subscriber.get('user_ids')) for subscriber in subscribers_eng)
    
    # 날짜계산
    yesterday = calculateYesterday()
    
    # 어제 업로드된 공지사항 가져오기
    daily_articles = database.get_crawlings(yesterday)
    
    message_count = 0
    # 어제 공지사항 개수 세는 변수 -> 관리자 전송용
    daily_articles_count = len(daily_articles)
    
    # subscriber 형태 {"keyword" : keyword, "userIds" : []} 이런 형태
    for subscriber in subscribers:
        # 공지사항과 키워드를 전달해 contains 로 관련있는지 체크하는 부분
        extracted_articles = extract_articles_by_keyword(daily_articles, subscriber.get("keyword"))
        
        # 관련있는 공지사항만 유저에게 전송
        message_count += send_dm_to_users(subscriber, extracted_articles, 'kor')


    # subscriber 형태 {"keyword" : keyword, "userIds" : []} 이런 형태
    for subscriber in subscribers_eng:
        # 공지사항과 키워드를 전달해 contains 로 관련있는지 체크하는 부분
        extracted_articles = extract_articles_by_keyword(daily_articles, subscriber.get("keyword"))
        
        # 관련있는 공지사항만 유저에게 전송
        message_count += send_dm_to_users(subscriber, extracted_articles, 'eng')
    
    #todo 최종 결과 관리자에게 전송 -> 영어 키워드 결과도 전송하려면 수정 필요
    send_dm_to_admin(daily_articles_count, total_count, message_count)

    return {"statusCode": 200, "body": "Message Succeful!"}
