import os
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


# --- ПОТОК 2: ВАКАНСИИ CFO (SUPERJOB API) ---
def fetch_cfo_vacancies():
    api_key = os.environ.get('SUPERJOB_API_KEY')
    if not api_key:
        print("ВНИМАНИЕ: Не найден секрет SUPERJOB_API_KEY в переменных окружения!")
        return

    rows = []
    # Забираем до 3 страниц (по 100 вакансий) по запросу "Финансовый директор" в РФ (c=1)
    for page in range(3):
        params = urllib.parse.urlencode({
            'keyword': 'Финансовый директор',
            'c': 1,          # Россия (Москва, СПб и все крупные города)
            'count': 100,
            'page': page
        })
        url = f"https://superjob.ru?{params}"
        req = urllib.request.Request(url, headers={
            'X-Api-App-Id': api_key,
            'User-Agent': 'Mozilla/5.0'
        })

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                objects = data.get('objects', [])
                if not objects:
                    break

                for item in objects:
                    pay_from = item.get('payment_from') or 0
                    pay_to = item.get('payment_to') or 0
                    
                    # Расчёт средней вилки в рублях (если зарплата указана)
                    if pay_from > 0 and pay_to > 0:
                        salary_avg = round((pay_from + pay_to) / 2, 0)
                    elif pay_from > 0:
                        salary_avg = pay_from
                    elif pay_to > 0:
                        salary_avg = pay_to
                    else:
                        salary_avg = None

                    town = (item.get('town') or {}).get('title', 'Не указан')
                    experience = (item.get('experience') or {}).get('title', 'Не указан')
                    work_type = (item.get('type_of_work') or {}).get('title', 'Не указан')
                    place_of_work = (item.get('place_of_work') or {}).get('title', 'Не указан')
                    company = (item.get('client') or {}).get('title') or item.get('firm_name') or 'Конфиденциально'
                    
                    pub_ts = item.get('date_published')
                    pub_date = datetime.fromtimestamp(pub_ts).strftime('%Y-%m-%d') if pub_ts else ''

                    rows.append({
                        'vacancy_id': item.get('id'),
                        'title': item.get('profession', ''),
                        'company': company,
                        'city': town,
                        'salary_from': pay_from if pay_from > 0 else None,
                        'salary_to': pay_to if pay_to > 0 else None,
                        'salary_avg': salary_avg,
                        'currency': item.get('currency', 'rub'),
                        'experience': experience,
                        'work_type': work_type,
                        'work_format': place_of_work,
                        'published_date': pub_date,
                        'url': item.get('link', ''),
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })

                if not data.get('more'):
                    break
        except Exception as e:
            print(f"Ошибка при запросе SuperJob API (стр. {page}): {e}")
            break

    df = pd.DataFrame(rows)
    if not df.empty:
        df.drop_duplicates(subset=['vacancy_id'], inplace=True)
    df.to_csv('cfo_vacancies.csv', index=False, encoding='utf-8-sig')
    print(f"ИТОГО сохранено вакансий CFO: {len(df)}")


if __name__ == '__main__':
    fetch_futures()
    fetch_cfo_vacancies()
