import json
import os
import time
from datetime import datetime
from groq import Groq

def run_ai():
    # 1. 確保路徑正確
    base_path = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(base_path, "data_raw.json")
    save_path = os.path.join(base_path, "analysis_results.json")

    if not os.path.exists(raw_path): 
        print(f"❌ 找不到 {raw_path}")
        return
    
    with open(raw_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    # 2. 準備兩把 API Keys
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    keys = [k for k in keys if k]
    if not keys:
        print("🚨 錯誤：找不到任何 GROQ_API_KEY")
        return

    names = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    # 存檔時間點：直接用系統當下時間，不做任何時區加減
    results = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        "reports": {}
    }
    
    key_idx = 0
    stocks_data = raw.get("stocks", {})
    
    # 3. 開始 AI 分析
    for ticker, data in stocks_data.items():
        name = names.get(ticker, ticker)
        success = False
        
        while key_idx < len(keys) and not success:
            try:
                client = Groq(api_key=keys[key_idx])
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
                
                results["reports"][ticker] = chat.choices[0].message.content
                success = True
                print(f"✅ {name} 分析成功 (Key {key_idx+1})")
                time.sleep(2) # 避免觸發頻率限制
                
            except Exception as e:
                print(f"⚠️ Key {key_idx+1} 報錯，嘗試切換...")
                key_idx += 1

    # 4. 強制存檔
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"🏁 全部分析完成，存檔點: {results['last_update']}")

if __name__ == "__main__":
    run_ai()
