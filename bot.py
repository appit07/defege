\# bot.py - SYNCHRONE versie voor Railway
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
# =======================================================

# Geen asynchrone code! Gebruik gewone import
try:
    from telegram import Bot
    from telegram.error import TelegramError
    # Synchrone bot
    bot = Bot(token=BOT_TOKEN)
    print(f"✅ Telegram bot geladen")
except Exception as e:
    print(f"❌ Telegram import fout: {e}")
    bot = None

seen_ids = set()

def send_message(text):
    """Stuur synchroon bericht naar Telegram"""
    if not bot:
        print("⚠️ Bot niet beschikbaar, geen bericht verzonden")
        return False
    
    try:
        # Synchrone call - geen await!
        bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode='Markdown',
            disable_web_page_preview=False
        )
        print(f"✅ Bericht verzonden")
        return True
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")
        return False
    except Exception as e:
        print(f"❌ Fout: {e}")
        return False

def search_marktplaats():
    """Zoek naar Liebherr vriezers"""
    ads = []
    
    # API call
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
    """Controleer nieuwe advertenties"""
    global seen_ids
    print(f"\n[{datetime.now()}] Controleren...")
    
    ads = search_marktplaats()
    
    # Nieuwe ads vinden
    new_ads = []
    for ad in ads:
        if ad['id'] not in seen_ids:
            new_ads.append(ad)
            seen_ids.add(ad['id'])
            print(f"🆕 Nieuw: {ad['id']}")
    
    # Notificatie sturen
    if new_ads:
        msg = f"🎯 *{len(new_ads)} nieuwe Liebherr vriezer(s) ≤ €{MAX_PRICE}!*\n\n"
        for ad in new_ads[:5]:
            price = f"€{ad['price']:.2f}" if ad['price'] else "Prijs onbekend"
            loc = f"{ad['location']} ({ad['distance']:.0f}km)" if ad['distance'] else ad['location']
            msg += f"• [{ad['title'][:50]}]({ad['link']})\n  {price} – {loc}\n\n"
        if len(new_ads) > 5:
            msg += f"*... en {len(new_ads)-5} andere.*\n"
        msg += f"\n🔗 [Alle resultaten](https://www.marktplaats.nl/q/liebherr+vriezer/?priceTo={MAX_PRICE}&postcode={POSTCODE}&distance={MAX_DISTANCE_KM})"
        
        send_message(msg)
        print(f"✅ {len(new_ads)} nieuw, notificatie verstuurd")
    else:
        print("ℹ️ Geen nieuwe advertenties")
        # Elke 30 minuten een heartbeat
        if int(time.time()) % 1800 < 300:
            send_message(f"🔍 *Bot actief*\n\nGeen nieuwe vriezers gevonden.\nVolgende controle over 5 minuten.")

if __name__ == "__main__":
    print("="*60)
    print("LIEBHERR VRIEZER BOT - RAILWAY")
    print("="*60)
    print(f"📱 Chat ID: {CHAT_ID}")
    print(f"💰 Max prijs: €{MAX_PRICE}")
    print(f"📍 Locatie: {MAX_DISTANCE_KM}km van {POSTCODE}")
    print("="*60)
    
    # Test Telegram verbinding
    if send_message("🤖 *Bot gestart op Railway*\n\n✅ Zoekt naar Liebherr vriezers ≤ €80 binnen 80km van Leiden."):
        print("✅ Telegram verbinding OK!")
    else:
        print("❌ Telegram verbinding MISLUKT!")
    
    # Oneindige loop
    counter = 0
    while True:
        try:
            counter += 1
            print(f"\n--- Controle #{counter} ---")
            main_loop()
        except Exception as e:
            print(f"❌ Fout: {e}")
            send_message(f"❌ *Bot fout*\n`{str(e)[:200]}`")
        
        print("\n⏰ Wachten 5 minuten...")
        time.sleep(300)
