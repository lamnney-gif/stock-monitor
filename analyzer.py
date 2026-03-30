# 在 analyzer.py 裡面的執行部分
def run_analysis():
    # 讀取剛剛 fetcher.py 存好的原始數據
    try:
        with open("data_raw.json", "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except:
        print("❌ 找不到 data_raw.json，請先執行 fetcher.py")
        return

    analysis_results = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reports": {}
    }

    stocks = raw_data.get("stocks", {})
    if not stocks:
        print("❌ data_raw.json 裡面沒有股票數據！")
        return

    for ticker, data in stocks.items():
        print(f"📡 正在幫 {ticker} 進行 AI 診斷...")
        # 這裡呼叫你的 AI 函數 (例如 get_ai_response)
        report = get_ai_response(ticker, data) 
        
        if report:
            analysis_results["reports"][ticker] = report
            print(f"✅ {ticker} 分析完成")
        else:
            print(f"⚠️ {ticker} AI 回傳空值")

    # 最後存檔
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=4)
