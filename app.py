import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import joblib
from datetime import date

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="FilBleu Predictor — Prédiction de retard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- PATHS ----------------
PROJECT_ROOT = Path(__file__).resolve().parent  # app.py est à la racine
DEMO_DIR = PROJECT_ROOT / "demo"

MODEL_PATH = DEMO_DIR / "model.joblib"
DEMO_DATA = DEMO_DIR / "data.csv"

# (optionnel) si tu copies ces 2 fichiers aussi dans demo/
COVER_ROUTE = DEMO_DIR / "coverage_by_route.csv"
COVER_STOPS = DEMO_DIR / "coverage_top_stops.csv"


# ---------------- STYLE (PALETTE UNDER THE SEA) ----------------
APP_CSS = """
<style>
:root{
  --c1:#BAD2E0;
  --c2:#82AFF2;
  --c3:#3078CD;
  --c4:#25456B;
  --c5:#113356;
}
.stApp{
  background:
    radial-gradient(1100px 600px at 70% 20%, rgba(130,175,242,0.22), transparent 60%),
    radial-gradient(900px 550px at 20% 75%, rgba(48,120,205,0.18), transparent 60%),
    linear-gradient(180deg, var(--c5) 0%, #0b1424 100%);
  color: rgba(255,255,255,0.92);
}
.block-container{
  max-width: 1180px;
  margin: 0 auto;
  padding-top: 1.8rem;
  padding-bottom: 2rem;
}
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(17,51,86,0.98) 0%, rgba(37,69,107,0.98) 100%);
  border-right: 1px solid rgba(186,210,224,0.12);
}
section[data-testid="stSidebar"] *{
  color: rgba(255,255,255,0.92) !important;
}
[data-testid="stToolbar"]{visibility:hidden !important; height:0px !important;}
header{visibility:hidden !important;}
#MainMenu{visibility:hidden !important;}
footer{visibility:hidden !important;}

.hero-wrap{ text-align:center; margin-top: 0.4rem; margin-bottom: 1.2rem; }
.hero-title{ font-size: 52px; font-weight: 900; color: var(--c2); letter-spacing: -0.8px; margin: 0; }
.hero-sub{ font-size: 16px; color: rgba(186,210,224,0.90); margin-top: 10px; margin-bottom: 8px; }
.hero-tagline{ font-size: 15px; color: rgba(186,210,224,0.85); margin: 0; }

.chips{ text-align:center; margin-top: 14px; }
.chip{
  display:inline-block; padding:6px 10px; border-radius:999px;
  border:1px solid rgba(186,210,224,0.18);
  background: rgba(186,210,224,0.06);
  color: rgba(186,210,224,0.95); font-size: 12px; margin: 6px 6px 0 0;
}

.card{
  background: rgba(186,210,224,0.06);
  border: 1px solid rgba(130,175,242,0.28);
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  border-radius: 18px;
  padding: 26px 26px 20px 26px;
  min-height: 240px;
}
.card h3{ margin:0 0 12px 0; font-size: 24px; font-weight: 900; color: rgba(255,255,255,0.95); }
.card p{ margin:0 0 18px 0; color: rgba(186,210,224,0.92); line-height:1.55; font-size: 14.5px; }

div.stButton > button{
  width: 100%;
  background: var(--c3);
  color: white;
  border: 1px solid rgba(186,210,224,0.15);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-weight: 900;
}
div.stButton > button:hover{
  background: #2a6bb5;
  color: white;
}
.nav-btn button{
  width:100%;
  background: rgba(48,120,205,0.95) !important;
  border-radius: 12px !important;
  padding: 0.75rem 1rem !important;
  font-weight: 900 !important;
  border: 1px solid rgba(186,210,224,0.16) !important;
}
.nav-btn button:hover{
  background: rgba(130,175,242,0.95) !important;
  color: #0b1424 !important;
}

/* gros affichage résultat */
.big-result{
  font-size: 34px;
  font-weight: 950;
  margin-top: 10px;
  margin-bottom: 6px;
}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# ---------------- HELPERS ----------------

def format_delay_minutes(delay: float) -> str:
    seconds = int(round(abs(delay) * 60))

    # +/- 30 sec => à l'heure
    if -0.5 <= delay <= 0.5:
        return "🟢 À l’heure"

    if delay < -0.5:
        if seconds < 60:
            return f"🟢 En avance de {seconds} secondes"
        return f"🟢 En avance de {seconds//60} min {seconds%60} s"

    return f"⏰ En retard de {delay:.2f} minutes"

def format_delay_stat(delay_min: float) -> str:
    """
    Format lisible pour des stats (moyenne/médiane) :
    - proche de 0 => "0 s"
    - < 1 minute => "XX s"
    - sinon => "X min YY s"
    Garde aussi le signe (+ retard / - avance).
    """
    if pd.isna(delay_min):
        return "—"

    sec = int(round(delay_min * 60))  # garde le signe
    if abs(sec) <= 1:
        return "0 s"

    sign = "-" if sec < 0 else ""
    sec_abs = abs(sec)

    if sec_abs < 60:
        return f"{sign}{sec_abs} s"

    return f"{sign}{sec_abs//60} min {sec_abs%60} s"


def risk_label(pred_delay_min: float) -> str:
    if pred_delay_min < 2:
        return "🟢 Fluide ( < 2 min )"
    elif pred_delay_min < 5:
        return "🟡 Modéré ( 2–5 min )"
    else:
        return "🔴 Élevé ( > 5 min )"

@st.cache_resource
def load_model(model_path: Path):
    bundle = joblib.load(model_path)
    return bundle["model"], bundle["features"], bundle.get("name", "model")

@st.cache_data
def load_routes_and_stops_mapping():
    """Charge les lignes, arrêts ET la correspondance ligne→arrêts"""
    gtfs_dir = PROJECT_ROOT / "data" / "raw" / "gtfs"
    
    # 1. Charger les lignes
    routes_path = gtfs_dir / "routes.txt"
    routes_df = pd.read_csv(routes_path) if routes_path.exists() else pd.DataFrame()
    routes_list = sorted(routes_df["route_short_name"].astype(str).dropna().unique().tolist()) if not routes_df.empty else ["A"]
    
    # 2. Charger les arrêts avec coordonnées
    stops_path = gtfs_dir / "stops.txt"
    stops_df = pd.read_csv(stops_path) if stops_path.exists() else pd.DataFrame()
    
    # 3. Charger trips pour avoir route_id → trip_id
    trips_path = gtfs_dir / "trips.txt"
    trips_df = pd.read_csv(trips_path) if trips_path.exists() else pd.DataFrame()
    
    # 4. Charger stop_times pour avoir trip_id → stop_id
    stop_times_path = gtfs_dir / "stop_times.txt"
    stop_times_df = pd.read_csv(stop_times_path) if stop_times_path.exists() else pd.DataFrame()
    
    # 5. Fusionner pour avoir route_id → stops
    if not trips_df.empty and not stop_times_df.empty and not routes_df.empty:
        # trips + routes
        trips_routes = trips_df.merge(routes_df[["route_id", "route_short_name"]], on="route_id")
        
        # trips + stop_times
        trips_stops = trips_routes.merge(
            stop_times_df[["trip_id", "stop_id"]], 
            on="trip_id"
        )
        
        # Groupe par ligne pour avoir tous les arrêts de chaque ligne
        route_stops_map = (
            trips_stops.groupby("route_short_name")["stop_id"]
            .apply(lambda x: sorted(set(x)))
            .to_dict()
        )
    else:
        route_stops_map = {}
    
    # 6. Créer la liste des arrêts avec infos complètes
# 6. Créer la liste des arrêts avec infos complètes
    if not stops_df.empty:
        def clean_stop_name(stop_id):
            """Enlève le préfixe TTR:XXXXX-"""
            if pd.isna(stop_id):
                return "Inconnu"
            stop_id = str(stop_id)
            # Enlever "TTR:" et tout jusqu'au dernier "-"
            if ":" in stop_id and "-" in stop_id:
                # Format: TTR:GAVSB-1T → 1T
                parts = stop_id.split(":")
                if len(parts) > 1:
                    last_part = parts[-1]  # GAVSB-1T
                    if "-" in last_part:
                        return last_part.split("-")[-1]  # 1T
                    return last_part
            return stop_id
        
        stops_df["stop_id_clean"] = stops_df["stop_id"].apply(clean_stop_name)
        
        # ✅ Clarifier les directions dans le label
        def format_label(row):
            code = row["stop_id_clean"]
            name = str(row["stop_name"])
            
            # Détecter la direction (1T ou 2T)
            if code.endswith("1T"):
                return f"{code} — {name} (→ Direction 1)"
            elif code.endswith("2T"):
                return f"{code} — {name} (← Direction 2)"
            else:
                return f"{code} — {name}"
        
        stops_df["label"] = stops_df.apply(format_label, axis=1)
        
        stops_list = stops_df[["stop_id", "stop_name", "label", "stop_lat", "stop_lon"]].to_dict("records")
    else:
        stops_list = []
    
    return routes_list, stops_list, route_stops_map

def build_features_input(feat_cols, route_short_name, hour, day_of_week, stop_freq, stop_lat, stop_lon, route_type):
    if 0 <= hour <= 5:
        period = "nuit"
    elif 6 <= hour <= 10:
        period = "matin"
    elif 11 <= hour <= 14:
        period = "midi"
    elif 15 <= hour <= 18:
        period = "apresmidi"
    else:
        period = "soir"

    is_weekend = 1 if day_of_week >= 5 else 0
    is_peak_hour = 1 if hour in [7, 8, 9, 17, 18, 19] else 0

    base = {
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_peak_hour": is_peak_hour,
        "route_type": route_type,
        "stop_lat": stop_lat,
        "stop_lon": stop_lon,
        "stop_freq": stop_freq,
    }

    onehots = {
        f"route_short_name_{route_short_name}": 1,
        f"period_of_day_{period}": 1,
    }

    row = {c: 0 for c in feat_cols}
    for k, v in base.items():
        if k in row:
            row[k] = v
    for k, v in onehots.items():
        if k in row:
            row[k] = v

    return pd.DataFrame([row], columns=feat_cols)

# ---------------- NAV ----------------
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

def go(p):
    st.session_state.page = p
    st.rerun()

with st.sidebar:
    st.title("Navigation")

    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("Accueil 🏠", use_container_width=True): go("Accueil")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("Data Viz 📊", use_container_width=True): go("Data Viz")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("Prédiction 🔮", use_container_width=True): go("Prédiction")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
    if st.button("À propos ℹ️", use_container_width=True): go("À propos")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        """
        <small>
        FilBleu Predictor — ML & Web Scraping<br>
        Réseau Fil Bleu (Tours)<br>
        2025<br>
        © Hafsa Mousalli<br>
        @ Imane Lemkhayer
        </small>
        """,
        unsafe_allow_html=True
    )

page = st.session_state.page

# ---------------- PAGES ----------------
if page == "Accueil":
    st.markdown("""
    <div class="hero-wrap">
      <h1 class="hero-title">Bienvenue sur FilBleu Predictor</h1>
      <p class="hero-sub">Prédiction de retard — réseau Fil Bleu (Tours) à partir de données GTFS &amp; GTFS-RT.</p>
      <p class="hero-tagline">L’outil pour explorer et estimer les retards du réseau Fil Bleu !</p>

      <div class="chips">
        <span class="chip">Tours</span>
        <span class="chip">GTFS</span>
        <span class="chip">GTFS-RT</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="card">
          <h3>📊 Data Visualization</h3>
          <p>Analysez la distribution des retards, les tendances temporelles (heures / jours)
             et les segments les plus impactés (lignes / arrêts) sur la période collectée.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explorer les données"):
            go("Data Viz")

    with col2:
        st.markdown("""
        <div class="card">
          <h3>🔮 Prédiction de retard</h3>
          <p>Choisissez une ligne, un arrêt et un contexte temporel. Obtenez une estimation du
             retard (minutes) et un indicateur de risque 🟢🟡🔴.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Faire une prédiction"):
            go("Prédiction")




elif page == "Prédiction":
    st.markdown("## 🔮 Prédiction de retard")

    TEST_PATH = PROJECT_ROOT / "data" / "final" / "test.csv"
    METRICS_CSV = PROJECT_ROOT / "models" / "metrics.csv"
    BEST_PARAMS = PROJECT_ROOT / "models" / "best_params.json"

    if not MODEL_PATH.exists():
        st.error(f"Modèle introuvable : {MODEL_PATH}\n➡️ Lance `python src/ml/train_model.py`.")
        st.stop()

    model, feat_cols, model_name = load_model(MODEL_PATH)
    routes_list, all_stops_list, route_stops_map = load_routes_and_stops_mapping()

    @st.cache_data
    def load_test(path: Path):
        if not path.exists():
            return None
        return pd.read_csv(path)

    def compute_preds_on_test(df_test: pd.DataFrame, y_col="delay_minutes"):
        X = df_test.copy()
        if y_col in X.columns:
            y = X[y_col].astype(float)
            X = X.drop(columns=[y_col])
        else:
            y = None

        for c in feat_cols:
            if c not in X.columns:
                X[c] = 0
        X = X[feat_cols]
        preds = model.predict(X)
        return preds, y

    tab1, tab2, tab3 = st.tabs(["📌 Présentation du modèle", "📈 Résultats (test)", "🧾 Prédire un trajet"])

    with tab1:
        st.subheader("📌 Présentation du modèle")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Modèle", model_name)
        with c2: st.metric("Nb features", str(len(feat_cols)))
        with c3: st.metric("Cible", "delay_minutes (min)")

        st.markdown("""
**Objectif :** prédire le **retard en minutes** à partir d’un contexte (ligne, arrêt, heure, jour, etc.).

**Pourquoi ce modèle ?**
- Les retards sont **non-linéaires** (heures de pointe, différences fortes entre lignes)
- Les modèles type **Gradient Boosting / Random Forest** gèrent bien ces effets

**Bonnes pratiques**
- Split **temporel** train/test  → Le modèle apprend sur le passé & teste sur le futur 

- Métrique principale : **MAE** (en minutes)
        """)

        if METRICS_CSV.exists():
            st.write("### Tableau des métriques")
            st.dataframe(pd.read_csv(METRICS_CSV), use_container_width=True)
        else:
            st.info("Aucune métrique trouvée (models/metrics.csv).")
        st.caption(
            "La MAE représente l’erreur moyenne en minutes entre le retard réel et le retard prédit. "
            "Par exemple, une MAE de 6 minutes signifie que la prédiction se trompe en moyenne de ±6 minutes."
        )

        if BEST_PARAMS.exists():
            st.write("### Hyperparamètres (meilleur modèle)")
            try:
                import json
                params = json.loads(BEST_PARAMS.read_text(encoding="utf-8"))
                
                if params:
                    # Afficher les paramètres dans des colonnes
                    cols = st.columns(len(params))
                    
                    # Noms simplifiés pour l'affichage
                    param_labels = {
                        "learning_rate": "Taux d'apprentissage",
                        "max_depth": "Profondeur max",
                        "n_estimators": "Nb d'arbres",
                        "min_samples_split": "Min échantillons (split)",
                        "min_samples_leaf": "Min échantillons (feuille)"
                    }
                    
                    for idx, (key, value) in enumerate(params.items()):
                        with cols[idx]:
                            label = param_labels.get(key, key)
                            st.metric(label, value)
                    
                    st.caption("""
                    Ces paramètres ont été trouvés automatiquement par GridSearch pour minimiser l'erreur.
                    """)
                else:
                    st.info("Modèle avec paramètres par défaut")
                    
            except Exception:
                st.info("best_params.json présent mais lecture impossible.")

        with st.expander("🔍 Voir les features utilisées par le modèle"):
            st.caption(f"**{len(feat_cols)} features au total**")
            
            # Afficher en 3 colonnes
            cols = st.columns(3)
            for idx, feat in enumerate(feat_cols):
                cols[idx % 3].write(f"• {feat}")    

    with tab2:
        st.subheader("📈 Résultats sur le jeu de test")
        df_test = load_test(TEST_PATH)

        if df_test is None:
            st.warning("test.csv introuvable. Lance `python src/ml/prepare_dataset.py` pour le générer.")
        else:
            preds, y = compute_preds_on_test(df_test, y_col="delay_minutes")
            df_res = pd.DataFrame({"y_true": y.values if y is not None else [None] * len(preds), "y_pred": preds})

        if y is not None:
            df_res = pd.DataFrame({
                "Retard réel (min)": y.values if y is not None else [None] * len(preds), 
                "Retard prédit (min)": preds
            })
            
            # ✅ AJOUTE cette ligne pour calculer l'erreur absolue
            df_res["Erreur absolue (min)"] = (df_res["Retard réel (min)"] - df_res["Retard prédit (min)"]).abs()
            
            colA, colB, colC = st.columns(3)
            with colA: st.metric("MAE (test)", f"{df_res['Erreur absolue (min)'].mean():.2f} min")
            with colB: st.metric("Erreur médiane", f"{df_res['Erreur absolue (min)'].median():.2f} min")
            with colC:
                pct5 = (df_res["Erreur absolue (min)"] > 5).mean() * 100
                st.metric("% erreurs > 5 min", f"{pct5:.1f}%")

        st.write("### Réalité vs Prédiction (échantillon)")
        n_show = st.slider("Nombre de lignes à afficher", 10, 500, 50)
        st.dataframe(df_res.head(n_show), use_container_width=True)

    with tab3:
        st.subheader("🧾 Prédire un trajet")
        st.caption("Renseigne une situation, on estime le retard (minutes) + un niveau de risque.")

        # Charger les données
        routes_list, all_stops_list, route_stops_map = load_routes_and_stops_mapping()

        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 1. Sélection de la ligne
            route = st.selectbox(
                "Choisir une ligne",
                options=routes_list
            )
            
            # ✅ Info sur les directions
            st.info(" **1** = Direction 1 | **2** = Direction 2 (sens inverse)")
            
            # 2. Filtrer les arrêts selon la ligne sélectionnée
            if route and route in route_stops_map:
                # Récupérer les stop_id de cette ligne
                valid_stop_ids = route_stops_map[route]
                
                # Filtrer la liste complète
                stops_for_route = [
                    stop for stop in all_stops_list 
                    if stop["stop_id"] in valid_stop_ids
                ]
            else:
                # Si pas de mapping, afficher tous
                stops_for_route = all_stops_list
            
            # 3. Sélection de l'arrêt (filtré)
            if stops_for_route:
                stop_choice = st.selectbox(
                    "Choisir un arrêt",
                    options=stops_for_route,
                    format_func=lambda x: x["label"]
                )
            else:
                st.warning("Aucun arrêt trouvé pour cette ligne")
                stop_choice = {"stop_id": "NA", "stop_name": "Inconnu", "label": "NA — Inconnu", "stop_lat": 47.39, "stop_lon": 0.68}
        
        with col2:
            hour = st.slider("Heure", 0, 23, 18)
            day_of_week = st.selectbox(
                "Jour de la semaine",
                options=list(range(7)),
                format_func=lambda d: ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][d]
            )

        # Récupérer les coordonnées de l'arrêt
        if stop_choice and isinstance(stop_choice, dict):
            stop_lat = stop_choice.get("stop_lat", 47.3941)
            stop_lon = stop_choice.get("stop_lon", 0.6848)
            stop_id = stop_choice.get("stop_id", "NA")
        else:
            stop_lat, stop_lon, stop_id = 47.3941, 0.6848, "NA"
        
        stop_freq = 0.0001
        route_type = 0 if str(route).upper() == "A" else 3

        if st.button("🔮 Lancer la prédiction"):
            X_input = build_features_input(
                feat_cols=feat_cols,
                route_short_name=str(route),
                hour=int(hour),
                day_of_week=int(day_of_week),
                stop_freq=float(stop_freq),
                stop_lat=float(stop_lat),
                stop_lon=float(stop_lon),
                route_type=int(route_type),
            )

            pred = float(model.predict(X_input)[0])

            st.markdown("### Résultat :")
            st.markdown(
                f"<div class='big-result'>{format_delay_minutes(pred)}</div>",
                unsafe_allow_html=True
            )

            delay_for_risk = max(0.0, pred)
            st.write("Niveau de risque :", risk_label(delay_for_risk))
            st.caption("⚠️ La fiabilité dépend des lignes/arrêts et des périodes réellement observées en collecte.")


elif page == "Data Viz":
    st.markdown("## 📊 Data Visualization")
    st.caption("Exploration des retards reconstruits (GTFS-RT + GTFS statique) sur la période de collecte.")

    # 1) Charger df AVANT les filtres ✅
    DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "delays_calculated.csv"
    DATA_TRAIN = PROJECT_ROOT / "data" / "final" / "train.csv"

    GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"
    TRIPS_PATH = GTFS_DIR / "trips.txt"
    ROUTES_PATH = GTFS_DIR / "routes.txt"
    STOPS_PATH = GTFS_DIR / "stops.txt"

    @st.cache_data
    def load_data():
        if DATA_PROCESSED.exists():
            return pd.read_csv(DATA_PROCESSED), "data/processed/delays_calculated.csv"
        if DATA_TRAIN.exists():
            return pd.read_csv(DATA_TRAIN), "data/final/train.csv"
        return None, None

    @st.cache_data
    def enrich_with_gtfs(df_):
        if not (TRIPS_PATH.exists() and ROUTES_PATH.exists() and STOPS_PATH.exists()):
            return df_
        if "trip_id" not in df_.columns or "stop_id" not in df_.columns:
            return df_

        trips = pd.read_csv(TRIPS_PATH, usecols=["trip_id", "route_id"])
        df2 = df_.merge(trips, on="trip_id", how="left")

        routes = pd.read_csv(ROUTES_PATH, usecols=["route_id", "route_short_name", "route_type"])
        df2 = df2.merge(routes, on="route_id", how="left")

        stops = pd.read_csv(STOPS_PATH, usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"])
        df2 = df2.merge(stops, on="stop_id", how="left")

        df2["route_short_name"] = df2.get("route_short_name", "Inconnu").fillna("Inconnu")
        df2["stop_name"] = df2.get("stop_name", df2["stop_id"].astype(str)).fillna(df2["stop_id"].astype(str))
        return df2

    df, src = load_data()
    if df is None:
        st.error("Aucun dataset trouvé. Attendu : data/processed/delays_calculated.csv ou data/final/train.csv")
        st.stop()

    st.info(f"Source utilisée : **{src}** — {len(df):,} lignes".replace(",", " "))
    df = enrich_with_gtfs(df)

    # --------- Normalisation delay_minutes ----------
    if "delay_minutes" not in df.columns:
        possible = [c for c in df.columns if "delay" in c.lower()]
        if possible:
            df = df.rename(columns={possible[0]: "delay_minutes"})
        else:
            st.error("Colonne delay_minutes introuvable.")
            st.stop()

    df["delay_minutes"] = pd.to_numeric(df["delay_minutes"], errors="coerce")
    df = df.dropna(subset=["delay_minutes"])
    df = df[df["delay_minutes"].between(-10, 60)]

    # ✅✅✅ FIX IMPORTANT : heure + jour FIABLES depuis collecte_datetime
    if "collecte_datetime" in df.columns:
        df["collecte_datetime"] = pd.to_datetime(df["collecte_datetime"], errors="coerce")
        df["hour"] = df["collecte_datetime"].dt.hour.fillna(0).astype(int)
        df["dow_calc"] = df["collecte_datetime"].dt.dayofweek.fillna(0).astype(int)  # 0=Lun ... 6=Dim
    else:
        if "hour" not in df.columns:
            df["hour"] = 0
        df["dow_calc"] = 0

    # 2) Filtres EN HAUT ✅ + aucun filtre par défaut ✅
    st.markdown("### Filtres")
    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 2, 2])

    with fcol1:
        route_sel = st.multiselect(
            "Lignes",
            options=sorted(df["route_short_name"].astype(str).dropna().unique().tolist()),
            default=[]
        )

    with fcol2:
        top_stops = df["stop_name"].astype(str).value_counts().head(200).index.tolist()
        stop_sel = st.multiselect(
            "Arrêts",
            options=top_stops,
            default=[]
        )

    with fcol3:
        hour_range = st.slider("Heure", 0, 23, value=(0, 23))

    DAY_MAP = {0:"Lundi", 1:"Mardi", 2:"Mercredi", 3:"Jeudi", 4:"Vendredi", 5:"Samedi", 6:"Dimanche"}
    DAY_REV = {v:k for k,v in DAY_MAP.items()}

    with fcol4:
        dow_names = st.multiselect(
            "Jours",
            options=[DAY_MAP[i] for i in range(7)],
            default=[]
        )
        dow_sel = [DAY_REV[name] for name in dow_names]  # 0..6

    # 3) Application des filtres (si vide => pas de filtre) ✅
    dff = df.copy()
    if route_sel:
        dff = dff[dff["route_short_name"].astype(str).isin(route_sel)]
    if stop_sel:
        dff = dff[dff["stop_name"].astype(str).isin(stop_sel)]
    if hour_range != (0, 23):
        dff = dff[dff["hour"].between(hour_range[0], hour_range[1])]
    if dow_sel:
        # ✅ FIX : filtre sur dow_calc (fiable), PAS sur day_of_week
        dff = dff[dff["dow_calc"].isin(dow_sel)]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Données", "⏱️ Tendances", "🚌 Lignes", "🚏 Arrêts", "🧭 Couverture des données"])


### PAGE DONNÉES
    with tab1:
        st.markdown("### 📄 Données filtrées")
        if dff.empty:
            st.warning(
                "⚠️ Aucune donnée ne correspond à ces filtres.\n\n"
                "Essaie de changer le jour, l’heure ou de retirer un filtre."
            )
            st.stop()
        colA, colB, colC, colD, colE = st.columns((5))
        with colA: st.metric("Observations", f"{len(dff):,}".replace(",", " "))
        mean_delay = float(dff["delay_minutes"].mean()) if len(dff) else 0.0
        median_delay = float(dff["delay_minutes"].median()) if len(dff) else 0.0
        pct_ontime = (dff["delay_minutes"].abs() <= 0.5).mean() * 100 if len(dff) else 0.0
        with colB: st.metric("Retard moyen", format_delay_stat(mean_delay))
        with colC: st.metric("Retard médian", format_delay_stat(median_delay))
        max_delay = float(dff["delay_minutes"].max()) if len(dff) else 0.0
        with colD: st.metric("Retard max", format_delay_stat(max_delay))
        with colE: st.metric("À l’heure (±30s)", f"{pct_ontime:.1f}%")



        st.markdown("### 🔥 Les plus gros retards observés")
        cols_public = [c for c in ["collecte_datetime","route_short_name","stop_name","hour","delay_minutes"] if c in dff.columns]
        top_cases = (
            dff[cols_public]
            .sort_values("delay_minutes", ascending=False)
            .head(30)
            .reset_index(drop=True)
        )
        st.dataframe(top_cases, use_container_width=True)



        st.markdown("📊 Quantiles du retard (en minutes/secondes)")
        quantiles = dff["delay_minutes"].quantile([0.05, 0.25, 0.5, 0.75, 0.95])
        q_df = pd.DataFrame(
            [quantiles.values],
            columns=["5%", "25%", "50% (médiane)", "75%", "95%"],
            index=["delay_minutes"]
        )

        def format_delay(x):
            if pd.isna(x):
                return "—"
            x = float(x)
            if abs(x) < 1:
                return f"{int(round(x * 60))} s"
            return f"{x:.2f} min"

        q_df = q_df.applymap(format_delay)
        st.dataframe(q_df, use_container_width=True)
        st.info(
            "📊 La majorité des passages présentent de faibles retards (médiane ≈ 1 min). "
            "Cependant, 75% des passages présentent un retard inférieur à ~3–4 minutes "
            "(retard habituel). Les valeurs au-delà du 95e percentile correspondent à des "
            "situations exceptionnelles ou à des incidents majeurs."
        )

        with st.expander("🔍 Voir les données brutes"):
            st.dataframe(dff.head(300), use_container_width=True)


### PAGE TENDANCE 
    with tab2:
        st.markdown("### ⏱️ Tendances temporelles")
        hourly = (
            dff.assign(on_time=(dff["delay_minutes"].abs() <= 0.5))
            .groupby("hour", as_index=False)
            .agg(
                median_delay=("delay_minutes", "median"),
                pct_ontime=("on_time", "mean"),
                n=("delay_minutes", "size"),
            )
            .sort_values("hour")
        )

        if hourly.empty:
            st.warning("Pas assez de données avec ces filtres.")
            st.stop()

        # KPIs simples
        h_crit = int(hourly.loc[hourly["median_delay"].idxmax(), "hour"])
        med_max = float(hourly["median_delay"].max())
        st.metric("Heure la plus critique", f"{h_crit}h — médiane {format_delay_stat(med_max)}")

    
        # Petit tableau lisible
        st.markdown("")
        show = hourly.copy()
        show["pct_ontime"] = (show["pct_ontime"] * 100).round(1)
        show["median_delay"] = show["median_delay"].round(2)
        show = show.rename(columns={
            "hour": "heure",
            "median_delay": "médiane retard (min)",
            "pct_ontime": "% à l'heure (±30s)",
            "n": "observations",
        })
        st.dataframe(show, use_container_width=True)

        st.caption(
            "La médiane met en évidence un retard typique plus élevé en fin d’après-midi, "
        )

### Page Ligne
    with tab3:
        st.markdown("### 🚌 Analyse par ligne")
        by_route = (
            dff.groupby("route_short_name", as_index=False)
            .agg(n=("delay_minutes","size"), mean_delay=("delay_minutes","mean"))
            .sort_values("mean_delay", ascending=False)
        )
        st.dataframe(by_route.head(25), use_container_width=True)

        st.markdown("### 📊 Top lignes par retard moyen")
        topN = st.slider("Choisir le nombre de lignes les plus en retard à afficher", 5, 50, 15, key="top_routes")
        top_routes = by_route.head(topN).set_index("route_short_name")
        st.bar_chart(top_routes["mean_delay"])

### PAGE ARRET
    with tab4:
        st.markdown("### 🚏 Analyse par arrêt")
        by_stop = (
            dff.groupby("stop_name", as_index=False)
            .agg(n=("delay_minutes","size"), mean_delay=("delay_minutes","mean"))
            .sort_values("mean_delay", ascending=False)
        )
        st.dataframe(by_stop.head(25), use_container_width=True)

        st.markdown("### 🚏 Retard moyen observé aux arrêts")
        st.caption(
            "Ce graphique ne représente pas un retard de l’arrêt lui-même, "
            "mais le retard moyen des véhicules lorsqu’ils passent par cet arrêt."
        )

        topN2 = st.slider(
            "Choisir le nombre d’arrêts avec le plus fort retard moyen des véhicules à afficher",
            5, 50, 15,
            key="top_stops"
        )
        top_stops_df = by_stop.head(topN2).set_index("stop_name")
        st.bar_chart(top_stops_df["mean_delay"])

### PAGE COUVERTURE 
    with tab5:
        st.markdown("### 🧭 Couverture des données")
        st.caption(
            "Cette section permet de comprendre **quand** les données ont été collectées "
            "et d’évaluer leur **représentativité dans le temps**."
        )

        if "collecte_datetime" in df.columns:
            df["collecte_datetime"] = pd.to_datetime(df["collecte_datetime"], errors="coerce")
            df["collecte_date"] = df["collecte_datetime"].dt.date

            jours_collecte = (
                df["collecte_date"]
                .value_counts()
                .sort_index()
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📅 Nombre de jours collectés", jours_collecte.shape[0])
            with col2:
                st.metric("📊 Total d'observations", f"{jours_collecte.sum():,}".replace(",", " "))


            st.markdown("#### 📋 Détail des collectes par jour")
            detail_jours = (
                    jours_collecte
                    .rename("Nombre d'observations")
                    .reset_index()
                    .rename(columns={"index": "collecte_date"})
                )

                # Ajouter le jour de la semaine
            detail_jours["Jour"] = pd.to_datetime(
                    detail_jours["collecte_date"]
                ).dt.day_name(locale="fr_FR")

                # Réordonner les colonnes
            detail_jours = detail_jours[
                    ["collecte_date", "Jour", "Nombre d'observations"]
                ]
            st.dataframe(detail_jours, use_container_width=True)


            st.caption(
                "⚠️ Les analyses et prédictions reflètent uniquement les jours et périodes "
                "présents dans la collecte."
            )

        else:
            st.warning(
                "La colonne **collecte_datetime** n’est pas disponible dans ce dataset. "
                "La couverture temporelle ne peut pas être évaluée."
            )

elif page == "À propos":
    st.markdown("## ℹ️ À propos de FilBleu Predictor")

    st.markdown("""
### 🚎 FilBleu Predictor, c’est quoi ?

**FilBleu Predictor** est une application qui permet :
- d’**explorer** les retards observés sur le réseau **Fil Bleu (Tours)**,
- et d’**estimer un retard (en minutes)** selon une situation donnée (ligne, arrêt, heure, jour).

L’objectif est simple : offrir une lecture claire des retards et un outil de prédiction facile à tester.
""")

    st.markdown("""
### 📊 D’où viennent les données ?

L’application s’appuie sur deux familles de données :

**1) GTFS statique (horaires théoriques)**
- lignes, arrêts, trajets, horaires planifiés

