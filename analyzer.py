import json
import os
from datetime import datetime
from groq import Groq

def get_ai_response(client, ticker, data):
    """封裝 AI 請求邏輯"""
    prompt = f"""
    你是一位專業分析師。請針對以下數據提供投資建議：
    股票：{data['name']} ({ticker})
    現價：{data['price']} | RSI：{data['rsi']} | PE：{data['pe']}
    請用繁體中文回答，包含【一句話死穴】與【最終決斷】。內容簡短。
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return completion.choices[0].message.content

def run_pipeline():
    # 1. 檢查原始數據
    if not os.path.exists("data_raw.json"):
        print("❌ 找不到數據源")
        return
    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # 2. 準備兩把 Key
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    keys = [k for k in keys if k] # 過濾掉空的 Key
    
    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    stocks = raw_data.get("stocks", {})

    current_key_index = 0
    
    for ticker, data in stocks.items():
        success = False
        while current_key_index < len(keys) and not success:
            try:
                client = Groq(api_key=keys[current_key_index])
                print(f"📡 使用 Key {current_key_index + 1} 診斷 {data['name']}...")
                
                report = get_ai_response(client, ticker, data)
                results["reports"][ticker] = report
                success = True
                print(f"✅ {data['name']} 分析成功")
                
            except Exception as e:
                print(f"⚠️ Key {current_key_index + 1} 出錯: {str(e)}")
                current_key_index += 1 # 切換到下一把 Key
                if current_key_index < len(keys):
                    print("🔄 正在嘗試使用備用 Key...")
                else:
                    print("❌ 所有 Key 都已耗盡或失敗")

    # 3. 存檔
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_pipeline()
