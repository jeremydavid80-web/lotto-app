from flask import Flask, render_template, request, redirect
import json

app = Flask(__name__)

# -----------------------------
# CONFIGURATION
# -----------------------------

FILENAME = "lotto_results.json"
MISES_FILE = "mises.json"

PLAYERS = [
    {"name": "Jerem", "numbers": [8, 12, 14, 17, 39, 43]},
    {"name": "Nico", "numbers": [4, 14, 17, 22, 27, 29]},
    {"name": "Christophe", "numbers": [9, 16, 17, 26, 37, 45]},
    {"name": "Rich", "numbers": [10, 12, 15, 20, 43, 45]},
]

# -----------------------------
# FONCTIONS JSON
# -----------------------------

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

data = load_json(FILENAME, [])
mises = load_json(MISES_FILE, {p["name"]: 0 for p in PLAYERS})

# -----------------------------
# SYSTÈME DE RANGS 1 À 9
# -----------------------------

def get_rank(matches, bonus_match):
    if matches == 6 and bonus_match:
        return 1
    if matches == 6:
        return 2
    if matches == 5 and bonus_match:
        return 3
    if matches == 5:
        return 4
    if matches == 4 and bonus_match:
        return 5
    if matches == 4:
        return 6
    if matches == 3 and bonus_match:
        return 7
    if matches == 3:
        return 8
    if matches == 2 and bonus_match:
        return 9
    return None

# -----------------------------
# ROUTES PRINCIPALES
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html", players=PLAYERS, active="home")

@app.route('/')
def index():
    import json

    # Charger les mises (dictionnaire)
    with open('mises.json', 'r') as f:
        mises_data = json.load(f)

    # Total des mises
    total_mises = sum(mises_data.values())

    # Charger les résultats du loto (liste de tirages)
    with open('lotto_results.json', 'r') as f:
        results_data = json.load(f)

    # Calcul des gains cumulés par joueur
    gains_par_joueur = {}

    for tirage in results_data:
        for entry in tirage["results"]:
            nom = entry["name"]
            gain = entry["gain"]

            if nom not in gains_par_joueur:
                gains_par_joueur[nom] = 0

            gains_par_joueur[nom] += gain

    # Total des gains
    total_gains = sum(gains_par_joueur.values())

    # Meilleur joueur
    best_player = max(gains_par_joueur, key=gains_par_joueur.get)

    return render_template(
        "index.html",
        total_gains=total_gains,
        total_mises=total_mises,
        best_player=best_player
    )




@app.route("/tirages")
def tirages():
    return render_template("tirages.html", tirages=data, active="tirages")

@app.route("/mises")
def page_mises():
    return render_template("mises.html", mises=mises, active="mises")

@app.route("/recap")
def recap():
    total_mises = sum(mises.values())
    total_gains = sum(r["gain"] for entry in data for r in entry["results"])
    solde = total_gains - total_mises

    return render_template(
        "recap.html",
        total_mises=total_mises,
        total_gains=total_gains,
        solde=solde,
        active="recap"
    )

# -----------------------------
# PAGE GRILLES (gains par joueur)
# -----------------------------

@app.route("/grilles")
def grilles():
    grilles_data = {}

    for p in PLAYERS:
        name = p["name"]
        grilles_data[name] = {
            "numbers": p["numbers"],
            "tirages": [],
            "total_gain": 0
        }

    for entry in data:
        date = entry["date"]
        for r in entry["results"]:
            name = r["name"]
            rank = r["rank"]
            gain = r["gain"]

            grilles_data[name]["tirages"].append({
                "date": date,
                "rank": rank,
                "gain": gain
            })
            grilles_data[name]["total_gain"] += gain

    return render_template("grilles.html", grilles=grilles_data, active="grilles")

# -----------------------------
# AJOUT MANUEL D’UN TIRAGE
# -----------------------------

@app.route("/add_tirage", methods=["GET", "POST"])
def add_tirage():
    if request.method == "POST":
        date = request.form["date"]
        nums = request.form.getlist("nums")
        bonus = int(request.form["bonus"])
        played_bonus = int(request.form["played_bonus"])

        nums = [int(n) for n in nums]

        results = []
        for p in PLAYERS:
            matches = len(set(p["numbers"]) & set(nums))
            bonus_match = (bonus == played_bonus)
            rank = get_rank(matches, bonus_match)
            results.append({"name": p["name"], "rank": rank, "gain": 0})

        data.append({
            "date": date,
            "results": results
        })

        save_json(FILENAME, data)
        return redirect("/tirages")

    return render_template("add_tirage.html", active="add")

# -----------------------------
# AJOUT D’UNE MISE
# -----------------------------

@app.route("/add_mise", methods=["POST"])
def add_mise():
    name = request.form["name"]
    amount = float(request.form["amount"])
    mises[name] += amount
    save_json(MISES_FILE, mises)
    return redirect("/mises")

# -----------------------------
# SAISIE DES GAINS
# -----------------------------

@app.route("/gains/<path:date>", methods=["GET", "POST"])
def gains(date):
    entry = next((e for e in data if e["date"] == date), None)
    if not entry:
        return "Tirage introuvable"

    if request.method == "POST":
        for r in entry["results"]:
            r["gain"] = float(request.form.get(r["name"], 0))
        save_json(FILENAME, data)
        return redirect("/tirages")

    return render_template("gains.html", tirage=entry, active="tirages")

# -----------------------------
# LANCEMENT SERVEUR
# -----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
