

# <img width=30px src="https://github.com/CLOUDFIVE-TEAM/notiU/assets/61011209/3a33ca74-27ad-4a4a-861b-21d78f0d771b">   학교 챗봇/구독 슬랙 봇 '내가 알려줌!'

> Inha Univ. Cloud Computing <br>
  프로젝트 기간 : 2023.11.~ 2024.07. <br>

![스크린샷 2024-12-20 18 07 15](https://github.com/user-attachments/assets/93019689-bfe1-4dbb-a68b-b8c86d9dc4b5)

<br>

## 📣 AWS Public Sector Day 세션 발표
> [AWS Public Sector Day Seoul 2024](https://www.youtube.com/watch?v=dQIVgZM7eVc) 교육 세션 발표 <br>
> 'Noti U'캠퍼스 인텔리젼스 프로젝트(학사행정 Agent) <br>
<br> 강남 COEX, 2024.07.04
> 
![스크린샷 2024-12-20 21 16 35](https://github.com/user-attachments/assets/95777bdb-799a-41ad-87b9-3af31b3e1210)
<br>
<br>
## 📣 Slack Webinar 프로젝트 소개
> [2024 Slack Webinar](https://slack.com/intl/ko-kr/events/why-slack-with-aws) - Why Slack with AWS <br>
> 대학에서부터 기업까지, Slack과 함께 AI 트랜스포메이션의 시작 <br>
<br> Online, 2024.04.24
> 
![스크린샷 2024-12-20 21 22 53](https://github.com/user-attachments/assets/1b1aa2f7-4c30-470a-bd0a-3d6a54887ee1)
---
<br>

## 💡 Key Features
### **1. 공지사항 구독 기능**

- **관심분야인 특정 키워드 구독**  
  장학금, 졸업, 현장실습 등과 같은 특정 키워드를 구독하여 원하는 정보만 얻을 수 있도록 사용자 맞춤형 서비스를 제공합니다. 

- **키워드 해당 글 매일 제공**  
  매일 아침 9시에 슬랙을 통해 제공합니다. 원하는 공지가 올라왔는지 수시로 확인해야하는 번거로움을 줄여줍니다. 

- **마감 날짜 전 알림 기능**  
  마감일 3일 전에 리마인더 알림을 제공하여 무심코 잊어버린 신청 기한을 놓치지 않도록 도와줍니다.

- **특정 학과 공지사항 구독**  
  사용자가 원하는 학과를 선택해 그 학과의 공지사항을 받을 수 있습니다.

- **외국인 학생을 위한 영문 기능**  
  영문 명령어를 사용하고, 공지사항 결과를 영문으로 제공하여 외국인 학생들의 정보 불균형을 해소할 수 있습니다.
  
### **2. 학칙 챗봇 기능**

- **학칙 관련 사항 질문 시 답변**  
  학칙에 관련된 질문에 자동으로 빠른 답변을 제공해줍니다.

- **관련 공지사항 링크 함께 제공**  
  사용자의 질문과 관련된 최근 공지사항을 찾아, 해당 공지사항의 링크를 함께 제공합니다.
  
<br>
  
## 🎥 Introduction Video
https://github.com/user-attachments/assets/e7a9e13d-9cb7-4c9c-b1e9-ec9f97e57c5b

<br>

## ⚙️ Architecture
Utilizing AWS Lambda functions, built on a serverless architecture, with Slack serving as the main user interface for interaction.
<img src="https://github.com/user-attachments/assets/2d22b0b4-4b16-40c9-8db3-4956e480f529" width="900" align="center"/></div>

<br>

## 🛠️ Tech Stack

### 📚 **AWS Services**
- **Compute & Orchestration**:  
  - AWS Lambda 
  - Amazon EventBridge  
  - Amazon API Gateway  

- **AI & Machine Learning**:  
  - Amazon Bedrock  
  - Amazon SageMaker  

- **Storage & Databases**:  
  - Amazon DynamoDB  
  - Amazon S3  
  - Amazon EFS  
  - AWS Aurora DB (Vector Database)  

### 🧠 **AI & NLP**
- **Embeddings**:  
  - Cohere Embed Multilingual v3  

- **Chatbot Model**:  
  - Claude 3  

- **OCR & Translation**:  
  - DeepL  
  - EasyOCR  

### 💬 **Communication**
- **Slack Integration**:  
  - Slack API
 
  <br>

  
## 📁 Folder Structure
```
.
├── README.md
└── lambda
    ├── called-at-time-and-saved-to-DB.py
    ├── cloudfive-crawling-translator.py
    ├── cloudfive-create-reminder.py
    ├── cloudfive-get-deadline-from-gpt.py
    ├── cloudfive-img-to-text-p39.py
    ├── cloudfive-send-translated-results-to-admin.py
    ├── cloudfive-translator-by-gpt.py
    ├── send-subscribe-result-lambda.py
    └── subscribe-bot-app.py
```

<!-- ![architecture](https://github.com/CLOUDFIVE-TEAM/notiU/assets/61011209/06cf3ec9-9f86-4d81-bcad-a3d72e8c3b65) -->
<!-- ![logo](https://github.com/CLOUDFIVE-TEAM/notiU/assets/61011209/3a33ca74-27ad-4a4a-861b-21d78f0d771b) -->
<!-- ![cloudfive_info](https://github.com/CLOUDFIVE-TEAM/notiU/assets/61011209/c8314e05-ff68-4e37-a41a-d35ce36cf1fa)-->

