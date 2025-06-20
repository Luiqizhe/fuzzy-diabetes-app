# -*- coding: utf-8 -*-
"""Diabetes Risk (Fuzzy).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PeEKjWD9ZBFv-osIHgUS1k3N8kDEu_bL

# Preparation

Core Fuzzy Rules

IF Glucose ≥ 126 mg/dL (Diabetic) AND BMI ≥ 30 (Obese)
THEN Risk = High
*(ADA: Fasting glucose ≥126 + obesity = high risk)*

IF Glucose 100–125 mg/dL (Prediabetic) AND Age ≥ 55 (Elderly)
THEN Risk = Medium
*(ADA: Prediabetes + age ≥55 = elevated risk)*

IF DiabetesPedigreeFunction ≥ 0.8 (High Genetic Risk) AND Pregnancies ≥ 3
THEN Risk = Medium
(Gestational diabetes history + genetic risk)

IF BloodPressure ≥ 140/90 mmHg (Hypertensive) AND BMI ≥ 25 (Overweight)
THEN Risk = Medium
(Hypertension + overweight = metabolic syndrome risk)

IF Glucose ≥ 126 mg/dL AND Age ≤ 30 (Young)
THEN Risk = High
(Early-onset hyperglycemia = high risk regardless of age)

IF BMI ≥ 30 AND Age 25–60 (Middle-Aged)
THEN Risk = Medium
(Obesity in middle age = moderate risk)

IF DiabetesPedigreeFunction ≥ 0.8 AND Glucose 100–125 mg/dL
THEN Risk = Medium
(Genetic risk + prediabetes = elevated risk)

IF Pregnancies ≥ 3 AND BMI ≥ 25 (Overweight)
THEN Risk = Medium
(Gestational diabetes history + overweight)

IF Glucose ≤ 99 mg/dL (Normal) AND BMI 18.5–24.9 (Normal)
THEN Risk = Low
(Healthy range = low risk)

IF Age ≤ 30 AND Glucose ≤ 99 AND BMI ≤ 24.9
THEN Risk = Very Low
(Young, healthy metrics = minimal risk)

IF BloodPressure ≥ 140/90 AND Glucose ≥ 126
THEN Risk = High
(Hypertension + diabetes = compounded risk)

IF BMI ≥ 30 AND DiabetesPedigreeFunction ≥ 0.5
THEN Risk = Medium
(Obesity + moderate genetic risk)

IF Age ≥ 55 AND BMI ≥ 25
THEN Risk = Medium
(Elderly + overweight = age-related risk)

IF Glucose ≥ 126 AND BloodPressure ≥ 140/90
THEN Risk = High
(ADA: Comorbid diabetes and hypertension)

IF Glucose ≤ 99 AND DiabetesPedigreeFunction ≤ 0.4
THEN Risk = Very Low
(Low genetic risk + normal glucose)
"""

"""# Data Loading

"""

#cell 2
# Data Loading
import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Load Data ---
try:
    df = pd.read_csv('https://raw.githubusercontent.com/Duzttt/FL-Diabetes-prediction/refs/heads/main/diabetes.csv')
    st.success("Dataset loaded successfully.")
except FileNotFoundError:
    st.error("Error: 'diabetes.csv' not found. Please check the file path.")
    st.stop()

# --- Data Preprocessing ---
cols_with_zeros_as_missing = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
df[cols_with_zeros_as_missing] = df[cols_with_zeros_as_missing].replace(0, np.nan)

for col in cols_with_zeros_as_missing:
    median_val = df[col].median()
    df[col].fillna(median_val, inplace=True)
    st.write(f"Filled missing values in '{col}' with median: {median_val}")

# --- FCM Helper ---
def get_fcm_mf_params(data_series, n_clusters, m=2, error=0.005, maxiter=1000):
    data_reshaped = data_series.values.reshape(-1, 1)
    cntr, u, _, _, _, _, fpc = fuzz.cluster.cmeans(
        data_reshaped.T, n_clusters, m=m, error=error, maxiter=maxiter, init=None
    )
    sorted_centers = np.sort(cntr.flatten())
    sigmas = []

    if n_clusters > 1:
        avg_dist = np.mean(np.diff(sorted_centers))
        base_sigma = avg_dist * 0.40
        sigmas = [base_sigma] * n_clusters
    else:
        sigmas.append(data_series.std() / 2)

    return sorted_centers, sigmas, fpc

# --- FPC Analysis ---
fcm_mf_params = {}
feature_columns = ['Glucose', 'BMI', 'Age', 'BloodPressure', 'Pregnancies',
                   'DiabetesPedigreeFunction', 'SkinThickness', 'Insulin']
