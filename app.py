import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(
    page_title="AI Soil Bioremediation System",
    layout="centered"
)

st.title("AI-Assisted Soil Bioremediation Recommendation System")
st.write("Enter soil sample results to get the recommended bacteria.")

# Load knowledge base
kb = pd.read_excel(
    "soil_bacteria.xlsx",
    sheet_name="Bacteria_KB"
)

st.header("Enter Soil Sample Data")

pH = st.number_input("pH", min_value=0.0, max_value=14.0, value=8.2)

EC = st.number_input(
    "EC (µS/cm)",
    min_value=0.0,
    value=20300.0
)

OM = st.number_input(
    "Organic Matter (%)",
    min_value=0.0,
    value=0.9
)

# Carbon is calculated automatically from organic matter
Carbon = OM / 1.724

st.write(f"Estimated Organic Carbon (%): {Carbon:.2f}")

N = st.number_input(
    "Total Nitrogen (mg/kg)",
    min_value=0.0,
    value=387.0
)

P = st.number_input(
    "Available Phosphorus (mg/kg)",
    min_value=0.0,
    value=4.0
)

K = st.number_input(
    "Available Potassium (mg/kg)",
    min_value=0.0,
    value=236.0
)

Moisture = st.number_input(
    "Moisture (%)",
    min_value=0.0,
    max_value=100.0,
    value=32.0
)

sample = {
    "Sample_ID": "S01",
    "pH": pH,
    "EC": EC,
    "Organic_Matter": OM,
    "Carbon": Carbon,
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

    # EC is entered as µS/cm
    if sample["EC"] > 4000:
        problems.append("High salinity")

    if sample["Organic_Matter"] < 1.5:
        problems.append("Low organic matter")

    # Carbon is calculated, not entered manually
    if sample["Carbon"] < 1.0:
        problems.append("Low carbon")

    # N, P, K are now mg/kg
    if sample["N"] < 250:
        problems.append("Low N")

    if sample["P"] < 10:
        problems.append("Low P")

    if sample["K"] < 100:
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

    if "pH_min" in row and "pH_max" in row:
        if pd.notna(row["pH_min"]) and pd.notna(row["pH_max"]):
            if row["pH_min"] <= sample["pH"] <= row["pH_max"]:
                score += 2
                reasons.append("pH is suitable")
            else:
                score -= 1
                reasons.append("pH may be less suitable")

    if "high salinity" in problems_lower and "salinity" in limitation:
        score -= 1
        reasons.append("limitation: salinity may reduce activity")

    return score, "; ".join(reasons)


def calculate_ai_similarity(kb, detected_problems):
    problem_text = " ".join(detected_problems)

    if "AI_Profile" not in kb.columns:
        kb["AI_Profile"] = (
            kb["Target_Problem"].astype(str) + " " +
            kb["Main_Function"].astype(str) + " " +
            kb["AI_Tag"].astype(str) + " " +
            kb["Limitation"].astype(str)
        )

    texts = [problem_text] + kb["AI_Profile"].fillna("").astype(str).tolist()

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    similarity_scores = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:]
    ).flatten()

    kb["AI_Similarity"] = similarity_scores

    return kb


if st.button("Analyze Sample"):

    detected_problems = diagnose_soil(sample)

    kb = calculate_ai_similarity(kb, detected_problems)

    results = []

    for _, row in kb.iterrows():
        rule_score, reason = score_bacteria(row, detected_problems, sample)

        final_score = rule_score + (row["AI_Similarity"] * 10)

        results.append({
            "Bacteria": row["Bacteria"],
            "Rule_Score": round(rule_score, 2),
            "AI_Similarity": round(row["AI_Similarity"], 3),
            "Final_Score": round(final_score, 2),
            "Main_Function": row.get("Main_Function", ""),
            "Reason": reason
        })

    result_df = pd.DataFrame(results).sort_values(
        "Final_Score",
        ascending=False
    )

    st.subheader("Detected Soil Problems")
    st.write(detected_problems)

    support_actions = []

    if "Low carbon" in detected_problems:
        support_actions.append(
            "Add organic matter to improve soil carbon content."
        )

    if "Low organic matter" in detected_problems:
        support_actions.append(
            "Add compost or organic residues."
        )

    if "High salinity" in detected_problems:
        support_actions.append(
            "Improve drainage and use salt-tolerant bacterial strains."
        )

    if "Low moisture" in detected_problems:
        support_actions.append(
            "Improve irrigation management before bacterial application."
        )

    if support_actions:
        st.subheader("Recommended Support Actions")
        for action in support_actions:
            st.write("- " + action)

    st.subheader("Recommended Bacteria Ranking")
    st.dataframe(result_df, use_container_width=True)

    best = result_df.iloc[0]

    st.success(f"Best recommended bacteria: {best['Bacteria']}")
    st.write("Final Score:", best["Final_Score"])
    st.write("Reason:", best["Reason"])
