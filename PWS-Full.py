# ...existing code...
import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# UI imports
import tkinter as tk
from tkinter import ttk, messagebox

# try optional DateEntry from tkcalendar
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except Exception:
    DateEntry = None
    TKCALENDAR_AVAILABLE = False

# Remplace par ta clé API (ne la partage pas !)
api_key = "e1f10a1e78da46f5b10a1e78da96f525"
# Met ici tes 3 stationId
station_ids = ["ICUSSA12", "ICUSSA10", "ICUSSA13"]

# date par défaut (aujourd'hui UTC) ou argument en ligne de commande
default_date = sys.argv[1] if len(sys.argv) > 1 else datetime.utcnow().strftime("%Y%m%d")


def iso_from_widget_value(raw):
    """Convertit la valeur du widget en YYYYMMDD; gère DateEntry (get_date) ou différentes saisies."""
    if TKCALENDAR_AVAILABLE and hasattr(raw, 'get_date'):
        d = raw.get_date()  # retourne datetime.date
        return d.strftime("%Y%m%d")
    s = raw.get()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d.strftime("%Y%m%d")
        except Exception:
            pass
    raise ValueError("Format de date non reconnu. Utiliser YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY ou YYYYMMDD.")


def fetch_and_plot(date_str, text_widget):
    """Récupère les données des 3 stations pour date_str (YYYYMMDD), trace et affiche totaux."""
    try:
        # clear text widget
        text_widget.configure(state='normal')
        text_widget.delete("1.0", tk.END)
    except Exception:
        pass

    totals = {}
    plt.close("all")
    plt.figure(figsize=(12, 6))

    for station_id in station_ids:
        url = f"https://api.weather.com/v2/pws/history/all?stationId={station_id}&format=json&units=m&date={date_str}&numericPrecision=decimal&apiKey={api_key}"
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            msg = f"{station_id}: erreur requête - {e}\n"
            text_widget.insert(tk.END, msg)
            continue

        # sauvegarde optionnelle pour inspection
        try:
            with open(f'pluviometrie_{station_id}_{date_str}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        observations = data.get('observations', [])
        times = []
        pluies = []

        for obs in observations:
            t = obs.get('obsTimeUtc')
            if not t:
                continue
            try:
                if t.endswith('Z'):
                    dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(t)
            except Exception:
                try:
                    dt = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    continue
            times.append(dt)
            pluies.append(obs.get('metric', {}).get('precipTotal', 0))

        if times:
            paired = sorted(zip(times, pluies))
            times_sorted, pluies_sorted = zip(*paired)
            plt.plot(times_sorted, pluies_sorted, marker='o', label=station_id, alpha=0.8)
            # Considérons la valeur maximale observée comme total journalier
            total_mm = max(pluies_sorted)
            totals[station_id] = total_mm
            text_widget.insert(tk.END, f"{station_id} — total (mm): {total_mm:.2f}\n")
        else:
            text_widget.insert(tk.END, f"{station_id} — aucune observation pour cette date.\n")

    plt.title(f"Pluviométrie le {datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')}")
    plt.xlabel("Heure (UTC)")
    plt.ylabel("Précipitations (mm)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    try:
        plt.show(block=False)
    except Exception:
        plt.show()

    text_widget.configure(state='disabled')
    return totals


# --- Tkinter UI ---
root = tk.Tk()
root.title("PWS Pluviométrie - Sélection de la date")

frm = ttk.Frame(root, padding=10)
frm.grid(row=0, column=0, sticky="nsew")

ttk.Label(frm, text="Date (sélectionne ou saisis) :").grid(row=0, column=0, sticky="w", pady=(0, 6))

if TKCALENDAR_AVAILABLE:
    date_widget = DateEntry(frm, width=12)
    # set default date in widget
    try:
        default_dt = datetime.strptime(default_date, "%Y%m%d")
        date_widget.set_date(default_dt.date())
    except Exception:
        pass
    date_widget.grid(row=0, column=1, sticky="w")
else:
    date_widget = ttk.Entry(frm, width=16)
    date_widget.insert(0, datetime.strptime(default_date, "%Y%m%d").strftime("%Y-%m-%d"))
    date_widget.grid(row=0, column=1, sticky="w")
    ttk.Label(frm, text="(format: YYYY-MM-DD or DD/MM/YYYY)").grid(row=1, column=0, columnspan=2, sticky="w")

text = tk.Text(frm, width=50, height=10, state='disabled')
text.grid(row=2, column=0, columnspan=3, pady=(10, 0))

def on_get():
    try:
        date_str = iso_from_widget_value(date_widget)
    except Exception as e:
        messagebox.showerror("Erreur date", str(e))
        return
    fetch_and_plot(date_str, text)

btn_get = ttk.Button(frm, text="Récupérer et tracer", command=on_get)
btn_get.grid(row=0, column=2, padx=(10,0))

btn_quit = ttk.Button(frm, text="Quitter", command=root.destroy)
btn_quit.grid(row=3, column=2, sticky="e", pady=(10,0))

# run once at startup with default date
try:
    fetch_and_plot(default_date, text)
except Exception:
    pass

root.mainloop()
# ...existing code...