**2) GTFS-RT (temps réel)**
- mises à jour d’horaires et informations de circulation au format Protocol Buffers

📌 Les retards ne sont pas toujours fournis sous une forme directement exploitable.  
➡️ Ils sont **reconstruits** en comparant l'**heure prévue** (horaires théoriques) avec l'**heure réelle** (moment d'arrivée ou de passage), en tenant compte du fuseau horaire Europe/Paris.
""")

    st.markdown("""
### ⚙️ Comment ça fonctionne ?

Le fonctionnement suit 4 étapes :

1) **Collecte** du temps réel (GTFS-RT)  
2) **Parsing** des fichiers et mise en forme des données  
3) **Reconstruction** du retard `delay_minutes` (en minutes)  
4) **Analyse & prédiction** via un modèle de régression entraîné sur les données collectées

L’application propose ensuite :
- une page **Data Viz** pour comprendre les retards,
- une page **Prédiction** pour estimer un retard dans un contexte donné.
""")

    st.markdown("""
### 📈 Comment lire les résultats ?

- Un retard **positif** signifie que le véhicule est **en retard**.
- Un retard **négatif** signifie qu’il est **en avance** (selon la reconstruction).
- L’indicateur 🟢🟡🔴 donne un **niveau de risque** basé sur le retard estimé.
""")

    st.markdown("""
