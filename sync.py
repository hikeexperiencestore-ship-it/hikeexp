import requests
import json

def test_api():
    url = "https://www.majellando.it/it/booking_dates_and_availabilities/323237"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    print("🚀 Avvio richiesta di test all'API di Majellando...")
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            dati = response.json()
            # Questo stamperà il JSON formattato nei log di GitHub
            print(json.dumps(dati, indent=4, ensure_ascii=False))
        else:
            print(f"❌ Errore API: Status Code {response.status_code}")
    except Exception as e:
        print(f"❌ Errore durante la chiamata: {e}")

if __name__ == "__main__":
    test_api()
