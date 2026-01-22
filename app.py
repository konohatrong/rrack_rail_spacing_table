import streamlit as st
import pandas as pd
from wind_load import WindLoadCalculator

# --- INIT CALCULATOR ---
calculator = WindLoadCalculator()

st.title("AS/NZS 1170.2 Wind Load Calculator")

# --- 1. BASIC PARAMETERS (Updated Logic) ---
st.header("1. Design Parameters")
col1, col2 = st.columns(2)

with col1:
    region = st.selectbox("Region", ["A", "B", "C", "D", "NZ_1_2", "NZ_3", "NZ_4"], index=0)
    imp_level = st.selectbox("Importance Level", [1, 2, 3, 4], index=1)

with col2:
    design_life = st.selectbox("Design Life (years)", [5, 25, 50, 100], index=2)
    # คำนวณ Return Period อัตโนมัติ
    ret_period = calculator.get_return_period(imp_level, design_life)
    st.info(f"Calculated Return Period (R): **{ret_period} years**")

# Get Regional Wind Speed
V_R = calculator.get_regional_wind_speed(region, ret_period)
st.metric("Regional Wind Speed (VR)", f"{V_R:.2f} m/s")

# --- 2. SITE CONDITIONS (Restored!) ---
st.header("2. Site Conditions (Multipliers)")
col3, col4 = st.columns(2)

with col3:
    terrain_cat = st.selectbox("Terrain Category", [1, 2, 3, 4], index=1, 
                               help="1: Very Exposed, 2: Open, 3: Suburban, 4: Urban/Obstructed")
    height = st.number_input("Structure Height (z) [m]", min_value=1.0, value=10.0, step=0.5)

with col4:
    # Multipliers (Ms, Mt, Md)
    Ms = st.number_input("Shielding Multiplier (Ms)", min_value=0.0, value=1.0, step=0.05, help="Standard = 1.0")
    Mt = st.number_input("Topographic Multiplier (Mt)", min_value=1.0, value=1.0, step=0.05, help="Standard flat = 1.0")
    Md = st.number_input("Direction Multiplier (Md)", min_value=0.8, value=1.0, step=0.05, help="Standard = 1.0 (Omni-directional)")

# Calculate Mz,cat
Mz_cat = calculator.get_terrain_multiplier(height, terrain_cat)
st.info(f"Terrain/Height Multiplier (Mz,cat): **{Mz_cat:.2f}**")

# --- 3. FINAL CALCULATION ---
st.header("3. Site Wind Speed (V_sit)")

V_sit = calculator.calculate_site_wind_speed(V_R, Mz_cat, Ms, Mt, Md)
design_pressure = calculator.calculate_design_pressure(V_sit)

c1, c2 = st.columns(2)
c1.metric("Site Wind Speed (V_sit,β)", f"{V_sit:.2f} m/s")
c2.metric("Design Pressure (q*)", f"{design_pressure:.3f} kPa")

# --- OPTIONAL: Reference Table ---
with st.expander("Show Wind Speed Reference Table (Updated)"):
    st.write("Regional Wind Speeds (V_R) by Return Period:")
    st.dataframe(pd.DataFrame(calculator.wind_data))