### ⚠️ Ce qu'il faut garder en tête

Les résultats reflètent **uniquement les périodes où des données ont été collectées**.  
Selon les jours, les horaires et les lignes couvertes, la représentativité peut varier.

**Limitation importante :** La collecte GTFS-RT a capturé 10 jours (12 déc 2025 - 7 jan 2026), dont 4 jours pendant les vacances scolaires (25 déc, 31 déc, 1er jan, 7 jan). Cependant, le GTFS statique public ne contenait pas les grilles horaires exceptionnelles de ces jours. Par conséquent, **seuls 7 jours de service régulier** ont pu être exploités pour l'analyse et l'entraînement du modèle (687k observations).

Les retards peuvent aussi dépendre d'éléments externes non présents dans les données :
trafic, météo, incidents, affluence, travaux, événements…
""")

    st.markdown("""
### ➕ Axes d'amélioration possibles


- Collecte plus longue et plus régulière
- Ajout de variables externes (météo, vacances scolaires, etc.)
- Suivi de la performance dans le temps
""")

    st.markdown("---")
    st.markdown("### 👤 Auteurs")
    st.markdown("""
- **Hafsa Mousalli**  
- **Imane Lemkhayer**
""")

    st.caption(f"MAJ le : {date.today().isoformat()}")
