# main.py
import streamlit as st
from keyword_outline_bot import get_top_urls, get_article_text, analyse_article, propose_better_outline

st.set_page_config(page_title="Google SERP Top5 分析器", layout="centered")
st.markdown("""
    <style>
    .stTextInput>div>div>input {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #FF881A;
        color: white;
        border-radius: 0.5rem;
        font-weight: bold;
        padding: 0.6em 1.2em;
    }
    .stButton>button:hover {
        background-color: #7099FF;
    }
    .block-title {
        font-size: 1.5em;
        font-weight: 700;
        margin-top: 1.2em;
        color: #ffffff;
    }
    .pros {color: #00FFAA; font-weight: bold;}
    .cons {color: #FF8888; font-weight: bold;}
    .outline {color: #FFD700; font-weight: bold; white-space: pre-wrap;}
    </style>
""", unsafe_allow_html=True)

st.title("🔍 Google SERP Top5 分析器")
st.markdown("輸入關鍵字，我們將自動擷取前五篇文章，分析優缺點並產出建議的大綱。")

keyword = st.text_input("請輸入關鍵字：")

if st.button("開始分析") and keyword:
    with st.spinner("🔍 正在擷取資料與分析中…"):
        urls = get_top_urls(keyword)
        if not urls:
            st.error("❌ 找不到搜尋結果，請更換關鍵字或檢查 SerpAPI 設定")
        else:
            analyses = []
            for i, item in enumerate(urls, 1):
                st.markdown(f"---\n<div class='block-title'>📄 第 {i} 名：{item['title']}</div>", unsafe_allow_html=True)
                st.caption(item['link'])

                text = get_article_text(item["link"])
                if not text:
                    st.warning("⚠️ 擷取文章失敗，跳過此篇")
                    continue

                analysis = analyse_article(text, item["link"])
                analyses.append(analysis)

                with st.expander("✅ 查看分析結果"):
                    if analysis.get("pros"):
                        st.markdown("<div class='pros'>💚 優點：</div>", unsafe_allow_html=True)
                        st.markdown("\n".join([f"- {p}" for p in analysis["pros"]]))
                    if analysis.get("cons"):
                        st.markdown("<div class='cons'>💔 缺點：</div>", unsafe_allow_html=True)
                        st.markdown("\n".join([f"- {c}" for c in analysis["cons"]]))
                    if analysis.get("outline"):
                        st.markdown("<div class='outline'>📝 大綱：</div>", unsafe_allow_html=True)
                        st.code(analysis["outline"], language="markdown")

            if analyses:
                st.markdown("---")
                st.subheader("🧠 綜合建議大綱（可作為你文章的架構起點）")
                outline = propose_better_outline(analyses, keyword)
                st.code(outline, language="markdown")
                st.success("✅ 分析完成，可直接複製大綱使用！")
