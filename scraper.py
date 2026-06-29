import json, re, os
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PRICE_REGEX = re.compile(r'(\d+[.,]\d{2})\s*€')

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def fix_url(base, src):
    if not src or src.startswith('data:'): return None
    if src.startswith('//'): return 'https:' + src
    if src.startswith('http'): return src
    return urljoin(base, src)

def scrape_site(site):
    print(f"Scrapeando: {site['name']}...")
    session = requests.Session(impersonate="chrome120")
    try:
        res = session.get(site['url'], timeout=30)
        if res.status_code == 403:
            print(f"Bloqueado (403): {site['name']}")
            return []
    except Exception as e:
        print(f"Error de conexion: {e}")
        return []

    soup = BeautifulSoup(res.text, 'html.parser')
    products = []
    
    # Si está vacío, usa 'div' por defecto para evitar errores
    product_sel = site.get('product_selector') or 'div'
    cards = soup.select(product_sel)
    
    for card in cards:
        item = {"site": site['name'], "site_id": site['id']}
        
        name_sel = site.get('name_selector') or 'h1, h2, h3, a, span'
        name_el = card.select_one(name_sel)
        item['name'] = name_el.get_text(strip=True) if name_el else ""
        
        price_sel = site.get('price_selector')
        price_el = card.select_one(price_sel) if price_sel else card
        match = PRICE_REGEX.search(price_el.get_text(strip=True))
        item['price'] = float(match.group(1).replace(',', '.')) if match else 0
        
        img_sel = site.get('image_selector') or 'img'
        img_el = card.select_one(img_sel)
        if img_el:
            src = img_el.get('src') or img_el.get('data-src') or img_el.get('data-lazy-src')
            item['image'] = fix_url(site['url'], src)
        else:
            item['image'] = None
            
        measure_sel = site.get('measure_selector')
        if measure_sel:
            measure_el = card.select_one(measure_sel)
            item['measure'] = measure_el.get_text(strip=True) if measure_el else ""
        else:
            item['measure'] = ""
        
        if item['name'] and item['price'] > 0:
            products.append(item)
            
    print(f"Extraidos: {len(products)} productos en {site['name']}")
    return products

def main():
    config = load_config()
    os.makedirs('data', exist_ok=True)
    all_products = []
    for site in config:
        all_products.extend(scrape_site(site))
        
    with open('data/products.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"Total guardado: {len(all_products)} productos")

if __name__ == "__main__":
    main()
