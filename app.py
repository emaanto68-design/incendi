from flask import Flask, request, jsonify
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import math

app = Flask(__name__)

# Immagini Meteosat realtime (aggiornate ogni 5 minuti)
URL_IR = "https://view.eumetsat.int/static/MSG/IR108/latest.jpg"
URL_VIS = "https://view.eumetsat.int/static/MSG/VIS006/latest.jpg"

def load_image(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("L")
        return np.array(img)
    except Exception as e:
        print("Errore immagine:", e)
        return None

@app.route("/realtime_fire")
def realtime_fire():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        raggio = float(request.args.get("raggio"))
    except:
        return jsonify({"errore": "Parametri non validi"})

    ir_arr = load_image(URL_IR)
    vis_arr = load_image(URL_VIS)

    if ir_arr is None or vis_arr is None:
        return jsonify({
            "errore": "Immagine Meteosat non disponibile",
            "fonte": "Meteosat realtime"
        })

    # Soglie empiriche
    HOT = 200
    SMOKE_VIS = 120
    SMOKE_IR = 150

    try:
        hot_mask = ir_arr > HOT
        smoke_mask = (vis_arr < SMOKE_VIS) & (ir_arr > SMOKE_IR)
    except Exception as e:
        return jsonify({"errore": "Analisi immagine fallita", "dettaglio": str(e)})

    incendio = bool(hot_mask.any())
    fumo = bool(smoke_mask.any())

    # Probabilità
    prob = 0.0
    if incendio and fumo:
        prob = 0.9
    elif incendio:
        prob = 0.7
    elif fumo:
        prob = 0.4

    return jsonify({
        "incendio": incendio,
        "fumo": fumo,
        "probabilita": prob,
        "fonte": "Meteosat realtime (5 minuti)"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

