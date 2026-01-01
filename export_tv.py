import requests
import gzip
import xml.etree.ElementTree as ET
import json
import io
from datetime import datetime, timedelta

def generate_json_export():
    # URL du fichier XMLTV (Tout le bouquet)
    url = "https://xmltvfr.fr/xmltv/xmltv.xml.gz"
    output_filename = "programme_tv.json"

    # 1. Définition de la plage de temps (Maintenant -> Demain 23h59)
    now = datetime.now()
    tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
    
    # Formatage pour comparaison avec le format XMLTV (YYYYMMDDHHMMSS)
    now_str = now.strftime("%Y%m%d%H%M%S")
    end_str = tomorrow_end.strftime("%Y%m%d%H%M%S")

    print(f"1. Téléchargement des données depuis {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status() # Vérifie si le téléchargement a réussi
        
        print("2. Décompression et lecture du XML...")
        # Décompression du flux GZIP en mémoire
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
            # Parsing du XML
            context = ET.iterparse(f, events=('end',))
            
            # Structure de données finale
            result = {
                "metadata": {
                    "generated_at": now.isoformat(),
                    "period_start": now_str,
                    "period_end": end_str
                },
                "channels": {},
                "programmes": []
            }
            
            # On parcourt le XML élément par élément
            for event, elem in context:
                
                # Récupération des chaînes (Channels)
                if elem.tag == 'channel':
                    c_id = elem.get('id')
                    display = elem.find('display-name')
                    name = display.text if display is not None else c_id
                    result["channels"][c_id] = name
                    elem.clear() # Libère la mémoire

                # Récupération des programmes
                elif elem.tag == 'programme':
                    start = elem.get('start', '')[:14] # YYYYMMDDHHMMSS
                    stop = elem.get('stop', '')[:14]
                    
                    # FILTRE : Si le programme finit APRES maintenant ET commence AVANT la fin de demain
                    if stop >= now_str and start <= end_str:
                        
                        # Extraction sécurisée des données
                        title_elem = elem.find('title')
                        desc_elem = elem.find('desc')
                        category_elem = elem.find('category')
                        
                        prog_data = {
                            "channel_id": elem.get('channel'),
                            "start": start,
                            "stop": stop,
                            "title": title_elem.text if title_elem is not None else "Titre inconnu",
                            "desc": desc_elem.text if desc_elem is not None else "",
                            "category": category_elem.text if category_elem is not None else ""
                        }
                        result["programmes"].append(prog_data)
                    
                    elem.clear() # Libère la mémoire

        print(f"3. Sauvegarde dans {output_filename}...")
        # Écriture du JSON
        with open(output_filename, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, indent=2, ensure_ascii=False)
            
        print(f"✅ Succès ! {len(result['programmes'])} émissions récupérées.")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    generate_json_export()
