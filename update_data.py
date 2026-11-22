import requests
import pandas as pd
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Базовые коды активов на срочном рынке Мосбиржи (FORTS)
FUTURES_MAP = {
    'GOLD': 'Золото (GOLD)',
    'BR': 'Нефть Brent (BR)',
    'NG': 'Природный газ (NG)',
    'COFFEE': 'Кофе (COFFEE)',
    'KC': 'Кофе (COFFEE)',
    'COCOA': 'Какао (COCOA)',
    'CC': 'Какао (COCOA)'
}

def fetch_futures():
    url = 'https://moex.com'
    params = {'iss.meta': 'off', 'iss.only': 'securities,marketdata'}
    futures_rows = []
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=25).json()
        sec_cols = resp['securities']['columns']
        sec_data = resp['securities']['data']
        md_cols = resp['marketdata']['columns']
        md_data = resp['marketdata']['data']
        
        df_sec = pd.DataFrame(sec_data, columns=sec_cols)
        df_md = pd.DataFrame(md_data, columns=md_cols)
        df = pd.merge(df_sec, df_md, on='SECID')
        
        print("Доступные базовые активы на MOEX (пример):", df['ASSETCODE'].dropna().unique()[:20])
        
        for _, row in df.iterrows():
            asset_code = str(row.get('ASSETCODE', '')).upper()
            if asset_code in FUTURES_MAP:
                # Берем последнюю цену, а если торги закрыты (выходной) — расчетную цену предыдущего дня
                price = row.get('LAST') or row.get('SETTLEPRICE') or row.get('PREVPRICE')
                
                futures_rows.append({
                    'asset_group': FUTURES_MAP[asset_code],
                    'asset_code': asset_code,
                    'ticker': row.get('SECID'),
                    'short_name': row.get('SHORTNAME'),
                    'expiration_date': row.get('LASTTRADEDATE'),
                    'price': price,
                    'prev_settle_price': row.get('PREVPRICE'),
                    'change_pct': row.get('LASTTOPREVPRICE'),
                    'volume_contracts': row.get('VOLTODAY') or 0,
                    'open_interest': row.get('OPENPOSITION') or 0,
                    'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
    except Exception as e:
        print(f"Ошибка MOEX: {e}")

    df_fut = pd.DataFrame(futures_rows)
    df_fut.to_csv('moex_futures.csv', index=False, encoding='utf-8-sig')
    print(f"ИТОГО сохранено контрактов фьючерсов: {len(df_fut)}")


def fetch_vacancies():
    vacancies = []
    # Используем открытое API Habr Career (не блокирует зарубежные IP GitHub)
    url = 'https://habr.com'
    
    for page in range(1, 6):
        params = {'q': 'Финансовый директор', 'type': 'all', 'page': page}
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=25)
            if resp.status_code != 200:
                print(f"Статус ответа вакансий: {resp.status_code}")
                break
            data = resp.json()
            items = data.get('list', [])
            if not items:
                break
                
            for item in items:
                salary = item.get('salary') or {}
                locations = [loc.get('title') for loc in item.get('locations', [])]
                skills = [s.get('title') for s in item.get('skills', [])]
                
                vacancies.append({
                    'id': item.get('id'),
                    'job_name': item.get('title'),
                    'company': item.get('company', {}).get('title'),
                    'city': ', '.join(locations) if locations else 'Удаленно / Не указан',
                    'remote': item.get('remoteWork'),
                    'salary_from': salary.get('from'),
                    'salary_to': salary.get('to'),
                    'currency': salary.get('currency'),
                    'skills': ', '.join(skills),
                    'published_at': item.get('publishedDate', {}).get('date'),
                    'url': f"https://habr.com{item.get('href', '')}",
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
        except Exception as e:
            print(f"Ошибка вакансий: {e}")

    df_vac = pd.DataFrame(vacancies)
    df_vac.to_csv('cfo_vacancies.csv', index=False, encoding='utf-8-sig')
    print(f"ИТОГО сохранено вакансий: {len(df_vac)}")


if __name__ == '__main__':
    fetch_futures()
    fetch_vacancies()
