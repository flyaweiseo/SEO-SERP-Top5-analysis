# keyword_outline_bot.py
import os
import json
from typing import List, Dict
from openai import OpenAI
from serpapi import GoogleSearch
from trafilatura import fetch_url, extract
from newspaper import Article

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def get_top_urls(keyword: str, n: int = 5) -> List[Dict[str, str]]:
    params = {
        "engine": "google",
        "q": keyword,
        "api_key": SERP_API_KEY,
        "num": n,
        "hl": "en",
        "gl": "us",
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
        "你是一位具有15年經驗的資深 SEO 顧問，請根據以下文章內容完成三件事：\n"
        "1. 條列出文章比其他文章好的『優點』（Pros）：用 - 開頭每一項\n"
        "2. 條列出文章比其他文章缺乏的『缺點』（Cons）：用 - 開頭每一項\n"
        "3. 請輸出完整的大綱（以 H2 / H3 分層），加上缺漏應補內容（如投資觀點、比較、誤區等）\n"
        "請務必用如下格式回答：\n"
        "### 優點\n- ...\n- ...\n\n"
        "### 缺點\n- ...\n- ...\n\n"
        "### 大綱\nH2: ...\nH3: ...\n"
        "請用繁體中文回答。"
    )
    user_prompt = f"文章網址：{url}\n\n文章內容如下：\n{text[:3000]}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    reply = response.choices[0].message.content
    return parse_analysis(reply)


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

    system_prompt = f"你是一名15年經驗的資深 SEO 顧問，擅長分析內容、提取重點，並彙整成新文章的架構，因此每次都能讓關鍵字排名進入前三名，請根據以下資訊，重新設計一篇以『{keyword}』為主題的完整內容大綱：\n\n- 整合競品的優缺點與文章架構\n- 補足缺漏的觀點（如：實際案例、比較分析、使用者痛點、金融術語等）\n- 依照 SEO 結構輸出完整的 H2 / H3 大綱\n- 使用繁體中文"

    user_prompt = f"【競品優點】\n{pros}\n\n【競品缺點】\n{cons}\n\n【競品大綱】\n{outlines}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt[:3500]}
        ]
    )
    return response.choices[0].message.content.strip()
