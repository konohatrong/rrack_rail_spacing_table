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

# Custom CSS to try and make the UI look cleaner (Tahoma-ish for UI elements)
st.markdown("""
<style>
    .reportview-container .main .block-container{
        font-family: 'Tahoma', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Tahoma', sans-serif;
    }
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

vr = st.sidebar.number_input("Regional Wind Speed, Vr (m/s)", value=45.0, help="Region A=41-45, B=57, C=66, D=80")
md = st.sidebar.number_input("Direction Multiplier, Md", value=1.0, min_value=0.8, max_value=1.0)

st.sidebar.subheader("Terrain & Height")
tc = st.sidebar.selectbox("Terrain Category (TC)", [1, 2, 2.5, 3, 4], index=3)
b_height = st.sidebar.number_input("Building/Roof Height, z (m)", value=6.0, min_value=1.0)
ms = st.sidebar.number_input("Shielding Multiplier, Ms", value=1.0)
mt = st.sidebar.number_input("Topographic Multiplier, Mt", value=1.0)

# Calculate Vdes
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

def plot_building_diagram(b, d):
    fig, ax = plt.subplots(figsize=(5, 3))
    rect = patches.Rectangle((0, 0), b, d, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)
    ax.text(b/2, -d*0.15, f"Width b = {b}m", ha='center', color='blue', fontweight='bold', family='sans-serif')
    ax.text(-b*0.15, d/2, f"Depth d = {d}m", ha='right', va='center', rotation=90, color='green', fontweight='bold', family='sans-serif')
    
    ax.arrow(b/2, d+d*0.3, 0, -d*0.2, head_width=b*0.05, head_length=d*0.05, fc='red', ec='red')
    ax.text(b/2, d+d*0.35, "Wind 0°\n(Use h/d)", ha='center', color='red', fontsize=8, family='sans-serif')
    ax.arrow(-b*0.3, d/2, b*0.2, 0, head_width=d*0.05, head_length=b*0.05, fc='orange', ec='orange')
    ax.text(-b*0.35, d/2, "Wind 90°\n(Use h/b)", ha='center', va='center', rotation=90, color='orange', fontsize=8, family='sans-serif')
    
    ax.set_xlim(-b*0.5, b*1.5)
    ax.set_ylim(-d*0.3, d*1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

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
    
    # 1. Table
    st.subheader("1. Zone Analysis Summary")
    df_res = pd.DataFrame(results_list)
    st.dataframe(
        df_res.style.format("{:.3f}", subset=["Pressure (kPa)", "Line Load (kN/m)", "Max Span (m)", "Reaction (kN)"])
              .format("{:.1f}", subset=["Kl"])
              .highlight_max(subset=["Pressure (kPa)", "Reaction (kN)"], color='#ffcccc')
              .highlight_min(subset=["Max Span (m)"], color='#ffcccc'),
        use_container_width=True
    )

    # 2. Diagrams
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(f"2. Critical Case: {worst_case_res['zone']}")
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
        st.subheader("3. Input Summary")
        st.write(f"- **V_des:** {v_des:.2f} m/s")
        st.write(f"- **Angle:** {roof_angle}° ({roof_type})")
        st.write(f"- **Direction:** {governing_case}")
        st.write(f"- **Panel:** {panel_w}x{panel_d}m")
        st.write(f"- **Capacity (Mn):** {Mn:.3f} kNm")

    # ==========================
    # REPORT GENERATION
    # ==========================
    st.divider()
    st.header("📄 Plain Text Report Preview")
    st.caption("You can copy the report below or click 'Download'.")
    
    # Convert table to string
    table_str = df_res.to_string(index=False, justify="right", float_format=lambda x: "{:.3f}".format(x))
    
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

[2] ANALYSIS RESULTS SUMMARY (ALL ZONES)
----------------------------------------
   - Governing Wind Direction:   {governing_case}
   - Base External Cp,e:         {base_cpe:.2f}
   - Tributary Width:            {trib_width:.3f} m

{table_str}

[3] CRITICAL DESIGN VALUES (WORST CASE SCENARIO)
------------------------------------------------
   The most critical condition occurs in Zone: {worst_case_res['zone']}
   
   >> Max Design Pressure:       {worst_case_res['pressure']:.3f} kPa
   >> Max Line Load on Rail:     {worst_case_res['load']:.3f} kN/m
   >> Max Allowable Span:        {worst_case_res['span']:.2f} m
   >> Max Uplift Reaction:       {df_res.loc[df_res['Zone'] == worst_case_res['zone'], 'Reaction (kN)'].values[0]:.3f} kN

[4] LIMITATIONS & CONDITIONS OF USE
-----------------------------------
   1. Valid Design Scope:
      This calculation is strictly valid ONLY for the conditions specified above:
      - Terrain Category: {tc}
      - Max Roof Height: {b_height} m
      - Max Roof Angle: {roof_angle} degrees
      - Max Design Wind Speed: {v_des:.2f} m/s
      
   2. Prohibitions & Warnings:
      - DO NOT use this design if the building height exceeds {b_height} m.
      - DO NOT use if the site topography suggests a multiplier Mt > {mt}.
      - This report analyzes the ALUMINUM RAIL profile capacity ONLY.
      - The Pull-out capacity of screws/fasteners to the roof structure IS NOT
        covered by this report and must be verified separately using the 
        'Max Reaction' forces provided in Section [2].
      - Rail deflection checks (Serviceability) are not included in this output.

================================================================================
Generated by Solar Rail App | Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
================================================================================
"""

    # --- PREVIEW WITH COPY BUTTON ---
    # Using st.code with language='text' creates a nice block with a Copy button
    st.code(report_text, language='text')
    
    # Download Button
    st.download_button(
        label="💾 Download Report (.txt)",
        data=report_text,
        file_name="Solar_Rail_Report.txt",
        mime="text/plain"
    )
