import pandas as pd
import streamlit as st

st.set_page_config(page_title="Soil AI Bioremediation System", layout="centered")

st.title("AI-Assisted Soil Bioremediation Recommendation System")
st.write("Enter soil sample data to diagnose problems and recommend suitable bacteria.")

kb = pd.read_excel("soil_bacteria_kb_10gen_ai_v1.xlsx", sheet_name="Bacteria_KB")

st.header("Soil Sample Data")

pH = st.number_input("pH", 0.0, 14.0, 7.5)
EC = st.number_input("EC (Salinity)", 0.0, 10.0, 2.5)
OM = st.number_input("Organic Matter (%)", 0.0, 10.0, 1.2)
N = st.number_input("Nitrogen (0–1)", 0.0, 1.0, 0.3)
P = st.number_input("Phosphorus (0–1)", 0.0, 1.0, 0.3)
K = st.number_input("Potassium (0–1)", 0.0, 1.0, 0.5)
Moisture = st.number_input("Moisture (%)", 0.0, 100.0, 35.0)

sample = {"pH": pH, "EC": EC, "OM": OM, "N": N, "P": P, "K": K, "Moisture": Moisture}

def diagnose(s):
    problems = []
    if s["pH"] < 6: problems.append("Acidic pH")
    elif s["pH"] > 7.8: problems.append("Alkaline pH")
    if s["EC"] > 4: problems.append("High salinity")
    if s["OM"] < 1.5: problems.append("Low organic matter")
    if s["N"] < 0.4: problems.append("Low N")
    if s["P"] < 0.4: problems.append("Low P")
    if s["K"] < 0.4: problems.append("Low K")
    if s["Moisture"] < 25: problems.append("Low moisture")
    if not problems: problems.append("No major issue")
    return problems

def score(row, probs):
    tags = str(row.get("AI_Tag","")).lower()
    score = 0
    if "low n" in str(probs).lower() and "n_fixer" in tags: score += 3
    if "low p" in str(probs).lower() and "p_solubilizer" in tags: score += 3
    if "salinity" in str(probs).lower() and "salt" in tags: score += 3
    if "organic" in str(probs).lower() and "decomposer" in tags: score += 3
    if "pgpr" in tags: score += 1
    return score

if st.button("Analyze"):
    problems = diagnose(sample)
    results = []
    for _, r in kb.iterrows():
        results.append({"Bacteria": r["Bacteria"], "Score": score(r, problems)})
    df = pd.DataFrame(results).sort_values("Score", ascending=False)

    st.write("Problems:", problems)
    st.dataframe(df)
    st.success(f"Best: {df.iloc[0]['Bacteria']}")
