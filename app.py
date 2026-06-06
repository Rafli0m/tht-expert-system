import os
from pathlib import Path

import pandas as pd
from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "penyakit_tht_5_cleaned.csv"
REFERENCE_DIRS = {
    "jurnal": BASE_DIR / "jurnal",
    "buku": BASE_DIR / "buku",
}
REFERENCE_TITLE_OVERRIDES = {
    ("jurnal", "gangguan menelan.pdf"): "Dysphagia diagnosis system with integrated speech analysis from throat vibration",
    ("jurnal", "jurnal 1.pdf"): "Process abnormity identification by fuzzy logic rules and expert estimated thresholds derived certainty factor",
    ("jurnal", "jurnal 2.pdf"): "Expert systems: Definitions, advantages and issues in medical field applications",
    ("jurnal", "jurnal 3.pdf"): "Expert systems in medicine",
    ("jurnal", "jurnal 5.pdf"): "An Expert System to Diagnose Spinal Disorders",
}

TARGET_DISEASES = [
    "otitis media",
    "ear drum damage",
    "eustachian tube dysfunction (ear disorder)",
    "nose disorder",
    "obstructive sleep apnea (osa)",
]

DISEASE_INFO = {
    "otitis media": {
        "name": "Otitis Media",
        "specialist": "Telinga",
        "summary": "Infeksi atau peradangan pada telinga tengah yang sering disertai nyeri telinga, demam, dan gangguan pendengaran.",
        "focus": "Nyeri telinga, cairan telinga, demam, batuk, dan keluhan pilek.",
    },
    "ear drum damage": {
        "name": "Ear Drum Damage",
        "specialist": "Telinga",
        "summary": "Gangguan pada gendang telinga yang dapat ditandai nyeri, keluarnya cairan atau nanah, berdenging, dan penurunan pendengaran.",
        "focus": "Nanah atau darah dari telinga, telinga berdenging, dan penurunan pendengaran.",
    },
    "eustachian tube dysfunction (ear disorder)": {
        "name": "Eustachian Tube Dysfunction",
        "specialist": "Telinga",
        "summary": "Gangguan saluran eustachius yang dapat menimbulkan telinga terasa penuh, berdenging, nyeri telinga, atau pendengaran menurun.",
        "focus": "Telinga terasa penuh, berdenging, sakit tenggorokan, reaksi alergi, dan pusing.",
    },
    "nose disorder": {
        "name": "Nose Disorder",
        "specialist": "Hidung",
        "summary": "Gangguan pada hidung atau sinus yang dapat disertai hidung tersumbat, mimisan, nyeri wajah, batuk, dan sakit kepala.",
        "focus": "Mimisan, nyeri wajah, nyeri sinus, hidung tersumbat, dan sakit kepala.",
    },
    "obstructive sleep apnea (osa)": {
        "name": "Obstructive Sleep Apnea",
        "specialist": "Tidur & Pernapasan",
        "summary": "Gangguan napas saat tidur yang dapat disertai henti napas, kantuk, kelelahan, insomnia, dan mulut kering.",
        "focus": "Henti napas saat tidur, kantuk, kelelahan, sulit tidur, dan napas pendek.",
    },
}

# ---------------------------------------------------------------------------
# Symptom master — kode gejala → key internal
# ---------------------------------------------------------------------------
SYMPTOM_KEY_MAP = {
    "G01": "shortness of breath",
    "G02": "dizziness",
    "G03": "insomnia",
    "G04": "abnormal involuntary movements",
    "G05": "sore throat",
    "G06": "cough",
    "G07": "nasal congestion",
    "G08": "diminished hearing",
    "G09": "difficulty in swallowing",
    "G10": "pus draining from ear",
    "G11": "vomiting",
    "G12": "headache",
    "G13": "facial pain",
    "G14": "ear pain",
    "G15": "mouth dryness",
    "G16": "weight gain",
    "G17": "ringing in ear",
    "G18": "plugged feeling in ear",
    "G19": "fluid in ear",
    "G20": "fever",
    "G21": "difficulty breathing",
    "G22": "fatigue",
    "G23": "coryza",
    "G24": "allergic reaction",
    "G25": "sleepiness",
    "G26": "apnea",
    "G27": "abnormal breathing sounds",
    "G28": "pulling at ears",
    "G29": "redness in ear",
    "G30": "sinus congestion",
    "G31": "painful sinuses",
    "G32": "nosebleed",
    "G33": "sweating",
    "G34": "bleeding from ear",
    "G35": "swollen or red tonsils",
}

