import os
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta
import deepl

deepl_api_token = os.environ['DEEPL_API_TOKEN']
initial_characters_translated = 0

class DatabaseAccess():
    def __init__(self, crawling_table):
        self.dynamodb = boto3.resource('dynamodb')
        self.crawling_table = self.dynamodb.Table(crawling_table)

    def get_crawlings(self, yesterday):
        response = self.crawling_table.scan(FilterExpression=Attr("date").eq(yesterday))
        return response['Items']

    def update_traslated_results(self, daily_article, articleTitleEng, articleBodyEng):
        # 업데이트할 속성과 값을 지정
        update_expression = "SET articleTitleEng = :articleTitleEng, articleBodyEng = :articleBodyEng"

        expression_attribute_values = {
            ':articleTitleEng': articleTitleEng,
            ':articleBodyEng': articleBodyEng
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


def calculateYesterday():
    today = datetime.now()
    yesterday = today  # UTC기준이라 해당 코드 - timedelta(days=1)
    yesterday = yesterday.strftime("%Y.%m.%d.")
    return yesterday


def decideTranslator(total_translation_length):
    global deepl_api_token, initial_characters_translated
    tokens = deepl_api_token.split(",")
    for token in tokens:
        translator = deepl.Translator(token)
        if translator.get_usage().character.count + total_translation_length <= 500_000:
            initial_characters_translated = translator.get_usage().character.count
            return translator
    return None


def lambda_handler(event, context):
    database = DatabaseAccess('inha-notice-posts')
    yesterday = calculateYesterday()

    daily_articles = database.get_crawlings(yesterday)
    daily_articles_count = len(daily_articles)
    total_translation_length = sum(
        len(article.get('articleTitle', '')) + len(article.get('articleBody', '')) for article in daily_articles)

    failed_translations = []
    success_translations_count = 0

    translator = decideTranslator(total_translation_length)

    # todo Null이면 ChatGPT 람다 호출
    if translator is None:
        for daily_article in daily_articles:
            failed_translations.append({
                'contentID': daily_article.get('contentID'),
                'date': daily_article.get('date')
            })
        return {
            'statusCode': 200,
            'body': {
                'crawling_date': yesterday,
                'daily_articles_count': daily_articles_count,
                'total_characters_translated': 0,
                'success_translations_count': success_translations_count,
                'failed_translations': failed_translations
            }
        }

    for daily_article in daily_articles:
        try:
            article = list((daily_article.get('articleTitle', ''), daily_article.get('articleBody', '')))
            result = translator.translate_text(article, target_lang='EN-US')

            articleTitleEng = result[0].text
            articleBodyEng = result[1].text

            database.update_traslated_results(daily_article, articleTitleEng, articleBodyEng)

            success_translations_count += 1
        except deepl.DeepLException as e:
            failed_translations.append({
                'contentID': daily_article.get('contentID'),
                'date': daily_article.get('date')
            })
            continue  # 오류가 발생해도 계속 다음 항목으로 진행합니다.

    usage = translator.get_usage().character

    if failed_translations:
        return {
            'statusCode': 200,
            'body': {
                'crawling_date': yesterday,
                'daily_articles_count': daily_articles_count,
                'total_characters_translated': usage.count - initial_characters_translated,
                'deepl_usage': str(usage),
                'success_translations_count': success_translations_count,
                'failed_translations': failed_translations
            }
        }
    else:
        return {
            'statusCode': 200,
            'body': {
                'crawling_date': yesterday,
                'daily_articles_count': daily_articles_count,
                'total_characters_translated': usage.count - initial_characters_translated,
                'deepl_usage': str(usage),
                'success_translations_count': success_translations_count
            }
        }
