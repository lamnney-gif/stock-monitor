# fetcher.py
import yfinance as yf
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def get_last_update():
    """讀取上一筆 data_raw.json 的時間"""
    if os.path.exists("data_raw.json"):
        try:
            with open("data_raw.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("last_update", "N/A")
        except:
            return "N/A"
    return "N/A"

def get_tw_time():
    """當前 UTC+8 時間，用作本次更新時間"""
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def calculate_rsi(series, period=14):
    """精準版 RSI 計算"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1], 2) if not pd.isna(rs.iloc[-1]) else 50.0

def run_market():
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光",
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電",
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }

    last_update = get_last_update()
    print(f"上次更新時間: {last_update}")

    raw_results = {"last_update": get_tw_time(), "stocks": {}}

    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="1mo")
            if df.empty: 
                print(f"⚠️ {name} 無歷史資料，跳過")
                continue

            price = round(df['Close'].iloc[-1], 2)
            rsi_val = calculate_rsi(df['Close'], 14)

            # 🔹 ATR 地板（極端止損）
            atr_floor = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
            dynamic_stop = round(price - 2.5 * atr_floor, 2)

            # 🔹 防守觀察點（高點回檔停利）
            recent_high = df['Close'].rolling(5).max().iloc[-1]
            stop_profit_line = round(recent_high * 0.97, 2)

            # 支撐與壓力
            std20 = df['Close'].rolling(20).std().iloc[-1]
            support = round(price - 1.5 * std20, 2)
            pressure = round(price + 1.5 * std20, 2)
            buy_point = round(price - 1.2 * std20, 2)

            # 成交量比
            vol_avg = df['Volume'].iloc[-6:-1].mean()
            vol_ratio = round(df['Volume'].iloc[-1] / vol_avg, 2) if vol_avg > 0 else 1.0

            # 籌碼邏輯
            chip_flow = "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整")

            # 基本面
            info = tk.info if tk.info else {}
            pe_val = round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "---"
            rev_val = f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "---"

            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": pe_val,
                "growth": rev_val,
                "rsi": round(rsi_val, 2),
                "volume_ratio": vol_ratio,
                "chips": chip_flow,
                "support": support,
                "pressure": pressure,
                "atr": round(atr_floor, 2),
                "turnover_zone": round(price * 0.99, 2),
                "buy_point": buy_point,
                "dynamic_stop": dynamic_stop,
                "stop_profit_line": stop_profit_line
            }

            print(f"✅ {name} 更新完成: 價格={price}, ATR地板={round(atr_floor,2)}, 防守觀察點={stop_profit_line}")

        except Exception as e:
            print(f"❌ {sym} 更新失敗: {e}")

    # 輸出 JSON
    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)
    print(f"📊 本次更新完成，保存至 data_raw.json")

if __name__ == "__main__":
    run_market()
