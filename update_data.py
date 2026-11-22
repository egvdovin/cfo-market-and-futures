import yfinance as yf
import pandas as pd
from datetime import datetime

# Тикеры мировых фьючерсов (Yahoo Finance — работают на GitHub без гео-блокировок)
TICKERS = {
    'GC=F': 'Золото (Gold)',
    'BZ=F': 'Нефть Brent (Crude Oil)',
    'NG=F': 'Природный газ (Natural Gas)',
    'KC=F': 'Кофе (Coffee)',
    'CC=F': 'Какао (Cocoa)'
}

def fetch_futures():
    rows = []
    for ticker, name in TICKERS.items():
        try:
            asset = yf.Ticker(ticker)
            # Забираем историю за последние 5 торговых дней
            hist = asset.history(period='5d')
            if not hist.empty:
                last_row = hist.iloc[-1]
                prev_row = hist.iloc[-2] if len(hist) > 1 else last_row
                
                last_price = round(float(last_row['Close']), 2)
                prev_price = round(float(prev_row['Close']), 2)
                change_pct = round(((last_price - prev_price) / prev_price) * 100, 2) if prev_price else 0.0
                
                rows.append({
                    'asset_name': name,
                    'ticker': ticker,
                    'trade_date': last_row.name.strftime('%Y-%m-%d'),
                    'open': round(float(last_row['Open']), 2),
                    'high': round(float(last_row['High']), 2),
                    'low': round(float(last_row['Low']), 2),
                    'close_price': last_price,
                    'change_pct': change_pct,
                    'volume': int(last_row['Volume']),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
                print(f"Успешно загружен {name}: {last_price}")
        except Exception as e:
            print(f"Ошибка по {ticker}: {e}")

    df = pd.DataFrame(rows)
    df.to_csv('moex_futures.csv', index=False, encoding='utf-8-sig')
    print(f"ИТОГО сохранено фьючерсов: {len(df)}")

if __name__ == '__main__':
    fetch_futures()
