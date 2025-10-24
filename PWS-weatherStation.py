import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# Remplace par ta clé API (ne la partage pas !)
api_key = "e1f10a1e78da46f5b10a1e78da96f525"
# Met ici tes 3 stationId
station_ids = ["ICUSSA12", "ICUSSA10", "ICUSSA13"]


# date = "20251024"
date = sys.argv[1] if len(sys.argv) > 1 else datetime.utcnow().strftime("%Y%m%d")


plt.figure(figsize=(12, 6))

for station_id in station_ids:
    url = f"https://api.weather.com/v2/pws/history/all?stationId={station_id}&format=json&units=m&date={date}&numericPrecision=decimal&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()

    # sauvegarde optionnelle pour inspection
    with open(f'pluviometrie_{station_id}.json', 'w') as f:
        json.dump(data, f, indent=2)

    observations = data.get('observations', [])
    times = []
    pluies = []

    for obs in observations:
        t = obs.get('obsTimeUtc')
        if not t:
            continue
        # Convertit ISO '...Z' en objet datetime
        try:
            if t.endswith('Z'):
                dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(t)
        except Exception:
            # fallback si format différent
            try:
                dt = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue
        times.append(dt)
        pluies.append(obs.get('metric', {}).get('precipTotal', 0))

    # Trier par temps et tracer
    if times:
        paired = sorted(zip(times, pluies))
        times_sorted, pluies_sorted = zip(*paired)
        plt.plot(times_sorted, pluies_sorted, marker='o', label=station_id, alpha=0.8)

plt.title(f"Pluviométrie le {datetime.utcnow().strftime("%Y-%m-%d")}")
plt.xlabel("Heure (UTC)")
plt.ylabel("Précipitations (mm)")
plt.xticks(rotation=45)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
# ...existing code...
