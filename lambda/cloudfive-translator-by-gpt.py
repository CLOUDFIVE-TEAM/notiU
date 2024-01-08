from openai import OpenAI
import openai
import json
import os
import boto3
import time

openai_token = os.environ['OPENAI_TOKEN']

client = OpenAI(
    api_key=openai_token
)


class DatabaseAccess():
    def __init__(self, crawling_table):
        self.dynamodb = boto3.resource('dynamodb')
        self.crawling_table = self.dynamodb.Table(crawling_table)

    def get_crawlings(self, keys):
        response = self.dynamodb.batch_get_item(
            RequestItems={
                'inha-notice-posts': {
                    'Keys': keys
                }
            }
        )
        return response['Responses']['inha-notice-posts']

    def update_traslated_results_by_gpt(self, daily_article, article_eng):
        # 업데이트할 속성과 값을 지정
        update_expression = "SET articleTitleEng = :articleTitleEng, articleBodyEng = :articleBodyEng"

        expression_attribute_values = {
            ':articleTitleEng': article_eng.get('articleTitle', ''),
            ':articleBodyEng': article_eng.get('articleBody', '')
        }

        contentID = daily_article.get('contentID')
        date = daily_article.get('date')

        response = self.crawling_table.update_item(
            Key={
                'contentID': contentID,
                'date': date
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )


def translate_by_gpt(failure_article):
    global client
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are a helpful translator from Korean to English."},
            {"role": "user", "content": "you should translate sentenses in JSON format. "
                                        "There are two keys, 'articleTitle' and 'articleBody', "
                                        "and for each key, you should insert the result of translating Korean to English as the value."
                                        " The sentence to be translated is as follows:"
                                        + json.dumps(failure_article)
             }
        ],
        response_format={"type": "json_object"}
    )

    content_dict = json.loads(completion.choices[0].message.content)
    result = {
        'articleTitle': content_dict.get('articleTitle', ''),
        'articleBody': content_dict.get('articleBody', '')
    }
    return result


def lambda_handler(event, context):
    deeplTranslationResult = event["translationResultFromDeepl"]["Payload"]["body"]["failed_translations"]

    failed_translations = []
    success_translations_count = 0
    database = DatabaseAccess('inha-notice-posts')
    failure_articles = database.get_crawlings(deeplTranslationResult)

    for failure_article in failure_articles:
        try:
            article = list((failure_article.get('articleTitle', ''), failure_article.get('articleBody', '')))
            article_eng = translate_by_gpt(article)
            database.update_traslated_results_by_gpt(failure_article, article_eng)
            success_translations_count += 1
            time.sleep(20)  # 20초 동안 중지
        except openai.APIError as e:
            failed_translations.append({
                'contentID': failure_article.get('contentID'),
                'date': failure_article.get('date')
            })
            continue  # 오류가 발생해도 계속 다음 항목으로 진행합니다.

    return {
        'statusCode': 200,
        'body': {
            'success_translations_count': success_translations_count,
            'failed_translations': failed_translations
        }
    }
