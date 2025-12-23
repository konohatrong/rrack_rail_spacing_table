import streamlit as st
import structural
import wind_load
import report
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Solar Rail Design (AS/NZS 1170.2)", layout="wide")

st.markdown("""
<style>
    .reportview-container .main .block-container{ font-family: 'Tahoma', sans-serif; }
    h1, h2, h3 { font-family: 'Tahoma', sans-serif; }
    .metric-box { border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Solar Rail Design & Analysis (AS/NZS 1170.2:2021)")
st.markdown("**Structural Engineer & Software Developer:** Aluminum Rail Analysis for Solar PV")

# ==========================================
# SIDEBAR INPUTS
# ==========================================

# --- 1. Site & Wind Data (UPDATED: Probabilistic Vr) ---
st.sidebar.header("1. Wind Parameters (AS/NZS 1170.0/1170.2)")

st.sidebar.markdown("**Step A: Importance & Probability**")
region = st.sidebar.selectbox("Wind Region", ["A", "B", "C", "D"], index=0, help="A=Normal, B=Intermediate, C=Cyclonic, D=Severe")
imp_level = st.sidebar.selectbox("Importance Level (IL)", [1, 2, 3, 4], index=1, help="2=Normal Structures (1/500)")
design_life = st.sidebar.selectbox("Design Working Life", [25, 50, 100], index=1)

# Calculate Vr
ret_period = wind_load.get_return_period(imp_level, design_life)
vr = wind_load.get_vr_from_ari(region, ret_period)

st.sidebar.info(f"**Return Period (R):** {ret_period} years\n\n**Regional Speed ($V_R$):** {vr} m/s")

st.sidebar.markdown("**Step B: Site Multipliers**")
md = st.sidebar.number_input("Direction Multiplier, Md", value=1.0, min_value=0.8, max_value=1.0)
tc = st.sidebar.selectbox("Terrain Category (TC)", [1, 2, 2.5, 3, 4], index=3)
b_height = st.sidebar.number_input("Building/Roof Height, z (m)", value=6.0, min_value=1.0)
ms = st.sidebar.number_input("Shielding Multiplier, Ms", value=1.0)
mt = st.sidebar.number_input("Topographic Multiplier, Mt", value=1.0)

mz_cat = wind_load.get_mz_cat(b_height, tc)
v_des = wind_load.calculate_v_des_detailed(vr, md, mz_cat, ms, mt)
st.sidebar.success(f"**Design Wind Speed ($V_{{des}}$) = {v_des:.2f} m/s**")

# --- 2. Building Geometry ---
st.sidebar.header("2. Building Geometry")
b_width = st.sidebar.number_input("Building Width, b (m)", value=20.0)
b_depth = st.sidebar.number_input("Building Depth, d (m)", value=15.0)
roof_type = st.sidebar.radio("Roof Shape", ["Monoslope", "Gable Roof"])
roof_angle = st.sidebar.number_input("Roof Angle (Degrees)", min_value=0.0, max_value=60.0, value=10.0, step=0.5)

# --- 3. Panel & Rail Data ---
st.sidebar.header("3. Panel & Rail Configuration")
panel_w = st.sidebar.number_input("Panel Width (m)", value=1.134)
panel_d = st.sidebar.number_input("Panel Depth (m)", value=2.279)
rail_orient = st.sidebar.selectbox("Panel Side Parallel to Rail Span", ["Panel Width", "Panel Depth"])
orient_key = 'width' if rail_orient == "Panel Width" else 'depth'

st.sidebar.subheader("Coefficients")
ka = st.sidebar.number_input("Area Reduction Factor (Ka)", value=1.0)

# --- 4. Structural Test Data ---
st.sidebar.header("4. Structural Test (ASTM E290)")
breaking_load = st.sidebar.number_input("Breaking Load (kN)", value=5.0)
test_span = st.sidebar.number_input("Test Span (m)", value=1.0)
safety_factor = st.sidebar.number_input("Safety Factor (Mn)", value=1.1)
num_spans = st.sidebar.slider("Number of Continuous Spans", 1, 5, 2)

# ==========================================
# VISUALIZATION FUNCTIONS
# ==========================================
def plot_building_diagram(b, d, r_type):
    fig, ax = plt.subplots(figsize=(5, 3))
    rect = patches.Rectangle((0, 0), b, d, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)
    ax.text(b/2, -d*0.15, f"Width b = {b}m", ha='center', color='blue', fontweight='bold', family='sans-serif')
    ax.text(-b*0.15, d/2, f"Depth d = {d}m", ha='right', va='center', rotation=90, color='green', fontweight='bold', family='sans-serif')
    ax.arrow(b/2, d+d*0.3, 0, -d*0.2, head_width=b*0.05, head_length=d*0.05, fc='red', ec='red')
    ax.text(b/2, d+d*0.35, "Wind 0° (Normal)\n(Use h/d)", ha='center', color='red', fontsize=8, family='sans-serif')
    ax.arrow(-b*0.3, d/2, b*0.2, 0, head_width=d*0.05, head_length=b*0.05, fc='orange', ec='orange')
    ax.text(-b*0.35, d/2, "Wind 90° (Parallel)\n(Use h/b)", ha='center', va='center', rotation=90, color='orange', fontsize=8, family='sans-serif')
    if "Gable" in r_type:
        ax.plot([0, b], [d/2, d/2], color='purple', linestyle='-.', linewidth=2.5, label='Ridge Line')
        ax.text(b*0.02, d/2 + d*0.03, "RIDGE LINE", color='purple', fontsize=9, fontweight='bold', ha='left')
    ax.set_xlim(-b*0.5, b*1.5)
    ax.set_ylim(-d*0.3, d*1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

# ==========================================
# PLOTTING DIAGRAMS (UPDATED: ANNOTATIONS)
# ==========================================
def plot_fem_diagrams_annotated(analysis_res, zone_name):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    
    # --- SFD ---
    x_vals = analysis_res['x']
    shear_vals = analysis_res['shear']
    
    ax1.plot(x_vals, shear_vals, 'b-', label='Shear')
    ax1.fill_between(x_vals, shear_vals, color='blue', alpha=0.1)
    ax1.set_ylabel("Shear Force (kN)")
    ax1.set_title(f"Shear Force Diagram (SFD) - {zone_name}")
    ax1.grid(True, linestyle=':')
    ax1.axhline(0, color='black', linewidth=0.8)
    
    # Annotate Max Shear
    v_abs = np.abs(shear_vals)
    max_v_idx = np.argmax(v_abs)
    max_v_val = shear_vals[max_v_idx]
    max_v_x = x_vals[max_v_idx]
    
    ax1.plot(max_v_x, max_v_val, 'ro') # Red dot
    ax1.annotate(f"V* = {abs(max_v_val):.2f} kN", 
                 xy=(max_v_x, max_v_val), 
                 xytext=(10, 10 if max_v_val > 0 else -15),
                 textcoords="offset points", 
                 color='red', fontweight='bold',
                 arrowprops=dict(arrowstyle="->", color='red'))

    # --- BMD ---
    moment_vals = analysis_res['moment']
    
    ax2.plot(x_vals, moment_vals, 'r-', label='Moment')
    ax2.fill_between(x_vals, moment_vals, color='red', alpha=0.1)
    ax2.set_ylabel("Bending Moment (kNm)")
    ax2.set_title(f"Bending Moment Diagram (BMD) - {zone_name}")
    ax2.set_xlabel("Span Length (m)")
    ax2.grid(True, linestyle=':')
    ax2.axhline(0, color='black', linewidth=0.8)
    
    # Annotate Max Moment
    m_abs = np.abs(moment_vals)
    max_m_idx = np.argmax(m_abs)
    max_m_val = moment_vals[max_m_idx]
    max_m_x = x_vals[max_m_idx]
    
    ax2.plot(max_m_x, max_m_val, 'bo') # Blue dot
    ax2.annotate(f"M* = {abs(max_m_val):.2f} kNm", 
                 xy=(max_m_x, max_m_val), 
                 xytext=(10, 10 if max_m_val > 0 else -15),
                 textcoords="offset points", 
                 color='blue', fontweight='bold',
                 arrowprops=dict(arrowstyle="->", color='blue'))
    
    plt.tight_layout()
    return fig

# ==========================================
# ASCII ART
# ==========================================
def get_ascii_ridge_diagram(b, d, r_type):
    if "Gable" in r_type:
        return f"""
       Wind 0 deg (Normal)
             |
             v
      +---------------------+
      |      ROOF A         |
      | - - RIDGE LINE - - -| ---> Wind 90 deg
      |      ROOF B         |
      +---------------------+
        """
    else: 
        return f"""
       Wind 0 deg
             |
             v
      +---------------------+
      |    MONOSLOPE        |
      |                     |
      +---------------------+ ---> Wind 90 deg
        """

def get_ascii_art(zone_code):
    if zone_code == "RA1": return "[ RA 1: GENERAL AREA ]"
    elif zone_code == "RA2": return "[ RA 2: EDGES / RIDGE ]"
    elif zone_code == "RA3": return "[ RA 3: CORNERS ]"
    elif zone_code == "RA4": return "[ RA 4: HIGH SUCTION ]"
    return ""

# ==========================================
# MAIN LOGIC
# ==========================================
if st.button("🚀 Run Analysis for All Zones"):
    Mn = structural.calculate_Mn(breaking_load, test_span, safety_factor)
    trib_width = wind_load.calculate_tributary_width(panel_w, panel_d, orient_key)
    
    # 1. Wind Analysis
    ratio_0 = b_height / b_depth
    res_0 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, ratio_0)
    ratio_90 = b_height / b_width
    res_90 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, ratio_90)
    
    if res_0['cpe'] < res_90['cpe']:
        base_cpe, governing_case = res_0['cpe'], f"Wind 0° (Normal) | h/d={ratio_0:.2f}"
    else:
        base_cpe, governing_case = res_90['cpe'], f"Wind 90° (Side) | h/b={ratio_90:.2f}"

    # 2. Iterate Zones
    zones = [
        {"code": "RA1", "desc": "General Area", "kl": 1.0},
        {"code": "RA2", "desc": "Edges / Ridge", "kl": 1.5},
        {"code": "RA3", "desc": "Corners", "kl": 2.0},
        {"code": "RA4", "desc": "High Suction", "kl": 3.0},
    ]
    
    results_list = []
    worst_case_res = None
    max_pressure_found = -1.0
    
    for z in zones:
        p_z = wind_load.calculate_wind_pressure(v_des, base_cpe, Ka=ka, Kl=z['kl'])
        w_z = p_z * trib_width
        span_z, fem_res_z = structural.optimize_span(Mn, w_z, num_spans, max_span=4.0)
        max_reaction_z = np.max(np.abs(fem_res_z['reactions']))
        max_moment_z = fem_res_z['max_moment']
        
        results_list.append({
            "Zone": z['code'],
            "Description": z['desc'],
            "Kl": z['kl'],
            "Pressure (kPa)": p_z,
            "Line Load (kN/m)": w_z,
            "Max Span (m)": span_z,
            "Reaction (kN)": max_reaction_z,
            "M* (kNm)": max_moment_z
        })
        
        if p_z > max_pressure_found:
            max_pressure_found = p_z
            worst_case_res = {
                'zone': z['code'],
                'pressure': p_z,
                'span': span_z,
                'fem': fem_res_z,
                'load': w_z,
                'moment': max_moment_z,
                'reaction': max_reaction_z
            }

    # ==========================
    # DISPLAY RESULTS UI
    # ==========================
    st.divider()
    st.header("📊 Analysis Report Summary")
    
    # --- 1. ZONE ANALYSIS TABLE (MOVED UP) ---
    st.subheader("1. Zone Analysis Summary")
    df_res = pd.DataFrame(results_list)
    st.dataframe(
        df_res.style.format("{:.3f}", subset=["Pressure (kPa)", "Line Load (kN/m)", "Max Span (m)", "Reaction (kN)", "M* (kNm)"])
              .format("{:.1f}", subset=["Kl"])
              .highlight_max(subset=["Pressure (kPa)", "Reaction (kN)", "M* (kNm)"], color='#ffcccc')
              .highlight_min(subset=["Max Span (m)"], color='#ffcccc'),
        use_container_width=True
    )

    st.divider()

    # --- 2. INPUT & GEOMETRY (MOVED HERE) ---
    st.subheader("2. Input Summary & Geometry")
    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        st.write(f"- **Importance:** L{imp_level} (R={ret_period}y)")
        st.write(f"- **V_des:** {v_des:.2f} m/s (Region {region})")
        st.write(f"- **Geometry:** {b_width}x{b_depth}x{b_height}m")
        st.write(f"- **Governing Wind:** {governing_case}")
        st.write(f"- **Capacity (Mn):** {Mn:.3f} kNm")
    with col_in2:
        st.pyplot(plot_building_diagram(b_width, b_depth, roof_type))

    st.divider()

    # --- 3. CRITICAL CASE (MOVED DOWN) ---
    st.subheader(f"3. Critical Analysis Result (Worst Case: {worst_case_res['zone']})")
    
    col_crit1, col_crit2 = st.columns([1, 2])
    
    with col_crit1:
        st.markdown("### Design Values")
        st.metric("M* (Design Moment)", f"{worst_case_res['moment']:.3f} kNm")
        st.metric("V* (Max Shear)", f"{np.max(np.abs(worst_case_res['fem']['shear'])):.2f} kN")
        st.metric("Max Reaction", f"{worst_case_res['reaction']:.2f} kN")
        st.caption(f"Occurs in Zone **{worst_case_res['zone']}** at Span **{worst_case_res['span']:.2f} m**")
        
    with col_crit2:
        # Plot Annotated Diagrams
        st.pyplot(plot_fem_diagrams_annotated(worst_case_res['fem'], worst_case_res['zone']))

    # ==========================
    # REPORT GENERATION
    # ==========================
    st.divider()
    st.header("📄 Plain Text Report Preview")
    
    table_str = df_res.to_string(index=False, justify="right", float_format=lambda x: "{:.3f}".format(x))
    ridge_art = get_ascii_ridge_diagram(b_width, b_depth, roof_type)
    
    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================

[1] PROJECT INFORMATION & INPUTS
--------------------------------
   - Importance Level:           {imp_level} (Design Life: {design_life} yrs)
   - Annual Prob. Exceedance:    1/{ret_period}
   - Wind Region:                {region} (Vr = {vr} m/s)
   - Design Wind Speed (Vdes):   {v_des:.2f} m/s
   
   - Building Dimensions:        {b_width} m (W) x {b_depth} m (D) x {b_height} m (H)
   - Roof Configuration:         {roof_type}, Angle {roof_angle} deg
   
   - Rail Capacity (Mn):         {Mn:.3f} kNm 

[2] ANALYSIS RESULTS SUMMARY (ALL ZONES)
----------------------------------------
   - Governing Wind Direction:   {governing_case}
   - Tributary Width:            {trib_width:.3f} m

{table_str}

[3] CRITICAL DESIGN VALUES (WORST CASE SCENARIO)
------------------------------------------------
   The most critical condition occurs in Zone: {worst_case_res['zone']}
   
   >> M* (Design Moment):        {worst_case_res['moment']:.3f} kNm
   >> V* (Design Shear):         {np.max(np.abs(worst_case_res['fem']['shear'])):.2f} kN
   >> Max Allowable Span:        {worst_case_res['span']:.2f} m
   >> Max Uplift Reaction:       {worst_case_res['reaction']:.3f} kN

[4] VISUALIZATION GUIDE
-----------------------------------
   [4.1] BUILDING ORIENTATION
{ridge_art}

[5] LIMITATIONS & CONDITIONS OF USE
-----------------------------------
   1. Valid Design Scope:
      - Terrain Category: {tc}
      - Max Roof Height: {b_height} m
      - Design Wind Speed: {v_des:.2f} m/s
      
   2. Warnings:
      - Pull-out capacity of fasteners must be verified against Max Reaction.
================================================================================
Generated by Solar Rail App | Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
================================================================================
"""

    st.code(report_text, language='text')
    st.download_button(label="💾 Download Report (.txt)", data=report_text, file_name="Solar_Rail_Report.txt", mime="text/plain")