n_clusters_range = range(2, 7)

st.subheader("Fuzzy Partition Coefficient (FPC) Evaluation")

for col_name in feature_columns:
    st.markdown(f"**Feature: {col_name}**")
    fpcs = []
    data_reshaped = df[col_name].values.reshape(-1, 1).T

    for n_c in n_clusters_range:
        try:
            _, _, _, _, _, _, fpc = fuzz.cluster.cmeans(
                data_reshaped, n_c, m=2, error=0.005, maxiter=1000, init=None
            )
            fpcs.append(fpc)
            st.write(f"n_clusters={n_c}, FPC={fpc:.4f}")
        except Exception as e:
            st.warning(f"Error running FCM for {n_c} clusters on {col_name}: {e}")
            fpcs.append(np.nan)

    fig, ax = plt.subplots()
    ax.plot(n_clusters_range, fpcs, marker='o', linestyle='-')
    ax.set_title(f'FPC vs. Number of Clusters for {col_name}')
    ax.set_xlabel('Number of Clusters (n_clusters)')
    ax.set_ylabel('FPC')
    ax.grid(True)
    ax.set_xticks(list(n_clusters_range))
    st.pyplot(fig)

st.info("Review the FPC plots above. Look for an 'elbow point' where the FPC levels off to choose the best number of clusters.")

# --- Define how many fuzzy sets you want for each input feature. ---
# IMPORTANT: Adjust these values based on the FPC plots you just reviewed.
# Example: If Glucose FPC plot shows an elbow at 4, set n_clusters_glucose = 4.
n_clusters_glucose = 4 # Defaulting to 3, adjust based on FPC plot
n_clusters_bmi = 4     # Defaulting to 3, adjust based on FPC plot
n_clusters_age = 4     # Defaulting to 3, adjust based on FPC plot
n_clusters_blood_pressure = 5 # Defaulting to 3, adjust based on FPC plot
n_clusters_pregnancies = 5 # Defaulting to 3, adjust based on FPC plot
n_clusters_dpf = 4     # Defaulting to 3, adjust based on FPC plot
n_clusters_skin_thickness = 5 # Defaulting to 3, adjust based on FPC plot
n_clusters_insulin = 5 # Defaulting to 3, adjust based on FPC plot

# --- Apply FCM for each input feature with the CHOSEN n_clusters ---
# Glucose
centers, sigmas, fpc = get_fcm_mf_params(df['Glucose'], n_clusters_glucose)
fcm_mf_params['glucose'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"Glucose FCM FPC (chosen {n_clusters_glucose} clusters): {fpc:.4f}")

# BMI
centers, sigmas, fpc = get_fcm_mf_params(df['BMI'], n_clusters_bmi)
fcm_mf_params['bmi'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"BMI FCM FPC (chosen {n_clusters_bmi} clusters): {fpc:.4f}")

# Age
centers, sigmas, fpc = get_fcm_mf_params(df['Age'], n_clusters_age)
fcm_mf_params['age'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"Age FCM FPC (chosen {n_clusters_age} clusters): {fpc:.4f}")

# BloodPressure
centers, sigmas, fpc = get_fcm_mf_params(df['BloodPressure'], n_clusters_blood_pressure)
fcm_mf_params['blood_pressure'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"BloodPressure FCM FPC (chosen {n_clusters_blood_pressure} clusters): {fpc:.4f}")

# Pregnancies
centers, sigmas, fpc = get_fcm_mf_params(df['Pregnancies'], n_clusters_pregnancies)
fcm_mf_params['pregnancies'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"Pregnancies FCM FPC (chosen {n_clusters_pregnancies} clusters): {fpc:.4f}")

# DiabetesPedigreeFunction
centers, sigmas, fpc = get_fcm_mf_params(df['DiabetesPedigreeFunction'], n_clusters_dpf)
fcm_mf_params['diabetes_pedigree_function'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"DPF FCM FPC (chosen {n_clusters_dpf} clusters): {fpc:.4f}")

# SkinThickness
centers, sigmas, fpc = get_fcm_mf_params(df['SkinThickness'], n_clusters_skin_thickness)
fcm_mf_params['skin_thickness'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"SkinThickness FCM FPC (chosen {n_clusters_skin_thickness} clusters): {fpc:.4f}")

