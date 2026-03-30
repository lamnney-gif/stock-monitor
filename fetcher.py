import yfinance as yf
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def run_market():
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    raw_results = {"last_update": get_tw_time(), "stocks": {}}
    
    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            # 💡 關鍵修正：改抓 '1h' (小時線)，interval="1h" 能抓到更細膩的盤中波動
            df_hour = tk.history(period="60d", interval="1h") 
            df_day = tk.history(period="3mo", interval="1d") # 日線留著算 RSI 和 PE
            
            if df_hour.empty or len(df_hour) < 20: continue
            
            price = round(df_day['Close'].iloc[-1], 2)
            
            # --- 💡 專業 ATR 計算 (基於小時線模擬日波動) ---
            # 抓取過去 14 個交易小時的 True Range，並乘以 sqrt(7.5) 換算回日波動 (美股交易約 7.5 小時)
            hl = df_hour['High'] - df_hour['Low']
            hc = np.abs(df_hour['High'] - df_hour['Close'].shift())
            lc = np.abs(df_hour['Low'] - df_hour['Close'].shift())
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            
            # 取最近 24 小時(約 3 個交易日)的平均，這會非常靈敏
            atr_hourly = tr.rolling(24).mean().iloc[-1]
            # 換算成具備統計意義的日波幅 (小時波幅 * 根號交易時數)
            real_atr = round(atr_hourly * 2.73, 2) 
            
            # --- 💡 風控保底邏輯 ---
            # 如果算出來還是太小，強制給予 4.5% 的波幅 (高價股殺盤的基本消費)
            final_atr = max(real_atr, round(price * 0.045, 2))
            
            # 重新定義支撐位 (空頭排列下，防守應設在 2 倍 ATR)
            support = round(price - (final_atr * 2.0), 2)
            pressure = round(price + (final_atr * 1.5), 2)
            buy_point = round(price - (final_atr * 1.5), 2)
            
            # RSI 與基本面
            delta = df_day['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi_val = round(100 - (100 / (1 + rs.iloc[-1])), 2) if not pd.isna(rs.iloc[-1]) else 50.0
            
            info = tk.info if tk.info else {}
            
            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "---",
                "growth": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "---",
                "rsi": rsi_val,
                "volume_ratio": round(df_day['Volume'].iloc[-1] / df_day['Volume'].iloc[-6:-1].mean(), 2),
                "chips": "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整"),
                "support": support,
                "pressure": pressure,
                "atr": final_atr,
                "turnover_zone": round(price * 0.98, 2),
                "buy_point": buy_point
            }
            print(f"✅ {name} 數據完成 (Price: {price}, ATR: {final_atr})")
            
        except Exception as e:
            print(f"❌ {sym} 執行失敗: {str(e)}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
