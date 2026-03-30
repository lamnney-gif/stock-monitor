import json
import os
import time
from datetime import datetime, timedelta
from groq import Groq

def get_tw_time():
    return datetime.utcnow() + timedelta(hours=8)

def run_ai():
    # 1. 讀取數據 (確保路徑正確)
    if not os.path.exists("data_raw.json"): 
        print("❌ 找不到 data_raw.json")
        return
    
    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    # 2. 準備 API Keys
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    keys = [k for k in keys if k]
    if not keys:
        print("❌ 找不到任何 GROQ_API_KEY")
        return

    # 對應名稱 (因為 data_raw 裡沒存名稱)
    names = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    key_idx = 0

    # 確保抓取的是 raw["stocks"]
    stocks_data = raw.get("stocks", {})
    
    for ticker, data in stocks_data.items():
        name = names.get(ticker, ticker) # 修正：從對照表抓名稱，抓不到就用代號
        success = False
        
        while key_idx < len(keys) and not success:
            try:
                client = Groq(api_key=keys[key_idx])
                
                # 修正 Prompt 中的變數抓取
                price = data.get('price', '---')
                pe = data.get('pe', '---')
                growth = data.get('growth', '---')
                
                prompt = f"分析{name}({ticker})：現價{price}、PE {pe}、成長率{growth}。需含【一句話死穴】與【最終決斷】。請使用繁體中文。"
                
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "你是一位洞察地緣政治與資本市場連動關係的資深策略家，講話簡練且具殺氣。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                content = chat.choices[0].message.content
                results["reports"][ticker] = content
                success = True
                print(f"✅ {name} ({ticker}) AI 分析成功")
                
                # 稍微加長一點延遲，避免 API Rate Limit (429 Error)
                time.sleep(2) 
                
            except Exception as e:
                print(f"⚠️ Key {key_idx+1} 報錯: {e}")
                key_idx += 1
                if key_idx < len(keys):
                    print(f"🔄 嘗試切換至 Key {key_idx+1}")
                else:
                    print("🚨 所有 API Key 已耗盡或皆報錯")

    # 3. 強制存檔 (這步最重要)
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"🏁 全部分析完成，已更新 analysis_results.json")

if __name__ == "__main__":
    run_ai()