# Insulin
centers, sigmas, fpc = get_fcm_mf_params(df['Insulin'], n_clusters_insulin)
fcm_mf_params['insulin'] = {'centers': centers, 'sigmas': sigmas, 'fpc': fpc}
st.write(f"Insulin FCM FPC (chosen {n_clusters_insulin} clusters): {fpc:.4f}")

"""# Exploratary Data Analysis"""

#cell 3
# Exploratary Data Analysis

# --- 2. Define Fuzzy Antecedents and Consequent ---

# Universe of Discourse (ensure these ranges match your data AFTER preprocessing)
# It's best to derive these from your actual data's min/max if possible,
# or ensure they cover the full range of expected values.
# For simplicity, using your specified ranges. Adjust if your actual data ranges differ significantly.

# --- Define Universes for Antecedents and Consequent ---
glucose_uni = np.arange(df['Glucose'].min() * 0.9, df['Glucose'].max() * 1.1 + 1, 1)
bmi_uni = np.arange(df['BMI'].min() * 0.9, df['BMI'].max() * 1.1 + 0.1, 0.1)
age_uni = np.arange(df['Age'].min() * 0.9, df['Age'].max() * 1.1 + 1, 1)
bp_uni = np.arange(df['BloodPressure'].min() * 0.9, df['BloodPressure'].max() * 1.1 + 1, 1)
preg_uni = np.arange(df['Pregnancies'].min(), df['Pregnancies'].max() + 1, 1)
dpf_uni = np.arange(df['DiabetesPedigreeFunction'].min() * 0.9, df['DiabetesPedigreeFunction'].max() * 1.1 + 0.01, 0.01)
skin_uni = np.arange(df['SkinThickness'].min() * 0.9, df['SkinThickness'].max() * 1.1 + 1, 1)
insulin_uni = np.arange(df['Insulin'].min() * 0.9, df['Insulin'].max() * 1.1 + 1, 1)
risk_uni = np.arange(0, 101, 1)

# --- Define Antecedents and Consequent ---
glucose = ctrl.Antecedent(glucose_uni, 'glucose')
bmi = ctrl.Antecedent(bmi_uni, 'bmi')
age = ctrl.Antecedent(age_uni, 'age')
blood_pressure = ctrl.Antecedent(bp_uni, 'blood_pressure')
pregnancies = ctrl.Antecedent(preg_uni, 'pregnancies')
dpf = ctrl.Antecedent(dpf_uni, 'diabetes_pedigree_function')
skin_thickness = ctrl.Antecedent(skin_uni, 'skin_thickness')
insulin = ctrl.Antecedent(insulin_uni, 'insulin')
diabetes_risk = ctrl.Consequent(risk_uni, 'diabetes_risk')

# --- Define Membership Function Assignment Function ---
def assign_fcm_mfs(antecedent_obj, mf_params, n_clusters, default_names):
    centers = mf_params['centers']
    sigmas = mf_params['sigmas']

    if len(centers) != n_clusters:
        st.warning(f"{antecedent_obj.label}: Number of centers ({len(centers)}) ≠ n_clusters ({n_clusters}). Using available centers.")

    for i in range(n_clusters):
        center = centers[i]
        sigma = sigmas[i]
        mf_name = default_names[i] if i < len(default_names) else f'fcm_cluster_{i}'
        antecedent_obj[mf_name] = fuzz.gaussmf(antecedent_obj.universe, center, sigma)

    st.success(f"{antecedent_obj.label}: Assigned {n_clusters} Gaussian MFs.")

# --- Apply FCM-derived MFs to All Antecedents ---
with st.expander("Assign Membership Functions using FCM"):
    assign_fcm_mfs(glucose, fcm_mf_params['glucose'], n_clusters_glucose,
                   ['very_low_gl', 'low_gl', 'normal_gl', 'high_gl'])
    assign_fcm_mfs(bmi, fcm_mf_params['bmi'], n_clusters_bmi,
                   ['underweight_bmi', 'normal_bmi', 'overweight_bmi', 'obese_bmi'])
    assign_fcm_mfs(age, fcm_mf_params['age'], n_clusters_age,
                   ['young_age', 'middle_aged_age', 'senior_age', 'elderly_age'])
    assign_fcm_mfs(blood_pressure, fcm_mf_params['blood_pressure'], n_clusters_blood_pressure,
                   ['very_low_bp', 'low_bp', 'normal_bp', 'elevated_bp', 'high_bp'])
    assign_fcm_mfs(pregnancies, fcm_mf_params['pregnancies'], n_clusters_pregnancies,
                   ['zero_preg', 'low_preg', 'medium_preg', 'high_preg', 'very_high_preg'])
    assign_fcm_mfs(dpf, fcm_mf_params['diabetes_pedigree_function'], n_clusters_dpf,
                   ['very_low_dpf', 'low_dpf', 'medium_dpf', 'high_dpf'])
    assign_fcm_mfs(skin_thickness, fcm_mf_params['skin_thickness'], n_clusters_skin_thickness,
                   ['very_thin_skin', 'thin_skin', 'normal_skin', 'thick_skin', 'very_thick_skin'])
    assign_fcm_mfs(insulin, fcm_mf_params['insulin'], n_clusters_insulin,
                   ['very_low_insulin', 'low_insulin', 'normal_insulin', 'elevated_ins', 'very_high_ins'])