SYMPTOM_LABELS = {
    "abnormal breathing sounds": "Suara napas tidak normal",
    "abnormal involuntary movements": "Gerakan tidak sadar",
    "allergic reaction": "Reaksi alergi",
    "apnea": "Henti napas saat tidur",
    "bleeding from ear": "Keluar darah dari telinga",
    "coryza": "Pilek / hidung berair",
    "cough": "Batuk",
    "difficulty breathing": "Sulit bernapas",
    "difficulty in swallowing": "Sulit menelan",
    "diminished hearing": "Pendengaran menurun",
    "dizziness": "Pusing",
    "ear pain": "Nyeri telinga",
    "facial pain": "Nyeri wajah",
    "fatigue": "Kelelahan",
    "fever": "Demam",
    "fluid in ear": "Cairan di telinga",
    "headache": "Sakit kepala",
    "insomnia": "Sulit tidur",
    "mouth dryness": "Mulut kering",
    "nasal congestion": "Hidung tersumbat",
    "nosebleed": "Mimisan",
    "painful sinuses": "Nyeri sinus",
    "plugged feeling in ear": "Telinga terasa penuh/tersumbat",
    "pulling at ears": "Sering menarik telinga",
    "pus draining from ear": "Nanah keluar dari telinga",
    "redness in ear": "Kemerahan pada telinga",
    "ringing in ear": "Telinga berdenging",
    "shortness of breath": "Napas pendek",
    "sinus congestion": "Sinus tersumbat",
    "sleepiness": "Mudah mengantuk",
    "sore throat": "Sakit tenggorokan",
    "sweating": "Berkeringat",
    "swollen or red tonsils": "Amandel bengkak/merah",
    "vomiting": "Muntah",
    "weight gain": "Berat badan naik",
}

SYMPTOM_GROUPS = {
    "Telinga": [
        "ear pain",
        "diminished hearing",
        "plugged feeling in ear",
        "fluid in ear",
        "ringing in ear",
        "pulling at ears",
        "pus draining from ear",
        "redness in ear",
        "bleeding from ear",
        "dizziness",
    ],
    "Hidung & Tenggorokan": [
        "nasal congestion",
        "coryza",
        "sore throat",
        "cough",
        "fever",
        "vomiting",
        "allergic reaction",
        "swollen or red tonsils",
        "nosebleed",
        "facial pain",
        "painful sinuses",
        "headache",
        "sinus congestion",
    ],
    "Tidur & Pernapasan": [
        "difficulty breathing",
        "abnormal breathing sounds",
        "mouth dryness",
        "fatigue",
        "sweating",
        "abnormal involuntary movements",
        "apnea",
        "weight gain",
        "difficulty in swallowing",
        "insomnia",
        "sleepiness",
        "shortness of breath",
    ],
}

NAV_ITEMS = [
    {"endpoint": "index", "label": "Beranda"},
    {"endpoint": "about", "label": "Tentang"},
    {"endpoint": "diseases", "label": "Penyakit"},
    {"endpoint": "method", "label": "Metode CF"},
    {"endpoint": "dataset", "label": "Dataset"},
    {"endpoint": "simulation", "label": "Simulasi"},
    {"endpoint": "references", "label": "Jurnal"},
]

