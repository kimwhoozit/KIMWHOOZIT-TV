import streamlit as st
import feedparser
import requests
import json
import re
import urllib.parse
import google.generativeai as genai

st.set_page_config(page_title="김씨 아저씨 트렌드 분석", layout="wide")

# 🔑 [PC & 클라우드 양방향 프리패스 안전장치]
default_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
except:
    pass  

st.sidebar.markdown("### 🔑 구글 유료 API 열쇠 입력창")
input_key = st.sidebar.text_input("구글 API 키 (클라우드 세팅 시 자동 입력됩니다 마)", value=default_key, type="password")

GEMINI_API_KEY = input_key.strip()

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.title("🔥 김씨 아저씨의 지식형 트렌드 분석 서비스")
st.write("구수한 입담 뒤에 날카로운 통찰을 숨긴 '지식인 김씨 아저씨'가 실시간 탑 토픽을 카테고리별로 매칭하여 분석합니다.")
st.write("---")

# 🔥 [동생 요청 반영: 자동입력란 고정 문구 초기값 수정 완료 마!]
prefix_text = st.text_input("💬 복사할 때 [카테고리] 바로 뒤에 붙을 고정 문구", value="")
suffix_text = st.text_area("💬 복사할 때 [이야기 맨 뒤]에 자동으로 붙을 고정 문구", value="\n==============================\n\n이미지 전용 한국어 숏츠 하나 만들어줘~!!")
st.write("---")

category = st.selectbox("어이 동생, 오늘은 어떤 주제로 썰을 풀어볼까?", ["정치/시사", "국제/해외이슈", "미스터리/공포/역사", "경제/비즈니스", "요리/음식 레시피", "일상/직장생활/인간관계", "투자/재테크/부동산"])

category_map = {
    "정치/시사": {
        "mode": "top_stories", "query": "",
        "hint": "양측의 정치적 역학 관계 and 핵심 쟁점을 송곳처럼 짚어내는 시사 평론 평론가 스타일"
    },
    "국제/해외이슈": {
        "mode": "niche_trend", "query": "국제 세계 미국 트럼프 전쟁 갈등 외교 바이러스 에볼라 사태",
        "hint": "전 세계 굵직한 사건사고, 트럼프 등 해외 인물 동향, 중동/이란 등 국제 정세 및 글로벌 위기 상황을 긴박하고 날카롭게 진단하는 국제 정세 전문 평론가 스타일"
    },
    "미스터리/공포/역사": {
        "mode": "niche_trend", "query": "유적 고고학 미스터리 역사 발견 비밀 과학",
        "hint": "발굴 데이터와 역사적 서사 배경을 토대로 숨겨진 진실을 파헤치는 흡입력 있는 다큐멘터리 스타일"
    },
    "경제/비즈니스": {
        "mode": "top_stories", "query": "",
        "hint": "거시 경제 지표의 변동이 실제 서민 가계와 골목 상권에 미치는 인과관계 분석 경제학자 스타일"
    },
    "요리/음식 레시피": {
        "mode": "niche_trend", "query": "요리 레시피 신제품 맛집 음식 트렌드 성분 과학",
        "hint": "재료의 화학적 변화와 맛의 황금 비율, 혹은 최신 음식 트렌드를 유쾌하고 과학적으로 설명하는 셰프 지식인 스타일"
    },
    "일상/직장생활/인간관계": {
        "mode": "niche_trend", "query": "직장인 심리학 회사 인간관계 트렌드 대처법",
        "hint": "직장 내 어른들의 심리학적 대처법 관점에서 속 시원한 솔루션을 제시하는 인생 멘토링 스타일"
    },
    "투자/재테크/부동산": {
        "mode": "top_stories", "query": "",
        "hint": "자산 시장의 주기, 공급 물량, 정책 변화를 기반 리스크를 헤지하는 전문 투자 리포트 스타일"
    }
}

