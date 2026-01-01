import requests
import gzip
import xml.etree.ElementTree as ET
import json
import io
from datetime import datetime, timedelta

def generate_json_export():
    url = "https://xmltvfr.fr/xmltv/xmltv.xml.gz"
    output_filename = "programme_tv.json"

    # 1. Configuration des dates (Maintenant -> Demain fin de journée)
    now = datetime.now()
    tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
    
    # Format YYYYMMDDHHMMSS pour le filtrage
    now_str = now.strftime("%Y%m%d%H%M%S")
    end_str = tomorrow_end.strftime("%Y%m%d%H%M%S")

    print(f"1. Téléchargement des données depuis {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        print("2. Extraction des programmes (Format strict + extensions)...")
        
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
            context = ET.iterparse(f, events=('end',))
            
            result = {
                "metadata": {
                    "generated_at": now.isoformat(),
                    "period_start": now_str,
                    "period_end": end_str
                },
                "channels": {},
                "programmes": []
            }
            
            for event, elem in context:
                
                # --- CHAINES ---
                if elem.tag == 'channel':
                    c_id = elem.get('id')
                    display = elem.find('display-name')
                    # On garde la structure simple Clé: Valeur pour les channels comme demandé précédemment
                    result["channels"][c_id] = display.text if display is not None else c_id
                    elem.clear()

                # --- PROGRAMMES ---
                elif elem.tag == 'programme':
                    # On conserve le format 14 caractères (YYYYMMDDHHMMSS) demandé dans ton exemple
                    start = elem.get('start', '')[:14]
                    stop = elem.get('stop', '')[:14]
                    
                    # Filtre temporel
                    if stop >= now_str and start <= end_str:
                        
                        # Champs existants (Base)
                        title_elem = elem.find('title')
                        desc_elem = elem.find('desc')
                        category_elem = elem.find('category')
                        
                        # Nouveaux champs (Extensions)
                        subtitle_elem = elem.find('sub-title')
                        icon_elem = elem.find('icon')
                        rating_elem = elem.find('rating')
                        
                        # Extraction du rating (valeur imbriquée)
                        rating_val = ""
                        if rating_elem is not None:
                            val_node = rating_elem.find('value')
                            if val_node is not None:
                                rating_val = val_node.text

                        prog_data = {
                            # --- Output de base conservé ---
                            "channel_id": elem.get('channel'),
                            "start": start,
                            "stop": stop,
                            "title": title_elem.text if title_elem is not None else "Titre inconnu",
                            "desc": desc_elem.text if desc_elem is not None else "",
                            "category": category_elem.text if category_elem is not None else "",
                            
                            # --- Ajouts demandés ---
                            "sub_title": subtitle_elem.text if subtitle_elem is not None else "",
                            "icon": icon_elem.get('src') if icon_elem is not None else "",
                            "rating": rating_val
                        }
                        result["programmes"].append(prog_data)
                    
                    elem.clear()

        print(f"3. Sauvegarde de {len(result['programmes'])} programmes dans {output_filename}...")
        with open(output_filename, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, indent=2, ensure_ascii=False)
            
        print("✅ Terminé.")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    generate_json_export()
