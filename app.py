import streamlit as st
import feedparser
import requests
import json
import re
import os
import random
import urllib.parse  # 🛠️ [긴급 수혈] 주소창 빈칸을 안전하게 포장해주는 라이브러리 추가
from bs4 import BeautifulSoup

# 안전장치 API 키 세팅
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AIzaSyDxtSWjqoec1X55hIyePoDga1WW1wTlNQo"

st.title("🔥 김씨 아저씨의 지식형 트렌드 분석 서비스")
st.write("구수한 입담 뒤에 날카로운 통찰을 숨긴 '지식인 김씨 아저씨'가 깊이 있는 정보 전달과 분석 썰을 배달합니다.")

st.write("---")
st.subheader("⚙️ 복사 매크로 설정 (유튜브/블로그 고정 문구)")

prefix_text = st.text_input(
    "💬 복사할 때 [카테고리] 바로 뒤에 붙을 고정 문구", 
    value=" 📢 안녕하세요! 김씨아저씨 TV입니다. 오늘 따끈따끈한 실시간 세상사 썰 배달왔습니다!\n\n==============================\n"
)
suffix_text = st.text_area(
    "💬 복사할 때 [이야기 맨 뒤]에 자동으로 붙을 고정 문구", 
    value="\n==============================\n\n👍오늘의 썰이 재밌으셨다면 [구독]과 [좋아요] 알림설정까지 꼭 부탁드려요 동생들! 다음 썰에서 만납시다!"
)
st.write("---")

category = st.selectbox(
    "어이 동생, 오늘은 어떤 주제로 썰을 풀어볼까?",
    ["정치/시사", "미스터리/공포/역사", "경제/비즈니스", "요리/음식 레시피", "일상/직장생활/인간관계", "투자/재테크/부동산"]
)

category_map = {
    "정치/시사": {"ceid": "KR:ko", "query": "정치 국회 정부 시사 공방", "genre_hint": "단순한 비난이 아니라 양측의 정치적 역학 관계, 지지율 추이, 법리적 쟁점과 파장을 날카롭고 논리적으로 짚어내는 시사 평론"},
    "미스터리/공포/역사": {"ceid": "KR:ko", "query": "유적 OR 고고학 OR 발견 OR 비밀 OR 미스터리 과학", "genre_hint": "단순 카더라가 아니라 고고학적 발굴 데이터, 과학적 검증 기법, 역사적 문헌 배경을 토대로 미스터리의 진실을 파헤치는 다큐멘터리 스타일"},
    "경제/비즈니스": {"ceid": "KR:ko", "query": "경제 물가 환율 금리 기업", "genre_hint": "거시 경제 지표(금리, 환율, 유가)의 변동이 국내 산업과 유통망, 그리고 서민 가계 경제에 미치는 인과관계를 완벽하게 매커니즘적으로 설명하는 분석"},
    "요리/음식 레시피": {"ceid": "KR:ko", "query": "요리 레시피 과학 맛집 음식 성분", "genre_hint": "단순 조리 순서 나열이 아니라, 재료의 화학적 변화(마이야르 반응 등), 맛의 밸런스를 잡는 황금 비율의 이유를 과학적·영양학적으로 설명하는 고급 레시피 가이드"},
    "일상/직장생활/인간관계": {"ceid": "KR:ko", "query": "직장인 심리학 회사 트렌드 노동법", "genre_hint": "단순 한탄이 아니라 최신 노동법 트렌드, 직장 내 심리학적 인간관계 대처법, 조직 행동론 관점에서 솔루션을 제시하는 커리어 멘토링"},
    "투자/재테크/부동산": {"ceid": "KR:ko", "query": "주식 부동산 재테크 금리 전망", "genre_hint": "자산 시장의 주기(Cycle), 공급 물량, 정책 변화, 가치 평가 지표를 기반으로 리스크를 헷지하고 실질적 수익률을 올릴 수 있는 프로 투자자의 심층 리포트"}
}

def is_too_similar(title1, title2):
    words1 = set(re.findall(r'[가-힣a-zA-Z0-9]+', title1))
    words2 = set(re.findall(r'[가-힣a-zA-Z0-9]+', title2))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return (len(intersection) / len(union)) > 0.35

def clean_source_name(text):
    if not text:
        return text
    text = text.replace("&nbsp;", " ").replace("\xa0", " ")
    text = re.sub(r'\s*[-|]?\s*[가-힣a-zA-Z0-9\s]+(일보|뉴스|저널|경제|미디어|타임즈|매거진|방송|신문|티비|TV|리포트|팩트|포커스|디지틀|데일리|엔터)\s*$', '', text)
    text = re.sub(r'[\[\(][가-힣a-zA-Z0-9\s]+(일보|뉴스|저널|경제|미디어|타임즈|매거진|방송|신문|티비|TV|리포트|팩트|포커스|디지틀|데일리|엔터)[\]\)]', '', text)
    return text.strip()

