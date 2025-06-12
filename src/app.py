import streamlit as st
from chatbot.utils.session import initialize_chatbot_session, chatbot_needs_reset

st.set_page_config(
    page_title="AI/ML Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

with open("src/chatbot/assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🤖 AI/ML Research Assistant</h1>', unsafe_allow_html=True)
# st.markdown('<h1 class="main-header">👩‍💻 👩💻 AI/ML Research Assistant</h1>', unsafe_allow_html=True)
# st.markdown('<h1 class="main-header">📚🔍  AI/ML Research Assistant</h1>', unsafe_allow_html=True)


# Sidebar Ayarları
with st.sidebar:
    st.header("⚙️ Ayarlar")

    search_type = st.radio(
        "Arama Tipi:",
        ["Normal", "Reasoning", "Vector Search"],
        format_func=lambda x: {
            "Normal": "Normal Arama",
            "Reasoning": "Akıllı Arama (Reasoning)",
            "Vector Search": "Vektör Tabanlı Arama"
        }.get(x, x),
        help="Arama yapmak istediğiniz yöntemi seçin"
    )
      
    # Arama tipine göre model listesi
    if search_type == "Reasoning":
        model_options = [
            "qwen-qwq-32b",
            "deepseek-r1-distill-llama-70b"
        ]
    else:
        model_options = [
            "gpt-4.1-nano-2025-04-14",
            "llama3-70b-8192",
            "llama-3.3-70b-versatile",
            "gemma2-9b-it"
        ]

    model_name = st.selectbox(
        "Model Seçimi:",
        model_options,
        help="Kullanmak istediğiniz modeli seçin"
    )
    #TODO: Bu kısımda search_type'a gore kontrol vardı
    # model_name = st.selectbox(
    #     "Model Seçimi:",
    #     ["gpt-4.1-nano-2025-04-14", "llama3-70b-8192", "llama-3.3-70b-versatile", "gemma2-9b-it"],
    #     help="Kullanmak istediğiniz modeli seçin"
    # )
    llm_provider = "OpenAI" if model_name == "gpt-4.1-nano-2025-04-14" else "Groq"


    temperature = st.slider(
        "Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="Yüksek değerler daha yaratıcı, düşük değerler daha tutarlı yanıtlar üretir"
    )

    st.markdown("---")
    st.header("💡 Örnek Sorular")
    st.subheader("🔍 Bu arama tipi için örnek sorular:")
    all_questions = {
        "Normal": [
            "AutoAgent makalesinin yazarları kimlerdir?",
            "DocETL makalesiyle ilişkili kod depoları hangileridir?",
            "Jiabin Tang'ın yazdığı tüm makaleleri listeler misin?",
            "MoonCast makalesinde hangi veri setleri kullanılmış?",
            "WebDancer makalesinin özetini verir misin?",
            "SoloSpeech makalesinin yayın tarihi nedir?",
            "Reservoir-enhanced Segment Anything Model makalesinin arXiv ve Papers With Code linkleri nedir?",
        ],
        "Reasoning": [
            "LLM ajanlarının zorluklarıyla ilgili makale bölümlerini bulur musun?",
            "ChartGalaxy makalesinde hangi yöntemler (methods) kullanılmış?",
            "ADOPT yöntemini kullanan makaleler hangileri?",
            "Large Language Model görevini ele alan makaleler hangileri?",
        ],
        "Vector Search": [
            "Podcast üretimiyle ilgili en alakalı makale paragraflarını getir.",
            "AutoAgent hakkında semantik olarak en yakın içeriği bul.",
            "Genel konuşma sistemleriyle ilgili benzer çalışmaları getir.",
        ]
    }
    
    if search_type == "Normal":
        sample_questions = (
            all_questions["Normal"] +
            all_questions["Reasoning"] +
            all_questions["Vector Search"]
        )
    else:
        sample_questions = all_questions.get(search_type, [])

    for example in sample_questions:
        if st.button(example):
            st.session_state.sample_question = example

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "chatbot" not in st.session_state:
    initialize_chatbot_session(llm_provider, model_name, temperature, search_type)

if "initialized" not in st.session_state:
    st.session_state.initialized = True

if chatbot_needs_reset(llm_provider, model_name, temperature, search_type):
    initialize_chatbot_session(llm_provider, model_name, temperature, search_type)
    st.session_state.messages = []
    # TODO: KONTROL ET
    if search_type == "Reasoning":
        # st.info(f"Reasoning arama tipi seçildi. Otomatik olarak qwen-qwq-32b modeli kullanılacak.")
        st.info(f"Akıllı arama (Reasoning) seçildi. Seçtiğiniz {model_name} modeli kullanılacak.")
    elif search_type == "Vector Search":
        st.info(f"Vektör tabanlı arama seçildi. Semantik arama için SentenceTransformer embedding modeli kullanılacak. Seçtiğiniz {model_name} modeli ise sonuçları işleyecektir.")
    else:
        st.info(f"LLM ayarları değiştirildi. Sağlayıcı: {llm_provider}, Model: {model_name}, Temperature: {temperature}")

# Chat Geçmişi
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    st.markdown(f"""
    <div class='chat-message {'user-message' if role=='user' else 'bot-message'}'>
        <strong>{'👤 Siz:' if role=='user' else '🤖 Asistan:'}</strong><br>{content}
    </div>
    """, unsafe_allow_html=True)
    if role == "assistant" and "cypher_query" in msg:
        with st.expander("🔍 Oluşturulan Cypher Query"):
            st.code(msg["cypher_query"], language="cypher")

# Giriş Kutusu
user_input = st.chat_input("AI/ML araştırmaları hakkında soru sorun...")

if "sample_question" in st.session_state:
    user_input = st.session_state.sample_question
    del st.session_state.sample_question

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("🤔 Yanıtlanıyor..."):
        response = st.session_state.chatbot.get_response(user_input)
    msg = {"role": "assistant", "content": response['answer']}
    if response['cypher_query']:
        msg["cypher_query"] = response['cypher_query']
    st.session_state.messages.append(msg)
    st.rerun()