# --- IMPORTANT: COMMENTED OUT MANUAL MF DEFINITIONS ---
# The following lines were manually defining MFs, overwriting the FCM-derived ones.
# If you want to use FCM-derived MFs, keep these lines commented out.
# If you prefer manual MFs, uncomment them BUT then the FCM analysis in Cell 2
# and the assign_fcm_mfs function become less relevant for your fuzzy system's inputs.

# pregnancies['zero_preg'] = fuzz.trimf(pregnancies.universe, [-0.5, 0, 0.5]) # Centered at 0
# pregnancies['low_preg'] = fuzz.trimf(pregnancies.universe, [0, 2, 4])
# pregnancies['medium_preg'] = fuzz.trimf(pregnancies.universe, [3, 5, 7])
# pregnancies['high_preg'] = fuzz.trapmf(pregnancies.universe, [6, 9, 17, 17])

# glucose['low_gl'] = fuzz.trimf(glucose.universe, [50, 50, 75])
# glucose['normal_gl'] = fuzz.trimf(glucose.universe, [70, 90, 110])
# glucose['prediabetic_gl'] = fuzz.trimf(glucose.universe, [100, 120, 140])
# glucose['high_gl'] = fuzz.trapmf(glucose.universe, [130, 160, 200, 200])

# blood_pressure['low_bp'] = fuzz.trimf(blood_pressure.universe, [40, 40, 65])
# blood_pressure['normal_bp'] = fuzz.trimf(blood_pressure.universe, [60, 75, 90])
# blood_pressure['elevated_bp'] = fuzz.trimf(blood_pressure.universe, [85, 95, 105])
# blood_pressure['high_bp'] = fuzz.trapmf(blood_pressure.universe, [100, 120, 180, 180])

# skin_thickness['thin_skin'] = fuzz.trimf(skin_thickness.universe, [10, 10, 30])
# skin_thickness['normal_skin'] = fuzz.trimf(skin_thickness.universe, [20, 50, 80])
# skin_thickness['thick_skin'] = fuzz.trimf(skin_thickness.universe, [60, 100, 100]) # Or trapmf([60, 80, 100, 100])

# insulin['low_normal_ins'] = fuzz.trapmf(insulin.universe, [15, 15, 60, 100])
# insulin['high_normal_ins'] = fuzz.trimf(insulin.universe, [80, 150, 250])
# insulin['elevated_ins'] = fuzz.trimf(insulin.universe, [200, 400, 600])
# insulin['very_high_ins'] = fuzz.trapmf(insulin.universe, [550, 700, 850, 850])

# bmi['underweight_bmi'] = fuzz.trapmf(bmi.universe, [15, 15, 17, 18.5])
# bmi['normal_bmi'] = fuzz.trimf(bmi.universe, [18, 21.5, 25])
# bmi['overweight_bmi'] = fuzz.trimf(bmi.universe, [24, 27.5, 30])
# bmi['obese_bmi'] = fuzz.trimf(bmi.universe, [29, 35, 40])
# bmi['severely_obese_bmi'] = fuzz.trapmf(bmi.universe, [38, 45, 60, 60])

# dpf['low_dpf'] = fuzz.trimf(dpf.universe, [0.05, 0.05, 0.4])
# dpf['medium_dpf'] = fuzz.trimf(dpf.universe, [0.3, 0.7, 1.1])
# dpf['high_dpf'] = fuzz.trapmf(dpf.universe, [0.9, 1.5, 2.5, 2.5])

# age['young_age'] = fuzz.trimf(age.universe, [20, 20, 35])
# age['middle_aged_age'] = fuzz.trimf(age.universe, [30, 45, 60])
# age['senior_age'] = fuzz.trapmf(age.universe, [55, 65, 85, 85])


