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

def bbox_from_radius(lat, lon, raggio_km):
    dlat = raggio_km / 111
    dlon = raggio_km / (111 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon

@app.route("/realtime_fire")
def realtime_fire():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    raggio = float(request.args.get("raggio"))

    # Scarica immagini Meteosat
    ir = Image.open(BytesIO(requests.get(URL_IR).content)).convert("L")
    vis = Image.open(BytesIO(requests.get(URL_VIS).content)).convert("L")

    ir_arr = np.array(ir)
    vis_arr = np.array(vis)

    # Soglie empiriche
    HOT = 200      # pixel molto caldi
    SMOKE_VIS = 120
    SMOKE_IR = 150

    # Analisi hotspot
    hot_mask = ir_arr > HOT

    # Analisi fumo (pattern VIS + IR)
    smoke_mask = (vis_arr < SMOKE_VIS) & (ir_arr > SMOKE_IR)

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
