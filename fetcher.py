import yfinance as yf
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    """獲取台北時間作為數據基準點"""
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
            # 💡 抓取 3 個月數據，確保 Rolling 計算有足夠樣本
            df = tk.history(period="3mo") 
            if df.empty or len(df) < 20:
                print(f"⚠️ {name} 數據不足，跳過")
                continue
            
            # --- 核心計算開始 ---
            price = round(df['Close'].iloc[-1], 2)
            
            # 💡 關鍵修正：真正的 ATR (True Range) 邏輯
            # TR 取三者最大：(當前高低差, 當前高與前收差, 當前低與前收差)
            hl = df['High'] - df['Low']
            hc = np.abs(df['High'] - df['Close'].shift())
            lc = np.abs(df['Low'] - df['Close'].shift())
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            
            # 計算 14 日平均真實波幅 (ATR)
            atr_val = tr.rolling(14).mean().iloc[-1]
            atr_val = round(atr_val, 2) if not pd.isna(atr_val) else round(price * 0.03, 2)
            
            # 基於 ATR 的動態支撐壓力 (1.5 倍 ATR 是標準風控距離)
            support = round(price - (atr_val * 1.5), 2)
            pressure = round(price + (atr_val * 1.5), 2)
            buy_point = round(price - (atr_val * 1.2), 2)
            
            # RSI 計算
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi_val = round(100 - (100 / (1 + rs.iloc[-1])), 2) if not pd.isna(rs.iloc[-1]) else 50.0
            
            # 成交量比 (5日均)
            vol_ratio = round(df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean(), 2)
            
            # 抓取基本面 info
            info = tk.info if tk.info else {}
            pe = info.get('trailingPE', "---")
            growth = info.get('revenueGrowth')
            growth_str = f"{growth*100:.1f}%" if (growth is not None) else "---"

            # 存入結果
            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": round(pe, 2) if isinstance(pe, (int, float)) else pe,
                "growth": growth_str,
                "rsi": rsi_val,
                "volume_ratio": vol_ratio,
                "chips": "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整"),
                "support": support,
                "pressure": pressure,
                "atr": atr_val,
                "turnover_zone": round(price * 0.985, 2), # 密集換手區模擬
                "buy_point": buy_point
            }
            print(f"✅ {name} 數據處理完成 (ATR: {atr_val})")
            
        except Exception as e:
            print(f"❌ {sym} 執行錯誤: {str(e)}")

    # 寫入 JSON
    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
