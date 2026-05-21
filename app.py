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

prefix_text = st.text_input("💬 복사할 때 [카테고리] 바로 뒤에 붙을 고정 문구", value=" 📢 안녕하세요! 김씨아저씨 TV입니다. 오늘 따끈따끈한 실시간 세상사 썰 배달왔습니다!\n\n==============================\n")
suffix_text = st.text_area("💬 복사할 때 [이야기 맨 뒤]에 자동으로 붙을 고정 문구", value="\n==============================\n\n👍오늘의 썰이 재밌으셨다면 [구독]과 [좋아요] 알림설정까지 꼭 부탁드려요 동생들! 다음 썰에서 만납시다!")
st.write("---")

category = st.selectbox("어이 동생, 오늘은 어떤 주제로 썰을 풀어볼까?", ["정치/시사", "미스터리/공포/역사", "경제/비즈니스", "요리/음식 레시피", "일상/직장생활/인간관계", "투자/재테크/부동산"])

category_map = {
    "정치/시사": {"hint": "양측의 정치적 역학 관계와 핵심 쟁점을 송곳처럼 짚어내는 시사 평론 평론가 스타일"},
    "미스터리/공포/역사": {"hint": "발굴 데이터와 역사적 서사 배경을 토대로 숨겨진 진실을 파헤치는 흡입력 있는 다큐멘터리 스타일"},
    "경제/비즈니스": {"hint": "거시 경제 지표의 변동이 실제 서민 가계와 골목 상권에 미치는 인과관계 분석 경제학자 스타일"},
    "요리/음식 레시피": {"hint": "재료의 화학적 변화와 맛의 황금 비율을 유쾌하고 과학적으로 설명하는 셰프 지식인 스타일"},
    "일상/직장생활/인간관계": {"hint": "직장 내 어른들의 심리학적 대처법 관점에서 속 시원한 솔루션을 제시하는 인생 멘토링 스타일"},
    "투자/재테크/부동산": {"hint": "자산 시장의 주기, 공급 물량, 정책 변화를 기반 리스크를 헤지하는 전문 투자 리포트 스타일"}
}

if st.button(f"[{category}] 아저씨 이야기 보따리 풀기"):
    if not GEMINI_API_KEY:
        st.error("🚨 어이 동생! 왼쪽 화면 입력창에 구글 API 키를 채워넣어 줘 마!")
    else:
        st.success("🔥 지금 이 순간 대한민국을 흔드는 구글 실시간 종합 헤드라인 톱 토픽을 긁어오는 중입니다 마!")
        
        # 🛠️ [동생의 천재적 아이디어] 검색어 고정 방식 폐기! 실시간 메인 뉴스 헤드라인 속보 30개를 직격 수집!
        top_stories_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            res = requests.get(top_stories_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            feed = feedparser.parse(res.content)
            
            # 실시간 헤드라인 최대 30개 수집
            raw_headlines =
