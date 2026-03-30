import json
import os
import time
from datetime import datetime
from groq import Groq

def get_ai_response(client, ticker, data):
    # 繼承你原本要求的資深策略家人設
    prompt = f"""
    請針對以下數據進行深度診斷：
    股票：{data['name']} ({ticker})
    現價：{data['price']} | RSI：{data.get('rsi', 'N/A')} | PE：{data.get('pe', 'N/A')}
    
    要求：
    1. 以「地緣政治與資本市場連動」的角度切入。
    2. 提供【一句話死穴】與【最終決斷】。
    3. 使用繁體中文，語氣冷峻專業。
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "你是一位洞察地緣政治與資本市場連動關係的資深策略家。"},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

def run():
    print("🚀 AI 分析模組啟動...")
    
    # 1. 讀取數據
    if not os.path.exists("data_raw.json"):
        print("❌ 錯誤：找不到 data_raw.json，請確認 fetcher.py 有先跑完")
        return

    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # 2. 抓取 Key (務必確認 main.yml 裡的 env 名字一致)
    k1 = os.getenv("GROQ_API_KEY_1")
    k2 = os.getenv("GROQ_API_KEY_2")
    keys = [k for k in [k1, k2] if k and len(k) > 10] # 過濾掉無效或過短的 Key
    
    if not keys:
        print(f"❌ 錯誤：Python 沒拿到任何有效的 API Key (K1長度: {len(k1) if k1 else 0})")
        return

    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    stocks = raw_data.get("stocks", {})

    key_idx = 0
    for ticker, data in stocks.items():
        success = False
        print(f"📡 診斷 {data['name']} ({ticker})...")
        
        while key_idx < len(keys) and not success:
            try:
                client = Groq(api_key=keys[key_idx])
                report = get_ai_response(client, ticker, data)
                results["reports"][ticker] = report
                success = True
                print(f"✅ {ticker} 分析成功 (Key {key_idx+1})")
                time.sleep(2) # 避開頻率限制
            except Exception as e:
                print(f"⚠️ Key {key_idx+1} 失敗: {str(e)}")
                key_idx += 1 # 換下一把 Key
        
        if not success:
            results["reports"][ticker] = "🤖 AI 暫時離線 (API 授權或額度問題)"

    # 3. 寫入檔案
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("🏁 分析任務結束。")

if __name__ == "__main__":
    run()
