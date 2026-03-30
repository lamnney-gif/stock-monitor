import json
import os
import time
from datetime import datetime
from groq import Groq

def get_ai_response(client, ticker, data):
    # 這裡就是你原本要求的人設與邏輯
    prompt = f"""
    請針對以下數據進行深度診斷：
    股票：{data['name']} ({ticker})
    現價：{df_price if 'df_price' in locals() else data['price']} | RSI：{data.get('rsi', 'N/A')}
    
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
    if not os.path.exists("data_raw.json"): return
    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    keys = [k for k in keys if k]
    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    
    key_idx = 0
    for ticker, data in raw_data.get("stocks", {}).items():
        success = False
        while key_idx < len(keys) and not success:
            try:
                client = Groq(api_key=keys[key_idx])
                print(f"📡 使用 Key {key_idx+1} 診斷 {ticker}...")
                results["reports"][ticker] = get_ai_response(client, ticker, data)
                success = True
                print(f"✅ {ticker} 分析成功")
                time.sleep(2) # 避開頻率限制
            except Exception as e:
                print(f"⚠️ Key {key_idx+1} 失敗: {e}")
                key_idx += 1
        
        if not success:
            results["reports"][ticker] = "🤖 AI 暫時離線 (額度用罄)"

    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run()
