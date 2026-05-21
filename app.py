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
st.write("구수한 입담 뒤에 날카로운 통찰을 숨긴 '지식인 김씨 아저씨'가 깊이 있는 분석 썰을 배달합니다.")
st.write("---")

prefix_text = st.text_input("💬 복사할 때 [카테고리] 바로 뒤에 붙을 고정 문구", value=" 📢 안녕하세요! 김씨아저씨 TV입니다. 오늘 따끈따끈한 실시간 세상사 썰 배달왔습니다!\n\n==============================\n")
suffix_text = st.text_area("💬 복사할 때 [이야기 맨 뒤]에 자동으로 붙을 고정 문구", value="\n==============================\n\n👍오늘의 썰이 재밌으셨다면 [구독]과 [좋아요] 알림설정까지 꼭 부탁드려요 동생들! 다음 썰에서 만납시다!")
st.write("---")

category = st.selectbox("어이 동생, 오늘은 어떤 주제로 썰을 풀어볼까?", ["정치/시사", "미스터리/공포/역사", "경제/비즈니스", "요리/음식 레시피", "일상/직장생활/인간관계", "투자/재테크/부동산"])

category_map = {
    "정치/시사": {"query": "정치 국회 정부 시사", "hint": "양측의 정치적 역학 관계와 핵심 쟁점을 송곳처럼 짚어내는 시사 평론 평론가 스타일"},
    "미스터리/공포/역사": {"query": "유적 고고학 발견 미스터리 역사", "hint": "발굴 데이터와 역사적 서사 배경을 토대로 숨겨진 진실을 파헤치는 흡입력 있는 다큐멘터리 스타일"},
    "경제/비즈니스": {"query": "경제 물가 환율 금리 기업", "hint": "거시 경제 지표의 변동이 실제 서민 가계와 골목 상권에 미치는 인과관계 분석 경제학자 스타일"},
    "요리/음식 레시피": {"query": "요리 레시피 맛집 음식 성분 과학", "hint": "재료의 화학적 변화와 맛의 황금 비율을 유쾌하고 과학적으로 설명하는 셰프 지식인 스타일"},
    "일상/직장생활/인간관계": {"query": "직장인 심리학 회사 트렌드 인간관계", "hint": "직장 내 어른들의 심리학적 대처법 관점에서 속 시원한 솔루션을 제시하는 인생 멘토링 스타일"},
    "투자/재테크/부동산": {"query": "주식 부동산 재테크 금리 전망", "hint": "자산 시장의 주기, 공급 물량, 정책 변화를 기반 리스크를 헤지하는 전문 투자 리포트 스타일"}
}

if st.button(f"[{category}] 아저씨 이야기 보따리 풀기"):
    if not GEMINI_API_KEY:
        st.error("🚨 어이 동생! 왼쪽 화면 입력창에 구글 API 키를 채워넣어 줘 마!")
    else:
        st.success("김씨 아저씨가 실제 웹 트렌드 뉴스를 수집하는 중입니다... 잠시만 기다려주마!")
        
        selected_info = category_map[category]
        news_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(selected_info['query'])}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            res = requests.get(news_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            feed = feedparser.parse(res.content)
            
            articles = []
            if feed.entries:
                for entry in feed.entries[:3]:
                    title = re.sub(r'\s*[-|]?\s*[가-힣a-zA-Z0-9\s]+$', '', entry.title).strip()
                    articles.append({"title": title, "summary": title})
            else:
                articles = [
                    {"title": f"최근 {category} 분야 최고의 핫트렌드 분석 현안", "summary": "현재 시장 전반에서 가장 뜨겁게 논쟁이 되고 있는 상황 정세"},
                    {"title": "두 번째로 파장이 크게 번지고 있는 구조적 변화 정황", "summary": "단순 가십을 넘어 거시적인 흐름의 변화를 이끄는 패러다임"},
                    {"title": "동생들을 위한 실전 리스크 헷징 및 대응 전략", "summary": "데이터와 실제 정황 분석을 기반으로 도출된 솔루션"}
                ]
                
            all_news = ""
            for idx, art in enumerate(articles):
                all_news += f"[이슈 {idx+1}]\n제목: {art['title']}\n내용: {art['summary']}\n\n"
                
            st.subheader(f"📌 원문 뉴스 수집 성공! [{category}] 핫이슈 3선")
            for art in articles:
                st.write(f"· {art['title']}")
                
            st.write("---")
            st.subheader(f"👨 동네 김씨 아저씨의 지식형 [{category}] 분석 썰")
            
            prompt_instruction = f"너는 50대 정 많은 동네 형님이자 세상 모든 분야에 빠삭한 숨은 대성 지식인 '김씨 아저씨'야. 제공된 3가지 실시간 기사 데이터를 바탕으로, 유튜브나 방송에서 구수하게 읊어줄 수 있는 '독창적이고 깊이 있는 심층 분석 썰' 3편을 작성해라. 각 이슈당 분량은 무조건 공백 제외 500자 이상의 묵직한 롱폼 대본 분량으로 상세하게 서술하고, [도입부-이면해부-해결책] 구조를 갖춰라. 말투는 (~했거든 마, ~알아야 한다 동생아) 같은 경상도 아저씨 톤을 유지해라. 장르 특성: {selected_info['hint']}. [기사 데이터]\n{all_news}"
            final_prompt = prompt_instruction + '\n\n응답은 반드시 마크다운 백틱 없이 순수한 JSON 규격으로만 출력해라. 형태: {"story1": "내용", "story2": "내용", "story3": "내용"}'
            
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
                st.info(f"🚀 [{success_model} 엔진] 가동 완료! 묵직한 오리지널 심층 대본을 출력한다 마!")
                raw_text = response.text
                raw_text = re.sub(r'```json\s*|```', '', raw_text).strip()
                stories_data = json.loads(raw_text)
                
                for i in range(len(articles)):
                    story_content = stories_data.get(f"story{i+1}", "보따리 풀다가 쏟았다 마.")
                    full_script = f"[{category}]{prefix_text}{story_content}{suffix_text}"
                    
                    st.markdown(f"### 👨 김씨 아저씨의 심층 분석 #{i+1} : {articles[i]['title']}")
                    # 💡 모바일/PC 100% 공용 붙박이 우측 상단 복사 단추 탑재!
                    st.code(full_script, language="text")
                    st.write("") 
                    
                st.balloons()
            else:
                st.warning("⚠️ 구글 서버 거부 반응 발생!")
        except Exception as e:
            st.error(f"오류 발생: {e}")