# ---------------------------------------------------------------------------
# Rules IF-THEN baru (gejala dalam key internal)
# Setiap rule adalah tuple (disease_key, [symptom_keys])
# ---------------------------------------------------------------------------
def _g(codes: list[str]) -> list[str]:
    """Konversi list kode G ke key internal."""
    return [SYMPTOM_KEY_MAP[c] for c in codes]

RULES_IFTHEN: list[dict] = [
    {"id": "R01", "disease": "otitis media", "symptoms": _g(["G11","G14","G20"]), "cf": 0.70},
    {"id": "R02", "disease": "otitis media", "symptoms": _g(["G08","G18","G19"]), "cf": 0.62},
    {"id": "R03", "disease": "otitis media", "symptoms": _g(["G23","G28","G06"]), "cf": 0.55},
    {"id": "R04", "disease": "otitis media", "symptoms": _g(["G05","G07","G14"]), "cf": 0.60},
    {"id": "R05", "disease": "otitis media", "symptoms": _g(["G11","G23","G28","G14"]), "cf": 0.72},
    {"id": "R06", "disease": "otitis media", "symptoms": _g(["G20","G08","G19"]), "cf": 0.60},
    
    {"id": "R07", "disease": "nose disorder", "symptoms": _g(["G30","G31","G32"]), "cf": 0.85},
    {"id": "R08", "disease": "nose disorder", "symptoms": _g(["G12","G13","G07"]), "cf": 0.75},
    {"id": "R09", "disease": "nose disorder", "symptoms": _g(["G21","G23","G20"]), "cf": 0.55},
    {"id": "R10", "disease": "nose disorder", "symptoms": _g(["G05","G06","G14","G32"]), "cf": 0.68},
    {"id": "R11", "disease": "nose disorder", "symptoms": _g(["G13","G31","G32"]), "cf": 0.88},
    {"id": "R12", "disease": "nose disorder", "symptoms": _g(["G07","G30","G12"]), "cf": 0.75},
    
    {"id": "R13", "disease": "obstructive sleep apnea (osa)", "symptoms": _g(["G26","G25","G27"]), "cf": 0.85},
    {"id": "R14", "disease": "obstructive sleep apnea (osa)", "symptoms": _g(["G15","G03","G22"]), "cf": 0.80},
    {"id": "R15", "disease": "obstructive sleep apnea (osa)", "symptoms": _g(["G16","G04","G09"]), "cf": 0.78},
    {"id": "R16", "disease": "obstructive sleep apnea (osa)", "symptoms": _g(["G01","G21","G33"]), "cf": 0.75},
    {"id": "R17", "disease": "obstructive sleep apnea (osa)", "symptoms": _g(["G26","G03","G22","G25"]), "cf": 0.85},
    {"id": "R18", "disease": "obstructive sleep apnea (osa)", "symptoms": _g(["G15","G27","G16"]), "cf": 0.75},
    
    {"id": "R19", "disease": "ear drum damage", "symptoms": _g(["G10","G34","G29"]), "cf": 0.88},
    {"id": "R20", "disease": "ear drum damage", "symptoms": _g(["G08","G18","G14"]), "cf": 0.55},
    {"id": "R21", "disease": "ear drum damage", "symptoms": _g(["G19","G28","G06"]), "cf": 0.55},
    {"id": "R22", "disease": "ear drum damage", "symptoms": _g(["G17","G14","G29"]), "cf": 0.58},
    {"id": "R23", "disease": "ear drum damage", "symptoms": _g(["G10","G08","G18","G29"]), "cf": 0.85},
    
    {"id": "R24", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G02","G18","G14"]), "cf": 0.65},
    {"id": "R25", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G24","G35","G27"]), "cf": 0.72},
    {"id": "R26", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G08","G29","G05"]), "cf": 0.62},
    {"id": "R27", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G17","G07","G14"]), "cf": 0.58},
    {"id": "R28", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G02","G24","G35","G18"]), "cf": 0.82},
    {"id": "R29", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G05","G27","G08"]), "cf": 0.60},
    {"id": "R30", "disease": "eustachian tube dysfunction (ear disorder)", "symptoms": _g(["G02","G18","G24","G08","G14"]), "cf": 0.82},
]

# ---------------------------------------------------------------------------
# Hitung CF pakar per gejala per penyakit dari dataset (untuk bobot)
# ---------------------------------------------------------------------------
def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    try:
        dataframe = pd.read_csv(path, sep=";")
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Dataset file is empty: {path}") from exc

    if "diseases" not in dataframe.columns:
        raise ValueError(
            "Dataset must include a 'diseases' column. "
            "Check that the THT dataset is semicolon-separated."
        )

    symptom_columns = [c for c in dataframe.columns if c != "diseases"]
    if not symptom_columns:
        raise ValueError("Dataset must include at least one symptom column.")

    dataframe["diseases"] = dataframe["diseases"].astype(str).str.strip()
    try:
        dataframe[symptom_columns] = dataframe[symptom_columns].apply(pd.to_numeric)
    except (TypeError, ValueError) as exc:
        raise ValueError("All symptom columns in the dataset must be numeric.") from exc

    return dataframe


DATAFRAME = load_dataset(DATASET_PATH)
SYMPTOM_COLUMNS = [c for c in DATAFRAME.columns if c != "diseases"]


# ---------------------------------------------------------------------------
DISEASE_COUNTS: dict[str, int] = {
    disease: int((DATAFRAME["diseases"] == disease).sum())
    for disease in TARGET_DISEASES
}


# ---------------------------------------------------------------------------
# Kumpulkan semua gejala yang muncul dalam rules (untuk form)
# ---------------------------------------------------------------------------
def _all_rule_symptoms() -> set[str]:
    symptoms: set[str] = set()
    for rule in RULES_IFTHEN:
        symptoms.update(rule["symptoms"])
    return symptoms

ALL_RULE_SYMPTOMS: set[str] = _all_rule_symptoms()


# ---------------------------------------------------------------------------
# Kumpulkan gejala-gejala yang relevan per penyakit (dari rules)
# ---------------------------------------------------------------------------
def _disease_symptom_set(disease: str) -> set[str]:
    """Ambil semua gejala yang muncul di rules penyakit tertentu."""
    syms: set[str] = set()
    for rule in RULES_IFTHEN:
        if rule["disease"] == disease:
            syms.update(rule["symptoms"])
    return syms


# ---------------------------------------------------------------------------
# Helpers umum
# ---------------------------------------------------------------------------
def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _combine_two_cf(old_cf: float, new_cf: float) -> tuple[float, str]:
    """Gabungkan dua CF menggunakan rumus kombinasi standar."""
    if old_cf >= 0 and new_cf >= 0:
        combined = old_cf + new_cf * (1 - old_cf)
        formula = f"{old_cf:.4f} + {new_cf:.4f} × (1 - {old_cf:.4f}) = {combined:.4f}"
    elif old_cf < 0 and new_cf < 0:
        combined = old_cf + new_cf * (1 + old_cf)
        formula = f"{old_cf:.4f} + {new_cf:.4f} × (1 + {old_cf:.4f}) = {combined:.4f}"
    else:
        denominator = 1 - min(abs(old_cf), abs(new_cf))
        combined = (old_cf + new_cf) / denominator if denominator else 0.0
        formula = (
            f"({old_cf:.4f} + {new_cf:.4f}) / "
            f"(1 - min(|{old_cf:.4f}|, |{new_cf:.4f}|)) = {combined:.4f}"
        )
    combined = max(-1.0, min(1.0, combined))
    return combined, formula


def build_cf_steps(cf_items: list[dict]) -> list[dict]:
    """Bangun langkah-langkah kombinasi CF dari daftar rule yang terpenuhi."""
    steps = []
    combined = 0.0
    # Urutkan dari CF tertinggi
    ordered = sorted(cf_items, key=lambda x: x["cf"], reverse=True)
    for idx, item in enumerate(ordered, start=1):
        old_cf = combined
        cf = float(item["cf"])
        combined, formula = _combine_two_cf(old_cf, cf)
        steps.append({
            "index": idx,
            "id": item.get("id", ""),
            "label": item["label"],
            "cf": cf,
            "old_cf": old_cf,
            "new_cf": combined,
            "cf_percent": format_percent(cf),
            "cf_value": item.get("cf_value", f"{cf:.4f}"),
            "old_percent": format_percent(old_cf),
            "new_percent": format_percent(combined),
            "formula": formula,
            "symptoms_str": item.get("symptoms_str", ""),
            "symptoms": item.get("symptoms", [])
        })
    return steps


# ---------------------------------------------------------------------------
# Diagnosis utama — berbasis Rule (R01-R30)
# ---------------------------------------------------------------------------
def diagnose(selected_symptoms: list[str]) -> list[dict]:
    selected_set = set(selected_symptoms)

    results = []
    for disease in TARGET_DISEASES:
        matched_rules = []
        for rule in RULES_IFTHEN:
            if rule["disease"] == disease:
                rule_symptoms_set = set(rule["symptoms"])
                # Logika AND strict: rule hanya aktif jika semua gejalanya dipilih user
                if rule_symptoms_set.issubset(selected_set):
                    symptom_labels = [SYMPTOM_LABELS.get(s, s.title()) for s in rule["symptoms"]]
                    matched_rules.append({
                        "id": rule["id"],
                        "disease": disease,
                        "cf": rule["cf"],
                        "symptoms": rule["symptoms"],
                        "symptoms_str": " AND ".join(symptom_labels),
                        "label": f"{rule['id']}",
                        "cf_value": f"{rule['cf']:.4f}",
                    })

        # Urutkan rule dari CF tertinggi
        matched_rules = sorted(matched_rules, key=lambda x: x["cf"], reverse=True)
        steps = build_cf_steps(matched_rules)
        final_cf = steps[-1]["new_cf"] if steps else 0.0

        results.append({
            "key": disease,
            "name": DISEASE_INFO[disease]["name"],
            "specialist": DISEASE_INFO[disease]["specialist"],
            "summary": DISEASE_INFO[disease]["summary"],
            "cf": final_cf,
            "percent": format_percent(final_cf),
            "bar_width": max(final_cf * 100, 3 if final_cf > 0 else 0),
            "matched": matched_rules,
            "matched_count": len(matched_rules),
            "sample_count": DISEASE_COUNTS[disease],
            "steps": steps,
        })

    return sorted(results, key=lambda x: x["cf"], reverse=True)


# ---------------------------------------------------------------------------
# Form helpers
# ---------------------------------------------------------------------------
def get_symptom_groups() -> list[dict]:
    groups = []
    for group_name, symptoms in SYMPTOM_GROUPS.items():
        items = [
            {"key": s, "label": SYMPTOM_LABELS.get(s, s.title())}
            for s in symptoms
            if s in ALL_RULE_SYMPTOMS
        ]
        if items:
            groups.append({"name": group_name, "symptoms": items})
    return groups


def get_total_displayed_symptoms() -> int:
    return sum(len(g["symptoms"]) for g in get_symptom_groups())


def selected_symptom_labels(selected: list[str]) -> list[str]:
    return [SYMPTOM_LABELS.get(s, s.title()) for s in selected]


# ---------------------------------------------------------------------------
# Disease cards (untuk halaman Diseases & Simulasi)
# ---------------------------------------------------------------------------
def top_rules_for_disease(disease: str, limit: int = 8) -> list[dict]:
    """Mengambil rules yang relevan untuk penyakit ini."""
    ranked = []
    for r in RULES_IFTHEN:
        if r["disease"] == disease:
            symptom_labels = [SYMPTOM_LABELS.get(s, s.title()) for s in r["symptoms"]]
            ranked.append({
                "id": r["id"],
                "symptom_text": " AND ".join(symptom_labels),
                "cf": r["cf"],
                "percent": format_percent(r["cf"])
            })

    ranked.sort(key=lambda x: x["cf"], reverse=True)
    return ranked[:limit]


def get_disease_cards(limit: int = 8) -> list[dict]:
    return [
        {
            "id": disease,
            "key": disease,
            "name": DISEASE_INFO[disease]["name"],
            "specialist": DISEASE_INFO[disease]["specialist"],
            "summary": DISEASE_INFO[disease]["summary"],
            "focus": DISEASE_INFO[disease]["focus"],
            "sample_count": DISEASE_COUNTS[disease],
            "top_rules": top_rules_for_disease(disease, limit=limit),
        }
        for disease in TARGET_DISEASES
    ]


# ---------------------------------------------------------------------------
# Dataset stats (hanya untuk halaman About / Dataset)
# ---------------------------------------------------------------------------
def get_dataset_stats() -> dict:
    distribution = [
        {
            "key": d,
            "name": DISEASE_INFO[d]["name"],
            "count": DISEASE_COUNTS[d],
            "percent": format_percent(DISEASE_COUNTS[d] / len(DATAFRAME)),
        }
        for d in TARGET_DISEASES
    ]
    return {
        "rows": len(DATAFRAME),
        "columns": DATAFRAME.shape[1],
        "symptoms": len(SYMPTOM_COLUMNS),
        "diseases": DATAFRAME["diseases"].nunique(),
        "displayed_symptoms": get_total_displayed_symptoms(),
        "rule_count": len(RULES_IFTHEN),
        "distribution": distribution,
        "dataset_file": DATASET_PATH.name,
    }


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
def get_references() -> dict:
    refs: dict[str, list[dict]] = {"jurnal": [], "buku": []}
    for kind, directory in REFERENCE_DIRS.items():
        if not directory.exists():
            continue
        for f in sorted(directory.glob("*.pdf")):
            title = REFERENCE_TITLE_OVERRIDES.get((kind, f.name.lower()), f.stem)
            refs[kind].append({
                "filename": f.name,
                "title": title,
                "url": url_for("reference_file", kind=kind, filename=f.name),
            })
    return refs


# ---------------------------------------------------------------------------
# Simulasi
# ---------------------------------------------------------------------------
def build_simulation(disease: str, selected_symptoms: list[str]) -> dict:
    if disease not in TARGET_DISEASES:
        disease = TARGET_DISEASES[0]

    # Ambil semua gejala untuk form simulasi
    available_symptoms = list(_disease_symptom_set(disease))
    available = [
        {
            "key": s,
            "label": SYMPTOM_LABELS.get(s, s.title())
        }
        for s in available_symptoms
    ]
    
    selected_set = set(selected_symptoms) & set(available_symptoms)

    matched_rules = []
    for rule in RULES_IFTHEN:
        if rule["disease"] == disease:
            rule_symptoms_set = set(rule["symptoms"])
            if rule_symptoms_set.issubset(selected_set):
                symptom_labels = [SYMPTOM_LABELS.get(s, s.title()) for s in rule["symptoms"]]
                matched_rules.append({
                    "id": rule["id"],
                    "disease": disease,
                    "cf": rule["cf"],
                    "symptoms": rule["symptoms"],
                    "symptoms_str": " AND ".join(symptom_labels),
                    "label": f"{rule['id']}",
                    "cf_value": f"{rule['cf']:.4f}",
                })

    # Urutkan dari CF tertinggi
    matched_rules = sorted(matched_rules, key=lambda x: x["cf"], reverse=True)
    steps = build_cf_steps(matched_rules)
    final_cf = steps[-1]["new_cf"] if steps else 0.0

    return {
        "disease": disease,
        "disease_name": DISEASE_INFO[disease]["name"],
        "symptoms": available,
        "selected": list(selected_set),
        "steps": steps,
        "final_cf": final_cf,
        "final_percent": format_percent(final_cf),
    }


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)


@app.context_processor
def inject_global():
    return {"nav_items": NAV_ITEMS, "app_name": "THT ExpertCare"}


@app.get("/")
def index():
    return render_template(
        "index.html",
        active_page="index",
        disease_info=DISEASE_INFO,
        total_symptoms=get_total_displayed_symptoms(),
    )


@app.get("/diagnose")
def diagnose_page():
    return render_template(
        "diagnose.html",
        active_page="diagnose",
        symptom_groups=get_symptom_groups(),
        disease_info=DISEASE_INFO,
        total_symptoms=get_total_displayed_symptoms(),
        error=None,
    )


@app.post("/diagnose")
def diagnose_route():
    selected = request.form.getlist("symptoms")
    if not selected:
        return render_template(
            "diagnose.html",
            active_page="diagnose",
            symptom_groups=get_symptom_groups(),
            disease_info=DISEASE_INFO,
            total_symptoms=get_total_displayed_symptoms(),
            error="Pilih minimal satu gejala agar sistem dapat menghitung nilai Certainty Factor.",
        )
    results = diagnose(selected)
    return render_template(
        "result.html",
        active_page="diagnose",
        results=results,
        top_result=results[0],
        selected_symptoms=selected_symptom_labels(selected),
        selected_symptom_keys=selected,
    )


@app.post("/calculation")
def calculation():
    selected = request.form.getlist("symptoms")
    if not selected:
        return redirect(url_for("diagnose_page"))
    results = diagnose(selected)
    return render_template(
        "calculation.html",
        active_page="diagnose",
        results=results,
        selected_symptoms=selected_symptom_labels(selected),
        selected_symptom_keys=selected,
    )


@app.get("/about")
def about():
    return render_template("about.html", active_page="about", stats=get_dataset_stats())


@app.get("/diseases")
def diseases():
    return render_template("diseases.html", active_page="diseases", diseases=get_disease_cards(limit=10))


@app.get("/disease/<id>")
def disease_detail(id):
    card = next((d for d in get_disease_cards(limit=10) if d["id"] == id), None)
    if not card:
        abort(404)
    return render_template("disease_detail.html", active_page="diseases", disease=card)


@app.get("/method")
def method():
    return render_template("method.html", active_page="method")


@app.get("/dataset")
def dataset():
    return render_template("dataset.html", active_page="dataset", stats=get_dataset_stats())


@app.route("/simulation", methods=["GET", "POST"])
def simulation():
    selected_disease = (
        request.form.get("disease") or request.args.get("disease") or TARGET_DISEASES[0]
    )
    if selected_disease not in TARGET_DISEASES:
        selected_disease = TARGET_DISEASES[0]

    selected_symptoms = request.form.getlist("symptoms") if request.method == "POST" else []
    error = None
    if request.method == "POST" and not selected_symptoms:
        error = "Pilih minimal satu gejala untuk melihat langkah perhitungan CF."

    sim = build_simulation(selected_disease, selected_symptoms)

    return render_template(
        "simulation.html",
        active_page="simulation",
        diseases=get_disease_cards(limit=3),
        selected_disease=selected_disease,
        simulation=sim,
        error=error,
    )


@app.get("/references")
def references():
    return render_template("references.html", active_page="references", references=get_references())


@app.get("/references/<kind>/<path:filename>")
def reference_file(kind: str, filename: str):
    directory = REFERENCE_DIRS.get(kind)
    if directory is None or not directory.exists():
        abort(404)
    return send_from_directory(directory, filename, as_attachment=False)


@app.get("/reset")
def reset():
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host="127.0.0.1", port=port)