# Output variable (Consequent) membership functions remain manually defined
# These are fine as they define the output risk levels.
diabetes_risk['low_risk'] = fuzz.trimf(diabetes_risk.universe, [0, 25, 50])
diabetes_risk['medium_risk'] = fuzz.trimf(diabetes_risk.universe, [25, 50, 75])
diabetes_risk['high_risk'] = fuzz.trimf(diabetes_risk.universe, [50, 75, 100])

#cell5
# --- 4. Define Fuzzy Rules ---

# IMPORTANT: These rules now assume that your FCM process
# will generate membership functions with names like 'low_gl', 'normal_gl', 'high_gl', etc.
# based on the `names` list provided in `assign_fcm_mfs` in Cell 4.
# You MUST verify that the names used here match the names actually assigned
# to your FCM-derived membership functions for the chosen n_clusters.
# If you chose more than 3 clusters for a feature, you'll need to adapt these rules
# to use the new names (e.g., 'very_high_gl', 'obese_bmi', etc.)

# Rules for High Risk
# Aim for 6 rules focusing on strong indicators and critical combinations
rule_high_1 = ctrl.Rule(glucose['high_gl'], diabetes_risk['high_risk'], label='High Glucose -> High Risk')
rule_high_2 = ctrl.Rule(bmi['obese_bmi'], diabetes_risk['high_risk'], label='Obese BMI -> High Risk')
rule_high_3 = ctrl.Rule(insulin['very_high_ins'], diabetes_risk['high_risk'], label='Very High Insulin -> High Risk')
rule_high_4 = ctrl.Rule(dpf['high_dpf'] & (glucose['high_gl'] | insulin['elevated_ins']), diabetes_risk['high_risk'], label='High DPF & (High Glucose OR Elevated Insulin) -> High Risk')
rule_high_5 = ctrl.Rule(age['elderly_age'] & (glucose['high_gl'] | bmi['obese_bmi']), diabetes_risk['high_risk'], label='Elderly Age & (High Glucose OR Obese BMI) -> High Risk')
rule_high_6 = ctrl.Rule(pregnancies['very_high_preg'] & glucose['high_gl'], diabetes_risk['high_risk'], label='Very High Pregnancies & High Glucose -> High Risk')

# Rules for Medium Risk
# Aim for 6 rules focusing on borderline or moderate risk
rule_medium_1 = ctrl.Rule(glucose['normal_gl'] & insulin['elevated_ins'], diabetes_risk['medium_risk'], label='Normal Glucose & Elevated Insulin -> Medium Risk')
rule_medium_2 = ctrl.Rule(bmi['overweight_bmi'] & (age['middle_aged_age'] | age['senior_age']), diabetes_risk['medium_risk'], label='Overweight BMI & Middle/Senior Age -> Medium Risk')
rule_medium_3 = ctrl.Rule(blood_pressure['elevated_bp'] & glucose['normal_gl'], diabetes_risk['medium_risk'], label='Elevated BP & Normal Glucose -> Medium Risk')
rule_medium_4 = ctrl.Rule(dpf['medium_dpf'] & (age['middle_aged_age'] | age['senior_age']), diabetes_risk['medium_risk'], label='Medium DPF & Middle/Senior Age -> Medium Risk')
rule_medium_5 = ctrl.Rule(pregnancies['high_preg'] & bmi['overweight_bmi'], diabetes_risk['medium_risk'], label='High Pregnancies & Overweight BMI -> Medium Risk')
rule_medium_6 = ctrl.Rule(glucose['normal_gl'] & bmi['obese_bmi'], diabetes_risk['medium_risk'], label='Normal Glucose & Obese BMI -> Medium Risk')

# Rules for Low Risk
# Aim for 6 rules focusing on combinations indicating low risk
rule_low_1 = ctrl.Rule(glucose['normal_gl'] & bmi['normal_bmi'] & age['young_age'], diabetes_risk['low_risk'], label='Normal Glucose & Normal BMI & Young Age -> Low Risk')
rule_low_2 = ctrl.Rule(glucose['low_gl'], diabetes_risk['low_risk'], label='Low Glucose -> Low Risk')
rule_low_3 = ctrl.Rule(bmi['normal_bmi'] & blood_pressure['normal_bp'], diabetes_risk['low_risk'], label='Normal BMI & Normal BP -> Low Risk')
rule_low_4 = ctrl.Rule(dpf['very_low_dpf'] & (age['young_age'] | age['middle_aged_age']), diabetes_risk['low_risk'], label='Very Low DPF & Young/Middle Age -> Low Risk')
rule_low_5 = ctrl.Rule(pregnancies['zero_preg'] & glucose['normal_gl'] & bmi['normal_bmi'], diabetes_risk['low_risk'], label='Zero Pregnancies & Normal Glucose & Normal BMI -> Low Risk')
rule_low_6 = ctrl.Rule(insulin['normal_insulin'] & skin_thickness['normal_skin'], diabetes_risk['low_risk'], label='Normal Insulin & Normal Skin -> Low Risk')


