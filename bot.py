# bot.py - ULTRA SIMPELE TEST
import requests
import time
import sys

print("="*60)
print("TELEGRAM TEST BOT")
print("="*60)

# ========== JOUW GEGEVENS ==========
BOT_TOKEN = "8541741403:AAGrz25dmNRHgKhEY9y0quLuqAlmf9501-M"
CHAT_ID = 5863829002
# ===================================

print(f"📱 Chat ID: {CHAT_ID}")
print(f"🔑 Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")

def send_telegram_direct(text):
    """Directe API call - geen package nodig!"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    try:
        print(f"📤 Versturen naar Telegram...")
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ ✅ ✅ GELUKT! Bericht verzonden!")
                return True
            else:
                print(f"❌ Telegram zegt: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Geen internetverbinding!")
        return False
    except Exception as e:
        print(f"❌ Fout: {e}")
        return False

def main():
    print("\n🚀 Test starten...")
    
    # Test 1: Check of token werkt via getMe
    try:
        me_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        me_response = requests.get(me_url, timeout=10)
        me_data = me_response.json()
        
        if me_data.get('ok'):
            bot_name = me_data['result'].get('first_name', 'Unknown')
            print(f"✅ Token werkt! Bot naam: {bot_name}")
        else:
            print(f"❌ Token FOUT: {me_data.get('description')}")
            return
    except Exception as e:
        print(f"❌ Kan Telegram API niet bereiken: {e}")
        return
    
    # Test 2: Stuur bericht
    test_text = """
🧪 *TESTBERICHT VAN RAILWAY*

✅ Deze test gebruikt *directe API* (geen telegram package!)
⏰ Tijd: {}
📍 Server: Railway

*Als je dit ziet, werkt alles!* 🎉
""".format(time.strftime('%H:%M:%S'))
    
    if send_telegram_direct(test_text):
        print("\n🎉 GEFELICITEERD! Telegram werkt!")
    else:
        print("\n❌ TEST MISLUKT - Check je token en chat ID")
    
    print("\n🏁 Test gedaan. Bot stopt nu.")

if __name__ == "__main__":
    main()