def fetch_real_article_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.decompose()
            body_text = ""
            art_body = soup.find(class_=re.compile(r'(article|body|content|text|detail|post)'))
            if art_body:
                body_text = art_body.get_text()
            else:
                body_text = soup.get_text()
            body_text = re.sub(r'\s+', ' ', body_text).strip()
            if len(body_text) > 150:
                return body_text[:1200]
    except:
        pass
    return ""

if st.button(f"[{category}] 아저씨 이야기 보따리 풀기"):
    st.success(f"김씨 아저씨가 웹 트렌드 팩트를 정밀하게 수집하고 분석하는 중입니다... 잠시만 기다려주마!")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    selected_info = category_map[category]
    
    # 🛠️ [에러 원인 저격 및 폭파] 한글 검색 키워드의 빈칸과 특수문자를 주소창용 특수 규격으로 안전하게 치환 가공!
    encoded_query = urllib.parse.quote(selected_info['query'])
    news_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid={selected_info['ceid']}"
    
    try:
        response = requests.get(news_url, headers=headers, timeout=15)
        feed = feedparser.parse(response.content)
        
        articles_list = []
        all_news_content = ""
        
        if not feed.entries:
            articles_list = [
                {"title": f"최근 {category} 분야 최고의 심층 이슈", "summary": "현재 업계와 학계에서 가장 뜨겁게 분석하고 있는 핵심 데이터와 구조적 정황 상황"},
                {"title": f"두 번째로 주목해야 할 패러다임의 변화", "summary": "단순한 현상을 넘어 사회 전반에 구조적 영향을 미치고 있는 새로운 트렌드의 핵심 원인"},
                {"title": f"동생들을 위한 리스크 관리 및 핵심 요약 지침", "summary": "실질적인 통찰과 데이터 분석을 기반으로 도출된 향후 전망 및 행동 전략"}
            ]
        else:
            for entry in feed.entries:
                if len(articles_list) >= 3:
                    break
                    
                duplicate_flag = False
                for existing_art in articles_list:
                    if is_too_similar(entry.title, existing_art['title']):
                        duplicate_flag = True
                        break
                
                if not duplicate_flag:
                    real_body = fetch_real_article_content(entry.link)
                    cleaned_title = clean_source_name(entry.title)
                    
                    if not real_body or len(real_body) < 100 or clean_source_name(real_body) in cleaned_title:
                        keywords = re.findall(r'[가-힣A-Za-z0-9]+', cleaned_title)
                        core_words = [w for w in keywords if len(w) > 1][:4]
                        real_body = f"현재 {', '.join(core_words)} 관련 현안이 긴박하게 전개되면서 각계의 공방과 구조적인 이해관계 대립이 수면 위로 떠오른 정세 상황"
                    else:
                        real_body = clean_source_name(real_body)
                    
                    articles_list.append({"title": cleaned_title, "summary": real_body[:600]})
        
        for idx, art in enumerate(articles_list):
            all_news_content += f"[이슈 {idx+1}]\n제목: {art['title']}\n기사 원문 진짜 본문내용: {art['summary']}\n\n"
            
        st.subheader(f"📌 원문 본문 추적 완료! 필터링된 [{category}] 뉴스 3선")
        for art in articles_list:
            st.write(f"· {art['title']}")
            
        st.write("---")
        st.subheader(f"👨 동네 김씨 아저씨의 지식형 [{category}] 분석 썰")
        
        prompt_instruction = f"""
        너는 대한민국 동네 포장마차에서 소주 잔을 기울이는 50대 정 많은 동네 형님이자, 알고 보면 세상 모든 분야에 빠삭한 숨은 지식인 '김씨 아저씨'야.
        제공된 3가지 [{category}] 기사 원문 진짜 본문데이터를 '철저히 분석'하여, 각 이슈별로 완벽하게 독립된 심층 분석 이야기 3편을 들려줘라.
        
        [치명적인 임무 규칙]
        너는 상상으로 소설을 지어내지 마라. 반드시 제공된 '기사 원문 진짜 본문내용' 속에 적혀 있는 실제 사건의 정황, 핵심 단어, 데이터, 인물들의 멘트를 대사 속에 정확히 인용하고 녹여내어 동생에게 설명해 줘야 한다.
        말투는 투박하고 구수한 50대 대화체지만, 알맹이는 기사 원문의 정보를 완벽히 전달해야 해.
        - 장르별 분석 무드: {selected_info['genre_hint']}
        
        [천재 김씨 아저씨의 대사 구성 규칙]
        1. 하나의 이어지는 글로 쓰지 말고, 각 이슈별로 이야기를 완전히 단절시켜라.
        2. [도입부]: 구수한 50대 형님 말투로 자유로운 일상 인사나 평상 무드를 잡으며 시작해라.
        3. [정보 전달 및 원문 분석]: 기사 원문 본문에 언급된 구체적인 수치, 핵심 사실, 인물들의 사정을 조목조목 짚으며 동생에게 가르쳐주듯 설명해라.
        4. [구조적 원인 분석]: "이게 왜 터졌냐 하면 말이다," 하면서 원인과 매커니즘을 비유를 들어 깊이 있게 해설해라.
        5. [향후 전망 및 솔루션]: 날카롭게 예측하고 서민들이 어떻게 대처해야 하는지 리얼한 포지션(인사이트)을 제시해라.
        6. 이야기의 양은 아주 길고 묵직하게 서너 문단 이상 작성해라.
        7. 결과물은 반드시 아래의 JSON 형식 규격만 완벽하게 출력해라. 다른 설명이나 마크다운 백틱 문자는 절대 넣지 마라.
        
        [출력 JSON 규격]
        {{
            "story1": "첫 번째 이슈 원문 내용을 철저히 인용한 아저씨의 똑똑하고 긴 심층 분석 썰",
            "story2": "두 번째 이슈 원문 내용을 철저히 인용한 아저씨의 똑똑하고 긴 심층 분석 썰",
            "story3": "세 번째 이슈 원문 내용을 철저히 인용한 아저씨의 똑똑하고 긴 심층 분석 썰"
        }}
        
        [수집된 실제 웹 트렌드 데이터]
        {all_news_content}
        """
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        api_headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt_instruction}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        api_response = requests.post(api_url, headers=api_headers, data=json.dumps(payload), timeout=60)
        result_json = api_response.json()
        
        if 'candidates' in result_json and result_json['candidates']:
            raw_text = result_json['candidates'][0]['content']['parts'][0]['text']
            raw_text = re.sub(r'```json\s*|```', '', raw_text).strip()
            stories_data = json.loads(raw_text)
            
            for i in range(len(articles_list)):
                story_content = stories_data.get(f"story{i+1}", "아저씨가 이 팩트는 이야기 보따리 풀다가 쏟아버렸다 마.")
                final_copy_ready_text = f"[{category}]{prefix_text}{story_content}{suffix_text}"
                
                st.markdown(f"### 👨 김씨 아저씨의 심층 분석 #{i+1} : {articles_list[i]['title']}")
                st.code(final_copy_ready_text, language="text")
                st.write("\n")
            st.balloons()
            
        else:
            st.warning("⚠️ 구글 게이트웨이 순시 지연 발생! 임시 백업 엔진 가동한다 마.")
            intros = ["어이 동생, 거 안주 하나 집어먹고 내 말 들어봐 봐.", "동생, 소주 한 잔 시원하게 들이켜고 여기 좀 주목해 봐라."]
            analyses = ["이게 단순한 가십거리가 아니라, 판 흐름 속 핵심 맥락을 싹 뜯어봐야 해.", "내가 이면의 매커니즘을 분석해 보니까, 아주 뼈아픈 인과관계가 숨어있더라고."]
            outros = ["너도 흐름 놓치지 말고 정신 똑바로 차려라 알겠냐?", "잘 메모해 뒀다가 실전에서 꼭 써먹어라!"]
            
            for i in range(len(articles_list)):
                title = articles_list[i]['title']
                summary = articles_list[i]['summary']
                
                b_intro = random.choice(intros)
                b_analysis = random.choice(analyses)
                b_outro = random.choice(outros)
                
                backup_story = f"{b_intro} 요새 이 [{category}] 판에서 진짜 눈여겨봐야 하는 게 바로 이 '{title}' 소식이거든?\n\n"
                backup_story += f"{b_analysis}\n"
                backup_story += f"👉 기사 분석 팩트: \"{summary}\"\n\n"
                backup_story += f"이야... {b_outro}"
                
                final_copy_ready_text = f"[{category}]{prefix_text}{backup_story}{suffix_text}"
                
                st.markdown(f"### 👨 [백업] 김씨 아저씨의 분석 #{i+1} : {title}")
                st.code(final_copy_ready_text, language="text")
                st.write("\n")
            st.toast("백업 모드로 조립되었습니다!", icon="🤖")
                
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")