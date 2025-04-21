# keyword_outline_bot.py
import os
import json
from typing import List, Dict
from openai import OpenAI
from serpapi import GoogleSearch
from trafilatura import fetch_url, extract
from newspaper import Article

openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"openai_api_key 的值: {openai_api_key}")
serpapi_api_key = os.getenv("SERPAPI_API_KEY")
print(f"serpapi_api_key 的值: {serpapi_api_key}")

client = OpenAI(api_key=openai_api_key)

def get_top_urls(keyword: str, n: int = 5) -> List[Dict[str, str]]:
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": serpapi_api_key,
        "num": n,
        "hl": "zh-tw",
        "gl": "tw",
        "google_domain": "google.com"
    }
    results = GoogleSearch(params).get_dict()
    organic = results.get("organic_results", [])[:n]
    return [{"title": o.get("title"), "link": o.get("link")} for o in organic]


def get_article_text(url: str) -> str:
    html = fetch_url(url)
    if html:
        text = extract(html, include_comments=False, include_tables=False)
        if text and len(text) > 200:
            return text

    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except:
        return ""


def analyse_article(text: str, url: str) -> Dict:
    system_prompt = (
        "你是一位具有15年經驗的資深 SEO 顧問，擅長分析 Google 搜尋前五名內容，並規劃出具有獨特觀點、架構合理、聚焦使用者搜尋意圖的 SEO 文章大綱。請根據以下文章內容完成三件事：\n"
        "1. 條列出文章比其他文章好的『優點』（Pros）：有哪些觀點、架構、舉例、標題安排是值得學習的？（用 - 開頭每一項）\n"
        "2. 條列出文章比其他文章缺乏的『缺點』（Cons）：有哪些觀點遺漏、結構瑣碎、內容重複、無法回應使用者搜尋意圖的地方？（用 - 開頭每一項）\n"
        "3. 請輸出原始文章完整的段落標題（列出所有 H2 / H3 並以 H2 / H3 分層）\n"
        "請務必用如下格式回答：\n"
        "### 優點\n- ...\n- ...\n\n"
        "### 缺點\n- ...\n- ...\n\n"
        "### 大綱\nH2: ...\nH3: ...\n"
        "請用繁體中文回答。"
    )
    user_prompt = f"文章網址：{url}\n\n文章內容如下：\n{text[:3000]}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        reply = response.choices[0].message.content
        return parse_analysis(reply)
    except Exception as e:
        print("🔥 OpenAI 回傳錯誤：", e)
        raise e


def parse_analysis(text: str) -> Dict:
    result = {"pros": [], "cons": [], "outline": ""}
    lines = text.splitlines()
    mode = None
    for line in lines:
        if any(k in line for k in ["優點", "好處"]):
            mode = "pros"
        elif any(k in line for k in ["缺點", "壞處", "可改進"]):
            mode = "cons"
        elif any(k in line for k in ["H2", "H3", "文章架構", "大綱"]):
            mode = "outline"

        if mode == "pros" and line.startswith("-"):
            result["pros"].append(line.lstrip("- "))
        elif mode == "cons" and line.startswith("-"):
            result["cons"].append(line.lstrip("- "))
        elif mode == "outline":
            result["outline"] += line + "\n"
    return result


def propose_better_outline(analyses: List[Dict], keyword: str) -> str:
    pros = sum([a.get("pros", []) for a in analyses], [])
    cons = sum([a.get("cons", []) for a in analyses], [])
    outlines = "\n\n".join([a.get("outline", "") for a in analyses])

    system_prompt = f"你是一名15年經驗的資深 SEO 顧問，擅長分析內容、提取重點，並彙整成具有獨特觀點的新文章架構，因此每次都能讓關鍵字排名進入前三名，請根據以下資訊，重新設計一篇以『{keyword}』為主題的完整內容大綱：\n\n- 整合競品的優缺點與文章架構\n- 補足缺漏的觀點（如：實際案例、比較分析、使用者痛點等）\n- 依照 SEO 結構輸出完整的 H2 / H3 大綱\n- 使用繁體中文\n- 限定 H2 段落為 5~7 段\n- 每個 H2 觀點或切入角度需明顯不同\n- 內容具有原創性或專業觀點（如：比較表、案例等）"

    user_prompt = f"【競品優點】\n{pros}\n\n【競品缺點】\n{cons}\n\n【競品大綱】\n{outlines}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt[:3500]}
        ]
    )
    return response.choices[0].message.content.strip()