# Collect all rules
all_rules = [
    rule_high_1, rule_high_2, rule_high_3, rule_high_4, rule_high_5, rule_high_6,
    rule_medium_1, rule_medium_2, rule_medium_3, rule_medium_4, rule_medium_5, rule_medium_6,
    rule_low_1, rule_low_2, rule_low_3, rule_low_4, rule_low_5, rule_low_6
]

#cell6
# --- 5. Create Control System and Simulation ---
risk_ctrl_system = ctrl.ControlSystem(all_rules)
risk_simulation = ctrl.ControlSystemSimulation(risk_ctrl_system)

#cell7
# --- 6. Simulate for a New Patient (Example) ---
# This cell is for a single example. The full DataFrame processing is in Cell 8.
# You can uncomment and test individual cases here if needed.
# For now, keeping it minimal as the full processing is handled below.
# results = []
# for i in range(len(df)):
#     try:
#         risk_simulation.input['glucose'] = df['Glucose'].iloc[i]
#         risk_simulation.input['bmi'] = df['BMI'].iloc[i]
#         risk_simulation.input['age'] = df['Age'].iloc[i]
#         risk_simulation.input['blood_pressure'] = df['BloodPressure'].iloc[i]
#         risk_simulation.input['pregnancies'] = df['Pregnancies'].iloc[i]
#         risk_simulation.input['diabetes_pedigree_function'] = df['DiabetesPedigreeFunction'].iloc[i]
#         risk_simulation.input['skin_thickness'] = df['SkinThickness'].iloc[i]
#         risk_simulation.input['insulin'] = df['Insulin'].iloc[i]
#         risk_simulation.compute()
#         results.append(risk_simulation.output['diabetes_risk'])
#     except Exception as e:
#         print(f"Error processing row {i} (after preprocessing): {e}")
#         results.append(np.nan)

# df['predicted_fuzzy_risk'] = results

#cell 8
# --- Classification Metrics (Streamlit Version) ---
# Calculate optimal threshold from F1-score
f1_scores = 2 * (precision * recall) / (precision + recall)
f1_scores[np.isnan(f1_scores)] = 0  # Handle division by zero if it occurs
optimal_f1_idx = np.argmax(f1_scores)
optimal_threshold = thresholds[optimal_f1_idx]
optimal_threshold = round(optimal_threshold, 2)
st.subheader(f"📊 Classification Metrics (Optimal Threshold = {optimal_threshold}%)")

# Display numerical metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Accuracy", f"{accuracy:.4f}")
col2.metric("Precision", f"{precision:.4f}")
col3.metric("Recall", f"{recall:.4f}")
col4.metric("F1-Score", f"{f1:.4f}")

# Display the optimal threshold
st.info(f"**Optimal Threshold selected by maximizing F1-Score for Outcome=1:** `{optimal_threshold:.2f}`")

# Confusion Matrix Visualization
st.subheader("🧮 Confusion Matrix")
fig, ax = plt.subplots()
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, ax=ax)
ax.set_xlabel('Predicted')
ax.set_ylabel('Actual')
ax.set_title('Confusion Matrix')
st.pyplot(fig)

# Interpretation of Confusion Matrix:
# [[TN, FP],
#  [FN, TP]]
# TN: True Negatives (Actual 0, Predicted 0) - Correctly identified as non-diabetic
# FP: False Positives (Actual 0, Predicted 1) - Incorrectly identified as diabetic (Type I error)
# FN: False Negatives (Actual 1, Predicted 0) - Incorrectly identified as non-diabetic (Type II error)
# TP: True Positives (Actual 1, Predicted 1) - Correctly identified as diabetic

# Classification Report (provides all the above in a neat format)
st.subheader("📄 Classification Report")
report = classification_report(y_true, y_pred, target_names=['No Diabetes (0)', 'Diabetes (1)'])
st.text(report)

# ROC AUC Score
# ROC AUC uses the probability scores, not the binary predictions
# Higher is better, 0.5 is random, 1.0 is perfect
roc_auc = roc_auc_score(y_true, y_scores)
st.metric("ROC AUC Score", f"{roc_auc:.4f}")

