# bot.py - LIEBHERR VRIEZER BOT voor Railway
import requests
import json
import re
import time
from datetime import datetime

# ==================== JOUW GEGEVENS ====================
BOT_TOKEN = "8541741403:AAGrz25dmNRHgKhEY9y0quLuqAlmf9501-M"
CHAT_ID = 5863829002
MAX_PRICE = 80
POSTCODE = "2311TP"
MAX_DISTANCE_KM = 80
CHECK_INTERVAL = 3  # minuten (jij wilt elke 3 minuten)
# =======================================================

print(f"\n{'='*60}")
print(f"LIEBHERR VRIEZER BOT - GESTART")
print(f"{'='*60}")
print(f"📱 Chat ID: {CHAT_ID}")
print(f"💰 Max prijs: €{MAX_PRICE}")
print(f"📍 Locatie: {MAX_DISTANCE_KM}km van {POSTCODE}")
print(f"⏰ Check interval: elke {CHECK_INTERVAL} minuten")
print(f"{'='*60}\n")

# Geziene advertenties (in RAM)
seen_ids = set()

def send_telegram(text):
    """Stuur bericht naar Telegram (directe API, werkt altijd)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️ Telegram fout: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"⚠️ Fout bij versturen: {e}")
        return False

def search_marktplaats():
    """Zoek naar Liebherr vriezers op Marktplaats"""
    ads = []
    
    # --- EERSTE POGING: API ---
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
                    if 'liebherr' in title.lower() and 'vriezer' in title.lower():
                        price = listing.get('priceInfo', {}).get('priceCents', 0) / 100
                        if price <= MAX_PRICE:
                            city = listing.get('location', {}).get('cityName', 'Onbekend')
                            distance = listing.get('location', {}).get('distance', 0) / 1000
                            if distance <= MAX_DISTANCE_KM:
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
        print(f"API error (niet erg): {e}")
    
    # --- TWEEDE POGING: FALLBACK HTML ---
    if not ads:
        try:
            url = "https://www.marktplaats.nl/q/liebherr+vriezer/"
            params = {
                'priceTo': str(MAX_PRICE),
                'postcode': POSTCODE,
                'distance': str(MAX_DISTANCE_KM)
            }
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                # Zoek naar advertentie IDs
                ids = re.findall(r'data-item-id="(\d+)"', resp.text)
                ids += re.findall(r'/v/(\d+)/', resp.text)
                ids = set(ids)
                
                for aid in list(ids)[:20]:
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

def check_and_notify():
    """Controleer op nieuwe advertenties en stuur notificatie"""
    global seen_ids
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Controleren...")
    
    ads = search_marktplaats()
    print(f"📊 {len(ads)} advertenties gevonden")
    
    # Filter nieuwe
    new_ads = []
    for ad in ads:
        if ad['id'] not in seen_ids:
            new_ads.append(ad)
            seen_ids.add(ad['id'])
            print(f"🆕 Nieuw: {ad['id']}")
    
    # Stuur notificatie als er nieuwe zijn
    if new_ads:
        msg = f"🎯 *{len(new_ads)} nieuwe Liebherr vriezer(s) ≤ €{MAX_PRICE}!*\n\n"
        
        for ad in new_ads[:5]:
            price_str = f"€{ad['price']:.2f}" if ad['price'] else "Prijs onbekend"
            loc_str = f"{ad['location']} ({ad['distance']:.0f}km)" if ad['distance'] else ad['location']
            msg += f"• [{ad['title'][:50]}]({ad['link']})\n  {price_str} – {loc_str}\n\n"
        
        if len(new_ads) > 5:
            msg += f"*... en {len(new_ads)-5} andere.*\n"
        
        msg += f"\n🔗 [Alle resultaten](https://www.marktplaats.nl/q/liebherr+vriezer/?priceTo={MAX_PRICE}&postcode={POSTCODE}&distance={MAX_DISTANCE_KM})"
        
        if send_telegram(msg):
            print(f"✅ Notificatie verstuurd voor {len(new_ads)} nieuwe advertentie(s)")
    else:
        print("ℹ️ Geen nieuwe advertenties")
        
        # OPTIONEEL: Elke 30 minuten een "ik leef nog" bericht
        if int(time.time()) % 1800 < CHECK_INTERVAL * 60:
            send_telegram(f"🔍 *Bot actief*\n\nGeen nieuwe vriezers gevonden.\nVolgende controle over {CHECK_INTERVAL} minuten.")

def main():
    """Hoofdloop - draait elke CHECK_INTERVAL minuten"""
    print("🚀 Bot wordt gestart...")
    
    # Stuur startbericht
    start_msg = f"""
🤖 *Liebherr Vriezer Bot gestart op Railway!*

✅ Checkt elke {CHECK_INTERVAL} minuten
🔍 Zoekopdracht: Liebherr vriezer
💰 Maximumprijs: €{MAX_PRICE}
📍 Binnen {MAX_DISTANCE_KM}km van {POSTCODE}

*Status:* ✅ Actief
"""
    send_telegram(start_msg)
    
    # Oneindige loop
    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            check_and_notify()
            
            print(f"\n⏰ Wachten {CHECK_INTERVAL} minuten...")
            time.sleep(CHECK_INTERVAL * 60)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot gestopt door gebruiker")
            send_telegram("🛑 *Bot gestopt*")
            break
        except Exception as e:
            print(f"\n❌ Fout in main loop: {e}")
            send_telegram(f"❌ *Bot fout*\n`{str(e)[:200]}`")
            time.sleep(60)  # Wacht 1 minuut bij fout

if __name__ == "__main__":
    main()
