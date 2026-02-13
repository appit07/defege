import requests
import json
import re
import time
from datetime import datetime
from telegram import Bot, error

# ==================== JOUW GEGEVENS ====================
BOT_TOKEN = "8541741403:AAGrz25dmNRHgKhEY9y0quLuqAlmf9501-M"
CHAT_ID = 5863829002
MAX_PRICE = 80
POSTCODE = "2311TP"
MAX_DISTANCE_KM = 80
# =======================================================

bot = Bot(token=BOT_TOKEN)
seen_ids = set()

def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown', disable_web_page_preview=False)
    except error.TelegramError as e:
        print(f"Telegram fout: {e}")

def search_marktplaats():
    ads = []
    try:
        url = "https://www.marktplaats.nl/lrp/api/search"
        params = {
            'query': 'liebherr vriezer',
            'limit': 30,
            'postcode': POSTCODE,
            'distanceMeters': MAX_DISTANCE_KM * 1000,
            'priceTo': MAX_PRICE * 100,
            'sortBy': 'DATE_DESC'
        }
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            for listing in data.get('listings', []):
                try:
                    title = listing.get('title', '')
                    if 'liebherr' not in title.lower() or 'vriezer' not in title.lower():
                        continue
                    price = listing.get('priceInfo', {}).get('priceCents', 0) / 100
                    if price > MAX_PRICE:
                        continue
                    city = listing.get('location', {}).get('cityName', 'Onbekend')
                    distance = listing.get('location', {}).get('distance', 0) / 1000
                    if distance > MAX_DISTANCE_KM:
                        continue
                    ads.append({
                        'id': listing['itemId'],
                        'title': title,
                        'price': price,
                        'location': city,
                        'distance': round(distance, 1),
                        'link': f"https://www.marktplaats.nl/v/{listing['itemId']}"
                    })
                except:
                    continue
    except Exception as e:
        print(f"API error: {e}")
    
    # Fallback
    if not ads:
        try:
            url = "https://www.marktplaats.nl/q/liebherr+vriezer/"
            params = {'priceTo': MAX_PRICE, 'postcode': POSTCODE, 'distance': MAX_DISTANCE_KM}
            resp = requests.get(url, params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if resp.status_code == 200:
                ids = re.findall(r'data-item-id="(\d+)"', resp.text)
                ids += re.findall(r'/v/(\d+)/', resp.text)
                for aid in set(ids)[:20]:
                    ads.append({
                        'id': aid,
                        'title': 'Liebherr vriezer',
                        'price': 0.0,
                        'location': 'Onbekend',
                        'distance': 0.0,
                        'link': f"https://www.marktplaats.nl/v/{aid}"
                    })
        except Exception as e:
            print(f"Fallback error: {e}")
    
    return ads

def main_loop():
    global seen_ids
    print(f"\n[{datetime.now()}] Controleren...")
    ads = search_marktplaats()
    new_ads = [ad for ad in ads if ad['id'] not in seen_ids]
    
    for ad in new_ads:
        seen_ids.add(ad['id'])
    
    if new_ads:
        msg = f"🎯 *{len(new_ads)} nieuwe Liebherr vriezer(s) ≤ €{MAX_PRICE}!*\n\n"
        for ad in new_ads[:5]:
            price_str = f"€{ad['price']:.2f}" if ad['price'] else "Prijs onbekend"
            loc_str = f"{ad['location']} ({ad['distance']:.0f}km)" if ad['distance'] else ad['location']
            msg += f"• [{ad['title'][:50]}]({ad['link']})\n  {price_str} – {loc_str}\n\n"
        if len(new_ads) > 5:
            msg += f"*... en {len(new_ads)-5} andere.*\n"
        msg += f"\n🔗 [Alle resultaten](https://www.marktplaats.nl/q/liebherr+vriezer/?priceTo={MAX_PRICE}&postcode={POSTCODE}&distance={MAX_DISTANCE_KM})"
        send_message(msg)
        print(f"✅ {len(new_ads)} nieuw")
    else:
        print("ℹ️ Geen nieuwe")

if __name__ == "__main__":
    send_message(f"🤖 *Bot gestart op Railway*\n\n✅ Zoekt elke 5 minuten naar Liebherr vriezers ≤ €{MAX_PRICE} binnen {MAX_DISTANCE_KM}km van Leiden.")
    while True:
        try:
            main_loop()
        except Exception as e:
            send_message(f"❌ *Fout*\n`{str(e)[:200]}`")
        time.sleep(300)