# --- 8. Visualize ROC Curve ---
st.subheader("📈 ROC Curve")
fig_roc, ax_roc = plt.subplots(figsize=(8, 6))
ax_roc.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
ax_roc.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random (AUC = 0.5)')
ax_roc.scatter(fpr[optimal_f1_idx], tpr[optimal_f1_idx], color='red', s=100, label=f'Optimal Threshold ({optimal_threshold})')
ax_roc.set(xlabel='False Positive Rate', ylabel='True Positive Rate', title='ROC Curve')
ax_roc.legend(loc='lower right')
ax_roc.grid(True)
st.pyplot(fig_roc)

# --- Optional: Visualize Predicted Risk Distribution ---
st.subheader("🔍 Predicted Fuzzy Risk Distribution")
fig_dist, ax_dist = plt.subplots(figsize=(10, 6))
sns.histplot(df_eval[df_eval['Outcome'] == 0]['predicted_fuzzy_risk'], color='blue', label='No Diabetes', kde=True, stat='density', alpha=0.6, bins=30, ax=ax_dist)
sns.histplot(df_eval[df_eval['Outcome'] == 1]['predicted_fuzzy_risk'], color='red', label='Diabetes', kde=True, stat='density', alpha=0.6, bins=30, ax=ax_dist)
ax_dist.axvline(optimal_threshold, color='green', linestyle='--', label=f'Optimal Threshold ({optimal_threshold})')
ax_dist.set(xlabel='Predicted Risk (%)', ylabel='Density', title='Fuzzy Risk Distribution by Outcome')
ax_dist.legend()
ax_dist.grid(axis='y', alpha=0.75)
st.pyplot(fig_dist)

#cell10
# --- 8. Visualize FCM-derived Membership Functions (NEW SECTION) ---
# This code should be placed after your FCM calculations and after
# you've assigned the FCM-derived MFs to your Antecedent objects.

# --- FCM-Derived Membership Function Visualization ---
st.subheader("📊 FCM-Derived Membership Functions")

# List of your antecedent objects
antecedents_to_view = [
    glucose,
    bmi,
    age,
    blood_pressure,
    pregnancies,
    dpf,
    skin_thickness,
    insulin
]

# Iterate through each antecedent and display its membership functions
for antecedent in antecedents_to_view:
    st.markdown(f"**{antecedent.label}**")
    fig, ax = plt.subplots()
    antecedent.view(ax=ax)
    st.pyplot(fig)

# --- FCM Parameters Review ---
st.subheader("🔧 FCM Parameters Summary")
for key, params in fcm_mf_params.items():
    st.markdown(f"**{key.capitalize()}** (FPC: {params['fpc']:.4f})")
    st.text(f"Centers: {np.array2string(params['centers'], precision=2, floatmode='fixed')}")
    st.text(f"Sigmas:  {np.array2string(np.array(params['sigmas']), precision=2, floatmode='fixed')}")

# --- Risk Categorization using K-Means ---
st.subheader("📉 K-Means Risk Categorization")

st.markdown(f"""
**Learned Thresholds:**  
- Low Risk: < {low_medium_threshold}%  
- Medium Risk: {low_medium_threshold}% - {medium_high_threshold}%  
- High Risk: ≥ {medium_high_threshold}%
""")

# Patient count
risk_category_counts = df_eval['risk_category'].value_counts().reindex(risk_order[:-1])
st.markdown("**Patient Counts by Risk Category:**")
st.dataframe(risk_category_counts.rename("Count"))

# Percentage per category
total_patients = len(df_eval)
st.markdown("**Percentage of Patients per Category:**")
for category in risk_order[:-1]:
    count = risk_category_counts.get(category, 0)
    pct = (count / total_patients) * 100 if total_patients > 0 else 0
    st.markdown(f"- {category}: {pct:.2f}%")

# Outcome Distribution
st.markdown("**Outcome Distribution by Risk Category:**")
risk_outcome_crosstab = pd.crosstab(df_eval['risk_category'], df_eval['Outcome'], margins=True)
risk_outcome_crosstab = risk_outcome_crosstab.reindex(risk_order)
risk_outcome_crosstab.columns = ['Actual No Diabetes', 'Actual Diabetes', 'Total']
st.dataframe(risk_outcome_crosstab)

# Accuracy/Purity by Category
st.markdown("**Category Purity (Accuracy within each Risk Group):**")
for category in risk_order[:-1]:
    row = risk_outcome_crosstab.loc[category]
    total_in_cat = row['Total']
    if total_in_cat > 0:
        pct_no_diabetes = (row['Actual No Diabetes'] / total_in_cat) * 100
        pct_diabetes = (row['Actual Diabetes'] / total_in_cat) * 100
        st.markdown(f"- **{category}**")
        st.markdown(f"  - Actual No Diabetes: {pct_no_diabetes:.2f}%")
        st.markdown(f"  - Actual Diabetes: {pct_diabetes:.2f}%")
    else:
        st.markdown(f"- **{category}**: No patients in this category.")

