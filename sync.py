import os
import requests
from bs4 import BeautifulSoup
import re

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")
PASSWORD_ADMIN = os.environ.get("PASSWORD_ADMIN")

# Associazione Nome Tour (Colonna F) -> Link Majellando
MAPPA_URLS = {
    "Tesori d'Abruzzo - Bominaco": "https://www.majellando.it/it/experience/e-bike-tra-i-tesori-dabruzzo_323237",
    "Da Barisciano a Fontecchio": "https://www.majellando.it/it/experience/in-ebike-dal-gran-sasso-a-fontecchio_398778",
    "Campo Imperatore - Piccolo Tibet": "https://www.majellando.it/it/experience/e-bike-sul-tibet-dabruzzo_961",
    "Campo Imperatore e i Tre Laghi": "https://www.majellando.it/it/experience/e-bike-a-campo-imperatore-e-i-tre-laghi-in-abruzzo_384814",
    "Rocca Calascio": "https://www.majellando.it/it/experience/e-bike-al-castello-di-rocca-calascio_502"
}

MESI = {
    "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04",
    "maggio": "05", "giugno": "06", "luglio": "07", "agosto": "08",
    "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12"
}

import datetime  # Importa la libreria per le date (da mettere in cima al file se non c'è)

def formatta_data(giorno, mese, anno):
    giorno_str = str(giorno).zfill(2)
    mese_str = MESI.get(str(mese).lower().strip(), "00")
    
    anno_str = str(anno).strip()
    # Se l'anno è vuoto, prende automaticamente l'anno corrente del server (2026, 2027, etc.)
    if not anno_str or anno_str == "None" or anno_str == "null":
        anno_str = str(datetime.date.today().year)
        
    return f"{giorno_str}.{mese_str}.{anno_str}"

def ottieni_calendario_attivo():
    payload = {
        "action": "get_calendario_attivo",
        "password": PASSWORD_ADMIN
    }
    try:
        res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        dati = res.json()
        if dati.get("success"):
            return dati.get("tours", [])
        else:
            print(f"⚠️ Errore lettura calendario: {dati.get('error')}")
            return []
    except Exception as e:
        print(f"❌ Errore Google Script: {e}")
        return []

def ottieni_posti_totali(id_tour):
    payload = {
        "action": "get_posti_totali",
        "password": PASSWORD_ADMIN,
        "idTour": str(id_tour)
    }
    try:
        res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        dati = res.json()
        if dati.get("success"):
            return int(dati.get("posti_totali"))
        return None
    except Exception as e:
        print(f"❌ Errore lettura posti: {e}")
        return None

import re
import requests

def estrai_disponibilita(url, data_target):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    try:
        # Estraggo l'ID del tour dall'URL originale (es. da "experience_323237" prendo "323237")
        id_match = re.search(r"_(\d+)(?:\b|/|\?|$)", url)
        if not id_match:
            print(f"❌ Impossibile estrarre l'ID del tour dall'URL: {url}")
            return 0
        
        tour_id = id_match.group(1)
        api_url = f"https://www.majellando.it/it/booking_dates_and_availabilities/{tour_id}"
        
        # Interroghiamo direttamente l'API con una richiesta POST
        response = requests.post(api_url, headers=headers)
        response.raise_for_status()
        
        dati = response.json()
        
        # Convertiamo la tua data target (DD.MM.YYYY) nel formato ISO (YYYY-MM-DD)
        # Esempio: "18.07.2026" -> "2026-07-18"
        giorno, mese, anno = data_target.split('.')
        data_cercata = f"{anno}-{mese}-{giorno}"
        
        # Cerchiamo la data dentro l'elenco ricevuto dall'API
        for evento in dati.get("data", []):
            # Il campo "from" nel JSON è simile a "2026-07-18T09:30:00+02:00"
            if evento.get("from", "").startswith(data_cercata):
                # Trovata! Restituiamo il numero esatto di posti rimasti
                return int(evento.get("availability", 0))
        
        # Se la data non è presente, significa che è passata o cancellata dal calendario
        return 0
        
    except Exception as e:
        print(f"❌ Errore API Majellando per il tour {url}: {e}")
        return 0

def aggiorna_google(id_tour, nuovi_occupati):
    payload = {
        "action": "update_tour",
        "password": PASSWORD_ADMIN,
        "idTour": str(id_tour),
        "nuoviOccupati": nuovi_occupati
    }
    try:
        res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        dati = res.json()
        if dati.get("success"):
            print(f"✅ ID {id_tour} aggiornato: {nuovi_occupati} occupati.")
    except Exception as e:
        print(f"❌ Errore aggiornamento: {e}")

if __name__ == "__main__":
    print("🚀 Inizio controllo calendario da GitHub Actions...")
    
    tours_attivi = ottieni_calendario_attivo()
    
    for t in tours_attivi:
        id_tour = t['id']
        nome_tour = t['tour']
        data_majellando = formatta_data(t['giorno'], t['mese'], t['anno'])
        
        url = MAPPA_URLS.get(nome_tour)
        if not url:
            print(f"⚠️ Link non configurato per: {nome_tour}")
            continue
            
        print(f"Verifico '{nome_tour}' del {data_majellando} (Riga ID {id_tour})...")
        
        posti_totali = ottieni_posti_totali(id_tour)
        if posti_totali is not None:
            posti_disponibili = estrai_disponibilita(url, data_majellando)
            
            if posti_disponibili is not None:
                prenotati = max(0, posti_totali - posti_disponibili)
                print(f"   -> Totali: {posti_totali} | Disponibili: {posti_disponibili} | Occupati calcolati: {prenotati}")
                aggiorna_google(id_tour, prenotati)
