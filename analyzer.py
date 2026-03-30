import json
import os
import time
from datetime import datetime
from groq import Groq

def get_ai_response(client, ticker, data):
    """
    這裡就是你原本的邏輯：資深策略家 + Llama-3.3-70b
    """
    prompt = f"""
    請針對以下數據進行深度診斷：
    股票：{data['name']} ({ticker})
    現價：{data['price']} | RSI：{data['rsi']} | 本益比：{data['pe']} | 營收成長：{data['growth']}
    
    要求：
    1. 以「地緣政治與資本市場連動」的角度切入。
    2. 提供【一句話死穴】與【最終決斷】。
    3. 使用繁體中文，語氣冷峻專業。
    """
    
    # 這裡就是你原本用的 Groq 調用方式
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "你是一位洞察地緣政治與資本市場連動關係的資深策略家。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5 # 降低隨機性，讓策略更穩重
    )
    return completion.choices[0].message.content

def run_pipeline():
    # 讀取 fetcher.py 存好的數據
    if not os.path.exists("data_raw.json"):
        print("❌ 找不到數據源")
        return
    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # 準備兩把 Key (Key 1 優先，不行換 Key 2)
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    keys = [k for k in keys if k] # 過濾空值
    
    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    stocks = raw_data.get("stocks", {})

    key_idx = 0 # 從第一把 Key 開始
    
    for ticker, data in stocks.items():
        success = False
        while key_idx < len(keys) and not success:
            try:
                # 初始化目前的 Key
                client = Groq(api_key=keys[key_idx])
                print(f"📡 使用 Key {key_idx + 1} 診斷 {data['name']}...")
                
                report = get_ai_response(client, ticker, data)
                results["reports"][ticker] = report
                success = True
                print(f"✅ {data['name']} 分析成功")
                
                # 免費版 Groq 建議每檔稍微停一下，避免 Rate Limit
                time.sleep(2) 
                
            except Exception as e:
                print(f"⚠️ Key {key_idx + 1} 發生錯誤: {str(e)}")
                key_idx += 1 # 換下一把 Key
                if key_idx < len(keys):
                    print(f"🔄 正在自動切換至備用 Key {key_idx + 1}...")
                else:
                    print("❌ 所有備援 Key 均已失效")

        if not success:
            results["reports"][ticker] = "🤖 智權診斷模組暫時離線 (API 額度用罄)"

    # 存檔，讓 Streamlit (opp.py) 去讀
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("🚀 分析完成並已存檔")

if __name__ == "__main__":
    run_pipeline()