# Visualize the three risk categories on the distribution plot
st.subheader("📈 Distribution of Predicted Fuzzy Risk")

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Plot histograms for each class (0 = No Diabetes, 1 = Diabetes)
sns.histplot(df_eval[df_eval['Outcome'] == 0]['predicted_fuzzy_risk'],
             color='blue', label='_nolegend_', kde=True, stat='density', alpha=0.6, bins=30, ax=ax)

sns.histplot(df_eval[df_eval['Outcome'] == 1]['predicted_fuzzy_risk'],
             color='red', label='_nolegend_', kde=True, stat='density', alpha=0.6, bins=30, ax=ax)

# Plot threshold lines
ax.axvline(low_medium_threshold, color='green', linestyle='--',
           label=f'Low/Medium Threshold ({low_medium_threshold}%)')

ax.axvline(medium_high_threshold, color='purple', linestyle=':',
           label=f'Medium/High Threshold ({medium_high_threshold}%)')

# Title and labels
ax.set_title('Distribution of Predicted Fuzzy Risk by Actual Outcome')
ax.set_xlabel('Predicted Fuzzy Risk (%)')
ax.set_ylabel('Density')
ax.grid(axis='y', alpha=0.75)

# Custom legend
legend_handles = [
    Patch(facecolor='blue', edgecolor='black', alpha=0.6, label='Actual No Diabetes'),
    Patch(facecolor='red', edgecolor='black', alpha=0.6, label='Actual Diabetes'),
    plt.Line2D([0], [0], color='green', linestyle='--', lw=2, label=f'Low/Medium Threshold ({low_medium_threshold}%)'),
    plt.Line2D([0], [0], color='purple', linestyle=':', lw=2, label=f'Medium/High Threshold ({medium_high_threshold}%)')
]
ax.legend(handles=legend_handles, loc='upper right')

st.pyplot(fig)

# Display thresholds
st.markdown(f"""
### 🧪 K-Means Risk Thresholds
- **Low Risk**: < {low_medium_threshold}%
- **Medium Risk**: {low_medium_threshold}% – {medium_high_threshold}%
- **High Risk**: ≥ {medium_high_threshold}%
""")

# Visualize the three risk categories on the distribution plot
st.subheader("📊 Distribution of Predicted Fuzzy Risk by Actual Outcome")

# Create the figure
fig, ax = plt.subplots(figsize=(12, 7))

# Plot histograms by outcome
sns.histplot(df_eval[df_eval['Outcome'] == 0]['predicted_fuzzy_risk'],
             color='blue', label='_nolegend_', kde=True, stat='density', alpha=0.6, bins=30, ax=ax)

sns.histplot(df_eval[df_eval['Outcome'] == 1]['predicted_fuzzy_risk'],
             color='red', label='_nolegend_', kde=True, stat='density', alpha=0.6, bins=30, ax=ax)

# Add vertical threshold lines
ax.axvline(low_medium_threshold, color='green', linestyle='--',
           label=f'Low/Medium Risk Threshold ({low_medium_threshold}%)')

ax.axvline(medium_high_threshold, color='purple', linestyle=':',
           label=f'Medium/High Risk Threshold ({medium_high_threshold}%)')

# Add title and labels
ax.set_title('Distribution of Predicted Fuzzy Risk (by Actual Outcome and Risk Categories)')
ax.set_xlabel('Predicted Fuzzy Risk (%)')
ax.set_ylabel('Density')
ax.grid(axis='y', alpha=0.75)

# Custom legend
custom_legend_handles = [
    Patch(facecolor='blue', edgecolor='black', alpha=0.6, label='Actual No Diabetes'),
    Patch(facecolor='red', edgecolor='black', alpha=0.6, label='Actual Diabetes'),
    plt.Line2D([0], [0], color='green', linestyle='--', lw=2, label=f'Low/Medium Risk Threshold ({low_medium_threshold}%)'),
    plt.Line2D([0], [0], color='purple', linestyle=':', lw=2, label=f'Medium/High Risk Threshold ({medium_high_threshold}%)')
]

ax.legend(handles=custom_legend_handles, loc='upper right')

# Render the figure in Streamlit
st.pyplot(fig)
