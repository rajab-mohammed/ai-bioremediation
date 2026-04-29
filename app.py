import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI Bioremediation System", layout="centered")

st.title("AI-Assisted Soil Bioremediation Recommendation System")

kb = pd.read_excel("soil_bacteria_kb_10gen_ai_v1.xlsx", sheet_name="Bacteria_KB")

st.header("Enter Soil Sample Data")

pH = st.number_input("pH", 0.0, 14.0, 8.2)
EC = st.number_input("EC / Salinity", 0.0, 20.0, 4.6)
OM = st.number_input("Organic Matter (%)", 0.0, 20.0, 0.9)
N = st.number_input("Nitrogen status (0–1)", 0.0, 1.0, 0.25)
P = st.number_input("Phosphorus status (0–1)", 0.0, 1.0, 0.30)
K = st.number_input("Potassium status (0–1)", 0.0, 1.0, 0.55)
Moisture = st.number_input("Moisture (%)", 0.0, 100.0, 32.0)

sample = {
    "Sample_ID": "S01",
    "pH": pH,
    "EC": EC,
    "Organic_Matter": OM,
    "N": N,
    "P": P,
    "K": K,
    "Moisture": Moisture
}

def diagnose_soil(sample):
    problems = []

    if sample["pH"] < 6.0:
        problems.append("Acidic pH")
    elif sample["pH"] > 7.8:
        problems.append("Alkaline pH")

    if sample["EC"] > 4.0:
        problems.append("High salinity")

    if sample["Organic_Matter"] < 1.5:
        problems.append("Low organic matter")

    if sample["N"] < 0.4:
        problems.append("Low N")

    if sample["P"] < 0.4:
        problems.append("Low P")

    if sample["K"] < 0.4:
        problems.append("Low K")

    if sample["Moisture"] < 25:
        problems.append("Low moisture")
    elif sample["Moisture"] > 70:
        problems.append("High moisture")

    if len(problems) == 0:
        problems.append("No major limitation")

    return problems

def score_bacteria(row, problems, sample):
    score = 0
    reasons = []

    target = str(row.get("Target_Problem", "")).lower()
    function = str(row.get("Main_Function", "")).lower()
    tags = str(row.get("AI_Tag", "")).lower()
    limitation = str(row.get("Limitation", "")).lower()

    problems_lower = [p.lower() for p in problems]

    if "low n" in problems_lower:
        if "nitrogen" in function or "n_fixer" in tags or "low n" in target:
            score += 4
            reasons.append("matches low nitrogen problem")

    if "low p" in problems_lower:
        if "phosphate" in function or "p_solubilizer" in tags or "low p" in target:
            score += 4
            reasons.append("matches low phosphorus problem")

    if "high salinity" in problems_lower:
        if "salinity" in target or "salt_tolerant" in tags or "stress" in function:
            score += 4
            reasons.append("matches salinity stress")

    if "low organic matter" in problems_lower:
        if "organic" in target or "om_decomposer" in tags or "decomposition" in function:
            score += 4
            reasons.append("matches low organic matter problem")

    if "low k" in problems_lower:
        if "pgpr" in tags or "growth" in function:
            score += 1
            reasons.append("supports general plant growth")

    # Optional pH suitability
    if "pH_min" in kb.columns and "pH_max" in kb.columns:
        if pd.notna(row["pH_min"]) and pd.notna(row["pH_max"]):
            if row["pH_min"] <= sample["pH"] <= row["pH_max"]:
                score += 2
                reasons.append("pH is suitable")
            else:
                score -= 1
                reasons.append("pH may be less suitable")

    # Optional limitation penalty
    if "high salinity" in problems_lower and "salinity" in limitation:
        score -= 1
        reasons.append("limitation: salinity may reduce activity")

    return score, "; ".join(reasons)

if st.button("Analyze Sample"):
    detected_problems = diagnose_soil(sample)

    results = []
    for _, row in kb.iterrows():
        score, reason = score_bacteria(row, detected_problems, sample)
        results.append({
            "Bacteria": row["Bacteria"],
            "Score": score,
            "Main_Function": row.get("Main_Function", ""),
            "Reason": reason
        })

    result_df = pd.DataFrame(results).sort_values("Score", ascending=False)

    st.subheader("Detected Soil Problems")
    st.write(detected_problems)

    st.subheader("Recommended Bacteria Ranking")
    st.dataframe(result_df, use_container_width=True)

    best = result_df.iloc[0]

    st.success(f"Best bacteria: {best['Bacteria']}")
    st.write("Reason:", best["Reason"])