if st.button(f"[{category}] 아저씨 이야기 보따리 풀기"):
    if not GEMINI_API_KEY:
        st.error("🚨 어이 동생! 왼쪽 화면 입력창에 구글 API 키를 채워넣어 줘 마!")
    else:
        selected_info = category_map[category]
        
        if selected_info["mode"] == "top_stories":
            st.success("🔥 지금 이 순간 대한민국을 흔드는 구글 실시간 종합 헤드라인 톱 토픽을 긁어오는 중입니다 마!")
            news_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        else:
            st.success(f"🎯 [{category}] 분야에서 실시간으로 가장 핫하게 떠오르는 트렌드 토픽들을 정밀 추적합니다 마!")
            news_url = f"https://news.google.com/rss?q={urllib.parse.quote(selected_info['query'])}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            res = requests.get(news_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            feed = feedparser.parse(res.content)
            
            raw_headlines = []
            if feed.entries:
                for entry in feed.entries[:30]:
                    clean_title = re.sub(r'\s*[-|]?\s*[가-힣a-zA-Z0-9\s]+$', '', entry.title).strip()
                    raw_headlines.append(clean_title)
            
            if not raw_headlines:
                st.error("🚨 구글 실시간 데이터를 긁어오지 못했다 마! 잠시 후 다시 시도해봐 마.")
            else:
                headline_pool = "\n".join([f"- {title}" for title in raw_headlines])
                
                st.write("---")
                st.subheader(f"👨 동네 김씨 아저씨의 지식형 [{category}] 분석 썰")
                
                prompt_instruction = f"""
                너는 50대 정 많은 동네 형님이자 세상 모든 분야에 빠삭한 숨은 대성 지식인 '김씨 아저씨'야.
                아래 제공된 [구글 실시간 트렌드 뉴스 리스트]에서 오늘 내가 선택한 카테고리인 [{category}]의 관점({selected_info['hint']})에 200% 부합하는 '최적의 이슈 3가지'를 니가 직접 엄선해라.
                
                [대본 작성 절대 준수 지침]
                1. 엄선한 3가지 이슈를 바탕으로 각각 story1, story2, story3 대본을 작성해라.
                2. 각 썰은 무조건 '공백 제외 500자 이상'의 묵직한 분량이어야 하며, [도입부-이면 구조 해부-서민 실전 솔루션/꿀팁] 단계를 확실히 밟아라.
                3. 말투는 (~했거든 마, ~알아야 한다 동생아) 같은 찰진 경상도 아저씨 톤을 유지하되 알맹이는 칼날 같아야 한다.
                4. 최종 결과물의 제목 파트에 니가 리스트에서 엄선한 '진짜 기사 제목'을 매칭해서 출력해라.
                
                [구글 실시간 트렌드 뉴스 리스트]
                {headline_pool}
                """
                
                final_prompt = prompt_instruction + '\n\n응답은 반드시 마크다운 백틱 없이 순수한 JSON 규격으로만 출력해라. 형태는 다음과 같아야 한다:\n{"selected_titles": ["선택한 기사제목1", "선택한 기사제목2", "선택한 기사제목3"], "story1": "내용", "story2": "내용", "story3": "내용"}'
                
                modern_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
                response = None
                success_model = ""
                
                for model_name in modern_models:
                    try:
                        model = genai.GenerativeModel(model_name=model_name, generation_config={"response_mime_type": "application/json"})
                        response = model.generate_content(final_prompt)
                        if response and response.text:
                            success_model = model_name
                            break
                    except:
                        continue
                
                if success_model:
                    raw_text = response.text
                    raw_text = re.sub(r'```json\s*|```', '', raw_text).strip()
                    stories_data = json.loads(raw_text)
                    
                    chosen_titles = stories_data.get("selected_titles", ["실시간 핫이슈 #1", "실시간 핫이슈 #2", "실시간 핫이슈 #3"])
                    
                    st.info(f"🚀 [{success_model} ENGINE] 가동 완료! 맞춤형 실시간 핫 토픽 대본을 출력한다 마!")
                    
                    for i in range(3):
                        story_content = stories_data.get(f"story{i+1}", "보따리 풀다가 쏟았다 마.")
                        title_text = chosen_titles[i] if i < len(chosen_titles) else "실시간 트렌드 분석 소식"
                        
                        full_script = f"[{category}]{prefix_text}{story_content}{suffix_text}"
                        
                        st.markdown(f"### 👨 김씨 아저씨의 실시간 융합 분석 #{i+1} : {title_text}")
                        st.code(full_script, language="text")
                        st.write("") 
                        
                    st.balloons()
                else:
                    st.warning("⚠️ 구글 서버 거부 반응 발생!")
        except Exception as e:
            st.error(f"오류 발생: {e}")
