import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
import warnings
import webbrowser
import os
import time
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression

# 忽略警告訊息
warnings.filterwarnings('ignore')

# 核心追蹤清單
tickers = {
    "MU": "美光", 
    "INTC": "英特爾", 
    "000660.KS": "海力士", 
    "2303.TW": "聯電", 
    "6770.TW": "力積電", 
    "2344.TW": "華邦電", 
    "3481.TW": "群創", 
}

def get_volume_support(df):
    """計算籌碼地板 (120日成交量密集區)"""
    try:
        recent_df = df.tail(120)
        if len(recent_df) < 20: return 0
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        max_vol_idx = np.argmax(v_hist[0])
        return (v_hist[1][max_vol_idx] + v_hist[1][max_vol_idx+1]) / 2
    except: return 0

def get_google_news(keyword):
    """抓取 Google 新聞"""
    news_items = []
    try:
        encoded_key = quote(f"{keyword} 股價 新聞")
        rss_url = f"https://news.google.com/rss/search?q={encoded_key}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:3]:
            news_items.append({"title": entry.title, "link": entry.link})
    except: pass
    return news_items

def run_monitor():
    now_obj = datetime.now()
    now_str = now_obj.strftime('%Y-%m-%d %H:%M:%S')
    results = []
    all_news_html = "" 

    print(f"🚀 [{now_str}] 正在同步全數據並計算關鍵位...")

    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty or len(df) < 20: continue
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # --- 價格指標 ---
            tech_support = ma20 - (2 * std20)   # 技術支撐 (布林下軌)
            tech_pressure = ma20 + (2 * std20)  # 建議賣出價 (布林上軌)
            chip_floor = get_volume_support(df) # 籌碼地板
            suggested_buy = (tech_support + chip_floor) / 2 # 建議買入價
            
            recent_high = df['High'].tail(5).max()
            stop_profit_price = recent_high * 0.97 # 停利防線
            
            # --- 技術指標 (斜率改為百分比) ---
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            y_data = df['Close'].tail(10).values
            X_data = np.arange(10).reshape(-1, 1)
            avg_price = y_data.mean()
            raw_slope = LinearRegression().fit(X_data, y_data.reshape(-1, 1)).coef_[0][0]
            slope_pct = (raw_slope / avg_price) * 100 
            
            bias = ((close_val - ma20) / ma20) * 100
            
            # --- 籌碼數據 ---
            info = stock.info
            f_pe = info.get('forwardPE', "無")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            insider_pct = info.get('heldPercentInsiders', 0) * 100

            # --- 智慧燈號邏輯 (恢復詳盡分析) ---
            row_class = ""
            light_icon = "🔎"
            
            if vol_ratio > 2.0 and abs(slope_pct) < 0.1 and close_val > ma20:
                row_class = "color-alert-orange"
                light_icon = "🚨"
                status = f"🚨 【大戶倒貨】成交量爆出 {vol_ratio:.2f} 倍但股價幾乎不動 (斜率僅 {slope_pct:.2f}%)。這是典型的高檔換手或大戶出貨，極度危險，建議大幅減碼防禦。"
            elif close_val >= tech_pressure * 0.98:
                row_class = "table-info"
                light_icon = "⚠️"
                status = f"⚠️ 【分批停利】現價 {close_val:.2f} 已逼近建議賣出價 {tech_pressure:.2f}。目前正乖離率達 {bias:.1f}%，短線過熱，隨時有回檔風險，建議先將獲利分批入袋。"
            elif vol_ratio < 0.8 and abs(slope_pct) < 0.05:
                row_class = "table-secondary"
                light_icon = "💤"
                status = f"💤 【縮量整理】成交量僅均量 {vol_ratio:.2f} 倍，且趨勢斜率極平緩 ({slope_pct:.2f}%)。市場目前觀望氣氛濃厚，暫無攻擊動能，建議保留現金等待表態。"
            elif close_val <= suggested_buy * 1.02 and slope_pct > -0.1:
                row_class = "table-success"
                light_icon = "✅"
                status = f"✅ 【買入訊號】股價回測建議買入價 {suggested_buy:.2f} 附近。支撐區表現強勁且趨勢開始回穩 ({slope_pct:.2f}%)，適合在此分批佈局中長線部位。"
            elif close_val <= tech_support:
                row_class = "table-danger"
                light_icon = "☢️"
                status = f"☢️ 【停損警示】股價已擊穿技術支撐 {tech_support:.2f}。目前趨勢慣性已被破壞，斜率急跌至 {slope_pct:.2f}%，請嚴格執行停損以保護資金安全。"
            else:
                status = f"🔎 【正常整理】目前在支撐 {tech_support:.2f} 與壓力 {tech_pressure:.2f} 之間穩定波動。量能平穩且斜率為 {slope_pct:.2f}%，無明顯轉向訊號，維持原有部位即可。"

            stock_news = get_google_news(name)
            for n in stock_news:
                all_news_html += f'<div class="mb-2 border-bottom pb-1 small"><span class="badge bg-primary">{name}</span> <a href="{n["link"]}" target="_blank" class="text-dark text-decoration-none fw-bold ms-1">{n["title"]}</a></div>'

            results.append({
                "light": light_icon,
                "name": f"{name} ({ticker})", "price": f"{close_val:.2f}", 
                "tech_sup": f"{tech_support:.2f}", "buy": f"{suggested_buy:.2f}", 
                "chip": f"{chip_floor:.2f}", "sell": f"{tech_pressure:.2f}",
                "stop": f"{stop_profit_price:.2f}", "pe": f"{f_pe:.1f}" if isinstance(f_pe, (float, int)) else "無",
                "inst": f"{inst_pct:.1f}%", "insider": f"{insider_pct:.1f}%",
                "vol": f"{vol_ratio:.2f}", "slope": f"{slope_pct:.2f}%", "status": status, "cls": row_class
            })
        except: pass

    # --- HTML 生成 ---
    html_all = f"""
    <html><head><meta charset="utf-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f4f7f6; padding: 20px; font-family: "Microsoft JhengHei", sans-serif; }}
        .header-box {{ background: linear-gradient(135deg, #0d6efd 0%, #004085 100%); color: white; border-radius: 12px; padding: 15px 25px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        th {{ background-color: #212529 !important; color: white !important; text-align: center; font-size: 0.75em; vertical-align: middle; padding: 10px !important; }}
        td {{ text-align: center; vertical-align: middle; border: 1px solid #dee2e6; font-size: 0.85em; background: white; white-space: nowrap; }}
        .diag-cell {{ text-align: left !important; font-weight: 500; padding: 12px !important; line-height: 1.5; color: #2c3e50; white-space: normal !important; min-width: 420px; }}
        .color-alert-orange {{ background-color: #ffccbc !important; color: #bf360c !important; }}
        .badge-buy {{ background-color: #198754; color: white; padding: 4px 6px; }}
        .badge-sell {{ background-color: #ffc107; color: black; padding: 4px 6px; }}
        .legend-item {{ padding: 8px; border-radius: 6px; margin-bottom: 6px; border: 1px solid #eee; display: flex; align-items: center; font-size: 0.85em; background: white; }}
        .legend-icon {{ width: 35px; font-size: 1.2em; text-align: center; margin-right: 10px; }}
        #timer {{ color: #ffeb3b; font-weight: bold; font-size: 1.1em; }}
        .status-col {{ font-size: 1.4em; width: 50px; }}
    </style>
    <script>
        let timeLeft = 60;
        function updateTimer() {{
            document.getElementById('timer').innerText = timeLeft;
            if (timeLeft <= 0) {{ window.location.reload(); }}
            timeLeft--;
        }}
        setInterval(updateTimer, 1000);
        function manualRefresh() {{ window.location.reload(); }}
    </script>
    </head>
    <body><div class="container-fluid" style="max-width: 1750px;">
        <div class="header-box d-flex justify-content-between align-items-center">
            <h2 class="m-0">🚀 半導體「大戶動向」戰情室</h2>
            <div class="d-flex align-items-center">
                <div class="me-4 text-end">
                    <small>最後更新：{now_str}</small><br>
                    <span>系統將在 <span id="timer">60</span> 秒後自動刷新</span>
                </div>
                <button class="btn btn-light btn-sm text-primary fw-bold shadow-sm" onclick="manualRefresh()">🔄 立即刷新</button>
            </div>
        </div>
        <div class="table-responsive shadow-sm rounded mb-4">
            <table class="table table-hover table-bordered mb-0">
                <thead><tr>
                    <th>燈號</th><th>股票名稱</th><th>現價</th>
                    <th>技術支撐</th><th><span class="badge badge-buy">建議買入價</span></th><th>籌碼地板</th>
                    <th><span class="badge badge-sell">建議賣出價</span></th><th>停利防線</th>
                    <th>本益比</th><th>機構持股</th><th>內部持股</th><th>量比</th><th>趨勢斜率</th>
                    <th>📊 智慧診斷與操作建議</th>
                </tr></thead>
                <tbody>"""

    for r in results:
        html_all += f"""<tr class='{r['cls']}'>
            <td class='status-col'>{r['light']}</td>
            <td><b>{r['name']}</b></td><td>{r['price']}</td>
            <td>{r['tech_sup']}</td><td><b>{r['buy']}</b></td><td>{r['chip']}</td>
            <td><b>{r['sell']}</b></td><td>{r['stop']}</td>
            <td>{r['pe']}</td><td>{r['inst']}</td><td>{r['insider']}</td><td>{r['vol']}</td><td>{r['slope']}</td>
            <td class='diag-cell'>{r['status']}</td>
        </tr>"""

    html_all += f"""</tbody></table></div>
        <div class="row">
            <div class="col-md-4">
                <div class="p-3 bg-white rounded shadow-sm border-start border-success border-5 h-100">
                    <h6 class="fw-bold mb-3 text-success">📘 指標註解說明</h6>
                    <div class="small">
                        <p class="mb-2"><b>● 趨勢斜率 (%)</b>：以 10 日回歸計算，反映每日平均漲跌幅百分比。</p>
                        <p class="mb-2"><b>● 建議買入價</b>：結合技術面(下軌)與籌碼面(大戶成本)的黃金切入點。</p>
                        <p class="mb-2"><b>● 籌碼地板</b>：利用成交量分布計算出的大戶主要防守價位。</p>
                        <p class="mb-0"><b>● 停利防線</b>：動態防守位，保護利潤不被大幅回吐。</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="p-3 bg-white rounded shadow-sm border-start border-warning border-5 h-100">
                    <h6 class="fw-bold mb-3 text-warning">🚦 燈號對照表</h6>
                    <div class="legend-item color-alert-orange"><div class="legend-icon">🚨</div><div><b>大戶倒貨</b>：爆量但不漲，代表籌碼正在高檔轉手。</div></div>
                    <div class="legend-item table-info"><div class="legend-icon">⚠️</div><div><b>分批停利</b>：股價過熱逼近上軌，建議入袋為安。</div></div>
                    <div class="legend-item table-success"><div class="legend-icon">✅</div><div><b>買入訊號</b>：回測支撐區且斜率止穩，適合分批佈局。</div></div>
                    <div class="legend-item table-danger"><div class="legend-icon">☢️</div><div><b>破位停損</b>：擊穿關鍵技術位，趨勢轉空，需保命。</div></div>
                    <div class="legend-item table-secondary"><div class="legend-icon">💤</div><div><b>縮量整理</b>：交易清淡趨勢平緩，建議觀望暫不開倉。</div></div>
                    <div class="legend-item"><div class="legend-icon">🔎</div><div><b>正常整理</b>：於區間內正常波動，量能平穩。</div></div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="p-3 bg-white rounded shadow-sm border-start border-primary border-5 h-100">
                    <h6 class="fw-bold mb-3 text-primary">📰 即時新聞</h6>
                    <div style="max-height: 250px; overflow-y: auto;">
                        {all_news_html if all_news_html else "數據加載中..."}
                    </div>
                </div>
            </div>
        </div>
    </div></body></html>"""

    with open("stock_report.html", "w", encoding="utf-8") as f: f.write(html_all)

if __name__ == "__main__":
    run_monitor()
    webbrowser.open('file://' + os.path.realpath("stock_report.html"))
    last_min = -1
    while True:
        now = datetime.now()
        if now.second == 0 and now.minute != last_min:
            run_monitor()
            last_min = now.minute
        time.sleep(0.5)