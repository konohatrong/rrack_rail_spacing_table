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

# Custom CSS for cleaner layout
st.markdown("""
<style>
    .reportview-container .main .block-container{ font-family: 'Tahoma', sans-serif; }
    h1, h2, h3 { font-family: 'Tahoma', sans-serif; }
    div.stButton > button { width: 100%; font-weight: bold; }
    .metric-box { border: 1px solid #e6e6e6; padding: 10px; border-radius: 5px; background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Solar Rail Design & Analysis (AS/NZS 1170.2:2021)")
st.markdown("**Structural Engineer & Software Developer:** Aluminum Rail Analysis for Solar PV")

# ==========================================
# SIDEBAR INPUTS
# ==========================================

# --- 1. Site & Wind Data ---
st.sidebar.header("1. Wind Speed Parameters")
st.sidebar.markdown("Calculation of $V_{des} = V_R \cdot M_d (M_{z,cat} \cdot M_s \cdot M_t)$")

vr = st.sidebar.number_input("Regional Wind Speed, Vr (m/s)", value=45.0)
md = st.sidebar.number_input("Direction Multiplier, Md", value=1.0, min_value=0.8, max_value=1.0)

st.sidebar.subheader("Terrain & Height")
tc = st.sidebar.selectbox("Terrain Category (TC)", [1, 2, 2.5, 3, 4], index=3)
b_height = st.sidebar.number_input("Building/Roof Height, z (m)", value=6.0, min_value=1.0)
ms = st.sidebar.number_input("Shielding Multiplier, Ms", value=1.0)
mt = st.sidebar.number_input("Topographic Multiplier, Mt", value=1.0)

mz_cat = wind_load.get_mz_cat(b_height, tc)
v_des = wind_load.calculate_v_des_detailed(vr, md, mz_cat, ms, mt)
st.sidebar.success(f"**Design Wind Speed ($V_{{des}}$) = {v_des:.2f} m/s**")

# --- 2. Building Geometry ---
st.sidebar.header("2. Building Geometry")
b_width = st.sidebar.number_input("Building Width, b (m)", value=20.0, help="Width perpendicular to Ridge (typically)")
b_depth = st.sidebar.number_input("Building Depth, d (m)", value=15.0, help="Length parallel to Ridge")
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
    
    # 1. Draw Building Rect
    rect = patches.Rectangle((0, 0), b, d, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)
    
    # 2. Dimensions
    ax.text(b/2, -d*0.15, f"Width b = {b}m", ha='center', color='blue', fontweight='bold', family='sans-serif')
    ax.text(-b*0.15, d/2, f"Depth d = {d}m", ha='right', va='center', rotation=90, color='green', fontweight='bold', family='sans-serif')
    
    # 3. Wind Arrows
    ax.arrow(b/2, d+d*0.3, 0, -d*0.2, head_width=b*0.05, head_length=d*0.05, fc='red', ec='red')
    ax.text(b/2, d+d*0.35, "Wind 0° (Normal)\n(Use h/d)", ha='center', color='red', fontsize=8, family='sans-serif')
    
    ax.arrow(-b*0.3, d/2, b*0.2, 0, head_width=d*0.05, head_length=b*0.05, fc='orange', ec='orange')
    ax.text(-b*0.35, d/2, "Wind 90° (Parallel)\n(Use h/b)", ha='center', va='center', rotation=90, color='orange', fontsize=8, family='sans-serif')

    # 4. RIDGE LINE
    if "Gable" in r_type:
        ax.plot([0, b], [d/2, d/2], color='purple', linestyle='-.', linewidth=2.5, label='Ridge Line')
        ax.text(b*0.02, d/2 + d*0.03, "RIDGE LINE", color='purple', fontsize=9, fontweight='bold', ha='left')

    ax.set_xlim(-b*0.5, b*1.5)
    ax.set_ylim(-d*0.3, d*1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

# ==========================================
# ASCII ART LIBRARY
# ==========================================
def get_ascii_ridge_diagram(b, d, r_type):
    """Generates ASCII diagram for Building Orientation & Ridge Line"""
    if "Gable" in r_type:
        return f"""
       Wind 0 deg (Normal/Transverse)
                 |
                 v
      +-----------------------------+
      |                             |
      |          ROOF SIDE A        |
      |                             |
      | - - - - RIDGE LINE - - - - -| ---> Wind 90 deg (Parallel)
      |                             |
      |          ROOF SIDE B        |
      |                             |
      +-----------------------------+
      (Building: {b}m Width x {d}m Depth)
        """
    else: # Monoslope
        return f"""
       Wind 0 deg (Low to High or High to Low)
                 |
                 v
      +-----------------------------+
      |                             |
      |                             |
      |        MONOSLOPE ROOF       |
      |                             |
      |                             |
      |                             |
      +-----------------------------+ ---> Wind 90 deg
      (Building: {b}m Width x {d}m Depth)
        """

def get_ascii_art(zone_code):
    if zone_code == "RA1":
        return """
      +-----------------------------+
      |                             |
      |      [      RA 1      ]     |
      |      [  GENERAL AREA  ]     |
      |                             |
      +-----------------------------+
      (Central area of the roof)
        """
    elif zone_code == "RA2":
        return """
      +#############################+
      |#                           #|
      |#     [      RA 2      ]    #|
      |#     [  EDGES / RIDGE ]    #|
      |#                           #|
      +#############################+
      (Perimeter strips along edges & ridge)
        """
    elif zone_code == "RA3":
        return """
      ##---------------------------##
      ##                           ##
      |      [      RA 3      ]     |
      |      [     CORNERS    ]     |
      ##                           ##
      ##---------------------------##
      (Square areas at roof corners)
        """
    elif zone_code == "RA4":
        return """
      X-----------------------------X
                                     
             [      RA 4      ]      
             [  HIGH SUCTION  ]      
                                     
      X-----------------------------X
      (Small localized spots at tips)
        """
    return ""

# ==========================================
# MAIN LOGIC
# ==========================================
if st.button("🚀 Run Analysis for All Zones"):
    Mn = structural.calculate_Mn(breaking_load, test_span, safety_factor)
    trib_width = wind_load.calculate_tributary_width(panel_w, panel_d, orient_key)
    
    # --- 1. DETAILED WIND DIRECTION ANALYSIS (Restored) ---
    # Case 0 deg: Ratio = h / d
    ratio_0 = b_height / b_depth
    res_0 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, ratio_0)
    
    # Case 90 deg: Ratio = h / b
    ratio_90 = b_height / b_width
    res_90 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, ratio_90)
    
    # Determine Worst Case
    if res_0['cpe'] < res_90['cpe']: # More negative is worse
        base_cpe = res_0['cpe']
        governing_case = f"Wind 0° (Normal) | h/d={ratio_0:.2f}"
        governing_note = res_0['note']
    else:
        base_cpe = res_90['cpe']
        governing_case = f"Wind 90° (Side) | h/b={ratio_90:.2f}"
        governing_note = res_90['note']

    # --- 2. Iterate Zones using Base Cpe ---
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
        
        results_list.append({
            "Zone": z['code'],
            "Description": z['desc'],
            "Kl": z['kl'],
            "Pressure (kPa)": p_z,
            "Line Load (kN/m)": w_z,
            "Max Span (m)": span_z,
            "Reaction (kN)": max_reaction_z
        })
        
        if p_z > max_pressure_found:
            max_pressure_found = p_z
            worst_case_res = {
                'zone': z['code'],
                'pressure': p_z,
                'span': span_z,
                'fem': fem_res_z,
                'load': w_z
            }

    # ==========================
    # DISPLAY RESULTS UI
    # ==========================
    st.divider()
    st.header("📊 Analysis Report Summary")
    
    # --- SECTION A: WIND DIRECTION COMPARISON ---
    st.subheader("1. Wind Direction Analysis ($C_{p,e}$ Check)")
    col_w1, col_w2, col_w3 = st.columns(3)
    
    with col_w1:
        st.markdown("#### Wind 0° (Normal)")
        st.write(f"- Ratio h/d: **{ratio_0:.2f}**")
        st.info(f"Cpe = **{res_0['cpe']:.2f}**")
        st.caption(f"Note: {res_0['note']}")
        
    with col_w2:
        st.markdown("#### Wind 90° (Parallel)")
        st.write(f"- Ratio h/b: **{ratio_90:.2f}**")
        st.info(f"Cpe = **{res_90['cpe']:.2f}**")
        st.caption(f"Note: {res_90['note']}")
        
    with col_w3:
        st.markdown("#### Governing Case")
        st.error(f"**{governing_case}**")
        st.metric("Base Cpe", f"{base_cpe:.2f}")

    st.divider()

    # --- SECTION B: ZONE TABLE ---
    st.subheader("2. Zone Optimization Summary (RA1 - RA4)")
    df_res = pd.DataFrame(results_list)
    st.dataframe(
        df_res.style.format("{:.3f}", subset=["Pressure (kPa)", "Line Load (kN/m)", "Max Span (m)", "Reaction (kN)"])
              .format("{:.1f}", subset=["Kl"])
              .highlight_max(subset=["Pressure (kPa)", "Reaction (kN)"], color='#ffcccc')
              .highlight_min(subset=["Max Span (m)"], color='#ffcccc'),
        use_container_width=True
    )

    st.divider()
    
    # --- SECTION C: DIAGRAMS ---
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(f"3. Critical Case: {worst_case_res['zone']}")
        st.markdown(f"Worst case analysis for **{worst_case_res['zone']}** (Pressure: {worst_case_res['pressure']:.3f} kPa)")
        
        fig_fem, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)
        res = worst_case_res['fem']
        ax1.plot(res['x'], res['shear'], 'b-')
        ax1.fill_between(res['x'], res['shear'], color='blue', alpha=0.1)
        ax1.set_ylabel("Shear (kN)")
        max_r = np.max(np.abs(res['reactions']))
        ax1.text(0, max_r, f"Max R={max_r:.2f}kN", color='red', fontweight='bold')
        ax1.grid(True, linestyle=':')
        
        ax2.plot(res['x'], res['moment'], 'r-')
        ax2.fill_between(res['x'], res['moment'], color='red', alpha=0.1)
        ax2.set_ylabel("Moment (kNm)")
        ax2.grid(True, linestyle=':')
        st.pyplot(fig_fem)
        
    with col2:
        st.subheader("4. Input & Geometry")
        st.pyplot(plot_building_diagram(b_width, b_depth, roof_type))
        st.markdown("---")
        st.write(f"- **V_des:** {v_des:.2f} m/s")
        st.write(f"- **Angle:** {roof_angle}° ({roof_type})")
        st.write(f"- **Capacity (Mn):** {Mn:.3f} kNm")

    # ==========================
    # REPORT GENERATION
    # ==========================
    st.divider()
    st.header("📄 Plain Text Report Preview")
    
    table_str = df_res.to_string(index=False, justify="right", float_format=lambda x: "{:.3f}".format(x))
    
    # ASCII Blocks
    ridge_art = get_ascii_ridge_diagram(b_width, b_depth, roof_type)
    
    zone_art = ""
    for z in zones:
        zone_art += f"\n--- ZONE {z['code']} ({z['desc']}) ---"
        zone_art += get_ascii_art(z['code'])
        zone_art += "\n"

    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================

[1] PROJECT INFORMATION & INPUTS
--------------------------------
   - Regional Wind Speed (Vr):   {vr} m/s
   - Multipliers:                Md={md}, Ms={ms}, Mt={mt}
   - Design Wind Speed (Vdes):   {v_des:.2f} m/s
   
   - Terrain Category:           {tc}
   - Building Dimensions:        {b_width} m (W) x {b_depth} m (D) x {b_height} m (H)
   - Roof Configuration:         {roof_type}, Angle {roof_angle} deg
   
   - Rail Capacity (Mn):         {Mn:.3f} kNm 
     (Based on Test: Break Load {breaking_load} kN, Span {test_span} m, SF {safety_factor})

[2] WIND ANALYSIS DETAILS
-------------------------
   [2.1] DIRECTIONAL ANALYSIS (Cpe Check)
   --------------------------------------
   A. Wind 0 deg (Normal/Transverse):
      - Aspect Ratio h/d: {ratio_0:.2f}
      - Cpe Value:        {res_0['cpe']:.2f} ({res_0['note']})

   B. Wind 90 deg (Parallel/Longitudinal):
      - Aspect Ratio h/b: {ratio_90:.2f}
      - Cpe Value:        {res_90['cpe']:.2f} ({res_90['note']})

   >> GOVERNING CASE: {governing_case}
      Base Cpe used for design: {base_cpe:.2f}

   [2.2] LOAD PARAMETERS
   ---------------------
   - Tributary Width:    {trib_width:.3f} m
   - Area Reduction Ka:  {ka}

[3] ZONE OPTIMIZATION SUMMARY (RA1 - RA4)
-----------------------------------------
{table_str}

[4] CRITICAL DESIGN VALUES (WORST CASE SCENARIO)
------------------------------------------------
   The most critical condition occurs in Zone: {worst_case_res['zone']}
   
   >> Max Design Pressure:       {worst_case_res['pressure']:.3f} kPa
   >> Max Line Load on Rail:     {worst_case_res['load']:.3f} kN/m
   >> Max Allowable Span:        {worst_case_res['span']:.2f} m
   >> Max Uplift Reaction:       {df_res.loc[df_res['Zone'] == worst_case_res['zone'], 'Reaction (kN)'].values[0]:.3f} kN

[5] LIMITATIONS & CONDITIONS OF USE
-----------------------------------
   1. Valid Design Scope:
      - Terrain Category: {tc}
      - Max Roof Height: {b_height} m
      - Max Design Wind Speed: {v_des:.2f} m/s
      
   2. Prohibitions & Warnings:
      - DO NOT use this design if the building height exceeds {b_height} m.
      - The Pull-out capacity of screws/fasteners must be verified separately.
      - Rail deflection checks (Serviceability) are not included.

[6] VISUALIZATION GUIDE (ASCII ART)
-----------------------------------
   [6.1] BUILDING ORIENTATION & RIDGE
{ridge_art}

   [6.2] ROOF ZONES REFERENCE
{zone_art}
================================================================================
Generated by Solar Rail App | Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
================================================================================
"""

    st.code(report_text, language='text')
    
    st.download_button(
        label="💾 Download Report (.txt)",
        data=report_text,
        file_name="Solar_Rail_Report.txt",
        mime="text/plain"
    )
