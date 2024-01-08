from slack_bolt import App
import json
import os

bot_token = os.environ['BOT_TOKEN']
app = App(token=bot_token)
failure = []


def make_deepl_translation_result(deeplTranslationResult):
    return {
        'mrkdwn_in': ['text'],
        'color': '#483D8B',
        'title': 'DeepL 번역 결과',
        'text': f"\n∙ 오늘 번역된  문자 수 : {deeplTranslationResult['total_characters_translated']}" \
                f"\n∙ DeepL 현재 사용량 : {deeplTranslationResult.get('deepl_usage', '')}" \
                f"\n∙ 번역 완료된 공지사항 개수 : {deeplTranslationResult['success_translations_count']}" \
                f"\n∙ 번역 실패한 공지사항 목록 : {str(deeplTranslationResult.get('failed_translations', '없음'))}"
    }


def make_chatGPT_translation_result(chatGPTTranslationResult):
    return {
        'mrkdwn_in': ['text'],
        'color': '#483D8B',
        'title': 'ChatGPT 번역 결과',
        'text': f"\n∙ 번역 완료된 공지사항 개수 : {chatGPTTranslationResult['success_translations_count']}" \
                f"\n∙ 최종 번역 실패한 공지사항 목록 : {str(chatGPTTranslationResult.get('failed_translations', '없음'))}"
    }


def make_deadline_result(deadlineResult):
    return {
        'color': '#483D8B',
        'text': f"<{deadlineResult['article_link']}|{deadlineResult['article_title']}>\ncontentID : {deadlineResult['contentID']}, date : {deadlineResult['date']}",
        'callback_id': 'modify_deadline',
        'actions': [
            {
                'name': '마감날짜',
                'type': 'button',
                'text': f"마감날짜 : {deadlineResult.get('deadline', '마감기한 없음')}",
                'url': deadlineResult['article_link']
            },
            {
                'name': '마감날짜 수정',
                'type': 'button',
                'text': "마감날짜 수정하기",
                'action_id': 'modify_deadline',
                'value': f"{deadlineResult['contentID']},{deadlineResult['date']}"
            }
        ]
    }


def send_dm_to_admin(deeplTranslationResult, chatGPTTranslationResult, deadlineResults):
    messages = []
    messages.append(make_deepl_translation_result(deeplTranslationResult))
    chatgpt_translation_count = 0

    if chatGPTTranslationResult:
        messages.append(make_chatGPT_translation_result(chatGPTTranslationResult))
        chatgpt_translation_count += chatGPTTranslationResult['success_translations_count']

    for deadlineResult in deadlineResults:
        print(deadlineResult)
        messages.append(make_deadline_result(deadlineResult))

    app.client.chat_postMessage(
        channel=admin_channel,
        text=f'*📝번역 결과*\n=> 업로드 된 공지사항 개수 : *{deeplTranslationResult["daily_articles_count"]}*, 번역 완료된 공지사항 개수 : *{deeplTranslationResult["success_translations_count"] + chatgpt_translation_count}*\n',
        attachments=json.dumps(messages)
    )


def lambda_handler(event, context):
    deeplTranslationResult = event["deeplTranslationResult"]["Payload"][
        "body"] if 'deeplTranslationResult' in event else None
    chatGPTTranslationResult = event["deeplTranslationResult"]["ChatGPTTranslationResult"]["Payload"][
        "body"] if 'deeplTranslationResult' in event and 'ChatGPTTranslationResult' in event[
        "deeplTranslationResult"] else None
    deadlineResults = event["deeplTranslationResult"]["DeadLineResult"]["Payload"]["body"][
        "DeadlineResults"] if 'deeplTranslationResult' in event and 'DeadLineResult' in event[
        "deeplTranslationResult"] else None

    send_dm_to_admin(deeplTranslationResult, chatGPTTranslationResult, deadlineResults)

    return {"statusCode": 200, "body": {
        "d": event["deeplTranslationResult"],
        "c": event["deeplTranslationResult"]["Payload"]["body"],
        "a": event["deeplTranslationResult"]["Payload"]["body"]["total_characters_translated"]
    }}
