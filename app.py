import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="척척박사 AI", page_icon="🎓")

# 2. API 설정 (보안 규칙 준수)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("`.streamlit/secrets.toml` 파일에 API 키를 설정해주세요!")
    st.stop()

# -----------------------------------------------------------------------------
# 3. [핵심] 사용 가능한 모델 목록 가져오기 및 자동 선택
# -----------------------------------------------------------------------------
def get_working_model():
    try:
        # 현재 내 API 키와 라이브러리 버전에서 사용 가능한 모델 리스트 확보
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1순위: gemini-1.5-flash, 2순위: gemini-pro, 3순위: 아무거나 첫 번째
        for target in ["models/gemini-1.5-flash", "models/gemini-1.0-pro", "models/gemini-pro"]:
            if target in available_models:
                return target
        return available_models[0] if available_models else None
    except Exception as e:
        st.error(f"모델 목록을 불러오는 중 오류가 발생했습니다: {e}")
        return None

target_model_name = get_working_model()

# -----------------------------------------------------------------------------
# 4. 사이드바 - 상태 진단창
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎓 시스템 진단")
    if target_model_name:
        st.success(f"연결 성공! 사용 모델:\n`{target_model_name}`")
    else:
        st.error("사용 가능한 모델을 찾지 못했습니다.")
    
    if st.button("대화 내용 지우기 🗑️"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------------------------------------------
# 5. 메인 채팅 로직
# -----------------------------------------------------------------------------
st.title("🎓 척척박사 AI")

if target_model_name:
    # 모델 초기화 (전문가 설정)
    model = genai.GenerativeModel(
        model_name=target_model_name,
        system_instruction="너는 박학다식한 전문가 '척척박사 AI'야. 친절하고 명확하게 답변해줘."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 화면에 대화 기록 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("질문을 입력하세요!"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            # Gemini는 이전 대화 기록(history)을 명시적으로 넣어줄 때 더 똑똑합니다.
            history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
            
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"답변 생성 중 오류 발생: {e}")