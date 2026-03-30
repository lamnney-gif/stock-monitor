import yfinance as yf
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def run_market():
    # 💡 區分市場，避免價格混亂
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    raw_results = {"last_update": get_tw_time(), "stocks": {}}
    
    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="3mo")
            if df.empty: continue
            
            # 💡 修正 1：價格獲取
            price = round(df['Close'].iloc[-1], 2)
            
            # --- 💡 修正 2：ATR 真實波動計算 (TR 邏輯) ---
            hl = df['High'] - df['Low']
            hc = np.abs(df['High'] - df['Close'].shift())
            lc = np.abs(df['Low'] - df['Close'].shift())
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            atr_val = tr.rolling(14).mean().iloc[-1]
            
            # --- 💡 修正 3：針對「台股」與「美股」的不同波動率保底 ---
            # 台股漲跌幅限制 10%，波動通常較美股小；美股無限制。
            if ".TW" in sym:
                # 台股邏輯：ATR 通常落在股價的 1.5% - 3%
                min_vol = price * 0.02 
                final_atr = round(max(atr_val, min_vol), 2)
            else:
                # 美股邏輯：ATR 通常落在股價的 4% - 6%
                min_vol = price * 0.05 
                final_atr = round(max(atr_val, min_vol), 2)

            # --- 💡 修正 4：支撐與壓力計算 (空頭排列防守加深) ---
            # 1780 元如果是台股，ATR 80 元 (約 4.5%) 其實是合理的劇烈波動
            support = round(price - (final_atr * 2.0), 2)
            pressure = round(price + (final_atr * 1.5), 2)
            buy_point = round(price - (final_atr * 1.5), 2)
            
            # RSI 與基本面
            rsi_val = 50.0 # 預設
            if len(df) >= 14:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi_val = round(100 - (100 / (1 + rs.iloc[-1])), 2)

            info = tk.info if tk.info else {}
            
            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "---",
                "growth": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "---",
                "rsi": rsi_val,
                "volume_ratio": round(df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean(), 2),
                "chips": "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整"),
                "support": support,
                "pressure": pressure,
                "atr": final_atr,
                "turnover_zone": round(price * 0.99, 2),
                "buy_point": buy_point
            }
            print(f"✅ {name} (Price: {price}, ATR: {final_atr})")
            
        except Exception as e:
            print(f"❌ {sym} 錯誤: {str(e)}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
