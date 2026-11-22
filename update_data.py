import requests
import pandas as pd
from datetime import datetime

HEADERS = {'User-Agent': 'CFO-Portfolio-Dashboard/1.0'}

# Коды регионов РФ для крупных городов (Москва, СПб, Татарстан, Свердловская, Новосибирская, Нижегородская обл., Краснодарский край)
TARGET_REGIONS = {
    '77': 'Москва',
    '78': 'Санкт-Петербург',
    '16': 'Республика Татарстан',
    '66': 'Свердловская область',
    '54': 'Новосибирская область',
    '52': 'Нижегородская область',
    '23': 'Краснодарский край'
}

# Базовые тикеры фьючерсов на срочном рынке Мосбиржи (FORTS)
FUTURES_MAP = {
    'GOLD': 'Золото (GOLD)',
    'BR': 'Нефть Brent (BR)',
    'NG': 'Природный газ (NG)',
    'COFFEE': 'Кофе (COFFEE)',
    'COCOA': 'Какао (COCOA)'
}

def fetch_vacancies():
    vacancies = []
    # Запрашиваем вакансии по ключевому слову "Финансовый директор"
    url = 'http://trudvsem.ru'
    params = {'text': 'Финансовый директор', 'limit': 100}
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
        data = resp.json()
        items = data.get('results', {}).get('vacancies', [])
        
        for entry in items:
            vac = entry.get('vacancy', {})
            reg_code = str(vac.get('region', {}).get('region_code', ''))[:2]
            
            # Фильтруем только Москву и крупнейшие регионы
            if reg_code in TARGET_REGIONS:
                vacancies.append({
                    'id': vac.get('id'),
                    'job_name': vac.get('job-name'),
                    'region': TARGET_REGIONS[reg_code],
                    'company': vac.get('company', {}).get('name'),
                    'salary_min': vac.get('salary_min'),
                    'salary_max': vac.get('salary_max'),
                    'schedule': vac.get('schedule'),
                    'employment': vac.get('employment'),
                    'experience': vac.get('requirement', {}).get('experience'),
                    'creation_date': vac.get('creation-date'),
                    'vac_url': vac.get('vac_url'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
    except Exception as e:
        print(f"Ошибка при загрузке вакансий: {e}")

    df_vac = pd.DataFrame(vacancies)
    df_vac.to_csv('cfo_vacancies.csv', index=False, encoding='utf-8-sig')
    print(f"Сохранено вакансий: {len(df_vac)}")


def fetch_futures():
    # Забираем все активные фьючерсы срочного рынка (FORTS) с MOEX ISS API
    url = 'https://moex.com'
    params = {'iss.meta': 'off', 'iss.only': 'securities,marketdata'}
    futures_rows = []
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=20).json()
        sec_cols = resp['securities']['columns']
        sec_data = resp['securities']['data']
        md_cols = resp['marketdata']['columns']
        md_data = resp['marketdata']['data']
        
        df_sec = pd.DataFrame(sec_data, columns=sec_cols)
        df_md = pd.DataFrame(md_data, columns=md_cols)
        
        # Объединяем справочник контрактов с текущими рыночными данными
        df = pd.merge(df_sec, df_md, on='SECID')
        
        for asset_code, asset_name in FUTURES_MAP.items():
            subset = df[df['ASSETCODE'] == asset_code].copy()
            for _, row in subset.iterrows():
                futures_rows.append({
                    'asset_group': asset_name,
                    'asset_code': asset_code,
                    'ticker': row.get('SECID'),
                    'short_name': row.get('SHORTNAME'),
                    'expiration_date': row.get('LASTTRADEDATE'),
                    'last_price': row.get('LAST'),
                    'open_price': row.get('OPEN'),
                    'high_price': row.get('HIGH'),
                    'low_price': row.get('LOW'),
                    'change_pct': row.get('LASTTOPREVPRICE'),
                    'volume_contracts': row.get('VOLTODAY'),
                    'open_interest': row.get('OPENPOSITION'),
                    'update_time': row.get('UPDATETIME'),
                    'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
    except Exception as e:
        print(f"Ошибка при загрузке фьючерсов: {e}")

    df_fut = pd.DataFrame(futures_rows)
    df_fut.to_csv('moex_futures.csv', index=False, encoding='utf-8-sig')
    print(f"Сохранено контрактов фьючерсов: {len(df_fut)}")


if __name__ == '__main__':
    fetch_vacancies()
    fetch_futures()
