import json
import urllib.request
import urllib.parse
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- ПОТОК 1: ФЬЮЧЕРСЫ ---
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


# --- ПОТОК 2: ВАКАНСИИ CFO (ОТКРЫТОЕ API HH.RU) ---
def fetch_cfo_vacancies():
    # Ориентировочные курсы для приведения валютных вилок к рублям
    RATES = {'RUR': 1.0, 'RUB': 1.0, 'USD': 95.0, 'EUR': 103.0}
    rows = []

    # Забираем до 5 страниц по 100 вакансий (до 500 актуальных вакансий по РФ, area=113)
    for page in range(5):
        params = urllib.parse.urlencode({
            'text': 'Финансовый директор',
            'area': 113,       # Россия (Москва, СПб и крупные города РФ)
            'per_page': 100,
            'page': page
        })
        url = f"https://hh.ru?{params}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'CFOMarketPortfolioDashboard/1.0 (analytics-portfolio@example.com)'
        })

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data.get('items', [])
                if not items:
                    break

                for item in items:
                    sal = item.get('salary') or {}
                    cur = sal.get('currency') or 'RUR'
                    rate = RATES.get(cur, 1.0)
                    gross_factor = 0.87 if sal.get('gross') else 1.0

                    s_from = sal.get('from')
                    s_to = sal.get('to')

                    pay_from = round(s_from * rate * gross_factor, 0) if s_from else None
                    pay_to = round(s_to * rate * gross_factor, 0) if s_to else None

                    if pay_from and pay_to:
                        salary_avg = round((pay_from + pay_to) / 2, 0)
                    elif pay_from:
                        salary_avg = pay_from
                    elif pay_to:
                        salary_avg = pay_to
                    else:
                        salary_avg = None

                    city = (item.get('area') or {}).get('name', 'Не указан')
                    company = (item.get('employer') or {}).get('name', 'Не указана')
                    experience = (item.get('experience') or {}).get('name', 'Не указан')
                    work_type = (item.get('employment') or {}).get('name', 'Не указан')
                    work_format = (item.get('schedule') or {}).get('name', 'Не указан')
                    pub_raw = item.get('published_at', '')
                    pub_date = pub_raw[:10] if pub_raw else ''

                    rows.append({
                        'vacancy_id': item.get('id'),
                        'title': item.get('name', ''),
                        'company': company,
                        'city': city,
                        'salary_from': pay_from,
                        'salary_to': pay_to,
                        'salary_avg': salary_avg,
                        'currency': 'RUR',
                        'experience': experience,
                        'work_type': work_type,
                        'work_format': work_format,
                        'published_date': pub_date,
                        'url': item.get('alternate_url', ''),
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })

                if page >= data.get('pages', 1) - 1:
                    break
        except Exception as e:
            print(f"Ошибка при запросе HH API (стр. {page}): {e}")
            break

    df = pd.DataFrame(rows)
    if not df.empty:
        df.drop_duplicates(subset=['vacancy_id'], inplace=True)
    df.to_csv('cfo_vacancies.csv', index=False, encoding='utf-8-sig')
    print(f"ИТОГО сохранено вакансий CFO: {len(df)}")


if __name__ == '__main__':
    fetch_futures()
    fetch_cfo_vacancies()
