import streamlit as st
import structural
import wind_load
import report  # ต้องมีไฟล์ report.py ที่อัปเดตแล้วอยู่ในโฟลเดอร์เดียวกัน
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Solar Rail Design (AS/NZS 1170.2)", layout="wide")

# Custom CSS for styling
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
# 0. DATA FUNCTIONS (GitHub / Template)
# ==========================================
@st.cache_data
def load_rail_data():
    try:
        # URL ไปยังไฟล์ CSV บน GitHub (Raw format)
        url = "https://raw.githubusercontent.com/konohatrong/rrack_rail_spacing_table/main/rail_data.csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        # กรณีโหลดไม่ได้ ให้ใช้ข้อมูลตัวอย่าง
        data = {
            'Brand': ['Generic', 'SolarRail-X', 'Alu-Pro'],
            'Model': ['Standard', 'SR-40Heavy', 'AP-60'],
            'Breaking Load (kN)': [5.0, 7.5, 6.2],
            'Test Span (m)': [1.0, 1.2, 1.0]
        }
        return pd.DataFrame(data)

def get_csv_template():
    df_template = pd.DataFrame(columns=['Brand', 'Model', 'Breaking Load (kN)', 'Test Span (m)'])
    return df_template.to_csv(index=False)

df_rails = load_rail_data()

# ==========================================
# SIDEBAR INPUTS
# ==========================================

st.sidebar.header("1. Wind Parameters (AS/NZS 1170.0/1170.2)")

# --- STEP A: PROBABILITY & REGION ---
st.sidebar.markdown("**Step A: Importance & Probability**")
region_list = ["A0", "A1", "A2", "A3", "A4", "A5", "B1", "B2", "C", "D"]
region = st.sidebar.selectbox("Wind Region", region_list, index=1)
imp_level = st.sidebar.selectbox("Importance Level (IL)", [1, 2, 3, 4], index=1, help="AS/NZS 1170.0 Table 3.3")
design_life = st.sidebar.selectbox("Design Working Life (Years)", [5, 25, 50, 100], index=2)

# Calculate Vr and Return Period
ret_period = wind_load.get_return_period(imp_level, design_life)
vr = wind_load.get_vr_from_ari(region, ret_period)

st.sidebar.info(f"**Calculated Values:**\n- Return Period (R): 1/{ret_period}\n- Regional Speed ($V_R$): {vr} m/s")

# --- STEP B: MULTIPLIERS ---
st.sidebar.markdown("**Step B: Site Multipliers**")
md = st.sidebar.number_input("Direction Multiplier, Md", value=1.0, min_value=0.8, max_value=1.0)
tc = st.sidebar.selectbox("Terrain Category (TC)", [1, 2, 2.5, 3, 4], index=3)
b_height = st.sidebar.number_input("Building/Roof Height, z (m)", value=6.0, min_value=1.0)
ms = st.sidebar.number_input("Shielding Multiplier, Ms", value=1.0)
mt = st.sidebar.number_input("Topographic Multiplier, Mt", value=1.0)

# Calculate Vdes
mz_cat = wind_load.get_mz_cat(b_height, tc)
v_des = wind_load.calculate_v_des_detailed(vr, md, mz_cat, ms, mt)
st.sidebar.success(f"**Design Wind Speed ($V_{{des}}$) = {v_des:.2f} m/s**")

# --- GEOMETRY ---
st.sidebar.header("2. Building Geometry")
b_width = st.sidebar.number_input("Building Width, b (m)", value=20.0)
b_depth = st.sidebar.number_input("Building Depth, d (m)", value=15.0)
roof_type = st.sidebar.radio("Roof Shape", ["Monoslope", "Gable Roof"])
roof_angle = st.sidebar.number_input("Roof Angle (Degrees)", min_value=0.0, max_value=60.0, value=10.0, step=0.5)

# --- PANEL & RAIL ---
st.sidebar.header("3. Panel & Rail")
panel_w = st.sidebar.number_input("Panel Width (m)", value=1.134)
panel_d = st.sidebar.number_input("Panel Depth (m)", value=2.279)
rail_orient = st.sidebar.selectbox("Panel Side Parallel to Rail Span", ["Panel Width", "Panel Depth"])
orient_key = 'width' if rail_orient == "Panel Width" else 'depth'

st.sidebar.subheader("Coefficients")
ka = st.sidebar.number_input("Area Reduction Factor (Ka)", value=1.0)
kc = st.sidebar.number_input("Comb. Factor (Kc)", value=1.0, help="Action Combination Factor")

# --- STRUCTURAL TEST DATA ---
st.sidebar.header("4. Structural Test Data")

st.sidebar.download_button(
    label="📥 Download CSV Template",
    data=get_csv_template(),
    file_name="rail_data_template.csv",
    mime="text/csv"
)

# Rail Selection from DB
rail_options = ["Custom Input"] + [f"{row['Brand']} - {row['Model']}" for i, row in df_rails.iterrows()]
selected_rail_str = st.sidebar.selectbox("Select Rail from Database:", rail_options)

if selected_rail_str != "Custom Input":
    sel_brand, sel_model = selected_rail_str.split(" - ")
    rail_data = df_rails[(df_rails['Brand'] == sel_brand) & (df_rails['Model'] == sel_model)].iloc[0]
    def_brand = rail_data['Brand']
    def_model = rail_data['Model']
    def_bk_load = float(rail_data['Breaking Load (kN)'])
    def_span = float(rail_data['Test Span (m)'])
    input_disabled = True
else:
    def_brand = "Custom"
    def_model = "-"
    def_bk_load = 5.0
    def_span = 1.0
    input_disabled = False

rail_brand = st.sidebar.text_input("Brand", value=def_brand, disabled=input_disabled)
rail_model = st.sidebar.text_input("Model No.", value=def_model, disabled=input_disabled)
breaking_load = st.sidebar.number_input("Breaking Load (kN)", value=def_bk_load, format="%.2f", disabled=input_disabled)
test_span = st.sidebar.number_input("Test Span (m)", value=def_span, format="%.2f", disabled=input_disabled)
safety_factor = st.sidebar.number_input("Safety Factor (Mn)", value=1.1)
num_spans = st.sidebar.slider("Number of Continuous Spans", 1, 5, 2)

# ==========================================
# VISUALIZATION FUNCTIONS (PLOTTING)
# ==========================================
def plot_building_diagram(b, d, r_type):
    fig, ax = plt.subplots(figsize=(5, 3))
    rect = patches.Rectangle((0, 0), b, d, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)
    
    # Dimensions
    ax.text(b/2, -d*0.15, f"Width b = {b}m", ha='center', color='blue', fontweight='bold', family='sans-serif')
    ax.text(-b*0.15, d/2, f"Depth d = {d}m", ha='right', va='center', rotation=90, color='green', fontweight='bold', family='sans-serif')
    
    # Wind Arrows
    ax.arrow(b/2, d+d*0.3, 0, -d*0.2, head_width=b*0.05, head_length=d*0.05, fc='red', ec='red')
    ax.text(b/2, d+d*0.35, "Wind 0° (Normal)", ha='center', color='red', fontsize=8, family='sans-serif')
    ax.arrow(-b*0.3, d/2, b*0.2, 0, head_width=d*0.05, head_length=b*0.05, fc='orange', ec='orange')
    ax.text(-b*0.35, d/2, "Wind 90° (Parallel)", ha='center', va='center', rotation=90, color='orange', fontsize=8, family='sans-serif')
    
    # Ridge Line
    if "Gable" in r_type:
        ax.plot([0, b], [d/2, d/2], color='purple', linestyle='-.', linewidth=2.5)
        ax.text(b*0.02, d/2 + d*0.03, "RIDGE LINE", color='purple', fontsize=9, fontweight='bold', ha='left')
    
    ax.set_xlim(-b*0.5, b*1.5)
    ax.set_ylim(-d*0.3, d*1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def plot_panel_load_diagram(pw, pd, orient, trib_w):
    fig, ax = plt.subplots(figsize=(5, 5))
    panel = patches.Rectangle((0, 0), pw, pd, linewidth=2, edgecolor='black', facecolor='white', label='Panel')
    ax.add_patch(panel)
    
    if orient == 'width':
        # Rails Horizontal
        rail_y1, rail_y2 = pd * 0.25, pd * 0.75
        ax.axhline(rail_y1, color='blue', linewidth=3, linestyle='--', label='Rail')
        ax.axhline(rail_y2, color='blue', linewidth=3, linestyle='--')
        
        # Trib Area
        rect_trib = patches.Rectangle((0, 0), pw, pd/2, linewidth=0, facecolor='red', alpha=0.2, label='Trib. Area')
        ax.add_patch(rect_trib)
        
        # Dimension
        dim_x = pw + 0.15
        ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, pd/2), arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
        ax.text(dim_x + 0.05, pd/4, f"Trib = {trib_w:.3f} m", color='red', rotation=90, va='center')
        
    else:
        # Rails Vertical
        rail_x1, rail_x2 = pw * 0.25, pw * 0.75
        ax.axvline(rail_x1, color='blue', linewidth=3, linestyle='--', label='Rail')
        ax.axvline(rail_x2, color='blue', linewidth=3, linestyle='--')
        
        # Trib Area
        rect_trib = patches.Rectangle((0, 0), pw/2, pd, linewidth=0, facecolor='red', alpha=0.2, label='Trib. Area')
        ax.add_patch(rect_trib)
        
        # Dimension
        dim_y = pd + 0.15
        ax.annotate('', xy=(0, dim_y), xytext=(pw/2, dim_y), arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
        ax.text(pw/4, dim_y + 0.05, f"Trib = {trib_w:.3f} m", color='red', ha='center')

    ax.text(pw/2, -0.1, f"Width = {pw}m", ha='center')
    ax.text(-0.1, pd/2, f"Depth = {pd}m", va='center', rotation=90)
    ax.set_xlim(-0.3, pw + 0.5)
    ax.set_ylim(-0.3, pd + 0.5)
    ax.set_aspect('equal')
    ax.legend(loc='lower right', fontsize='small')
    ax.axis('off')
    ax.set_title("Tributary Width Concept", fontsize=10)
    return fig

def plot_fem_diagrams_annotated(analysis_res, zone_name):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    
    # SFD
    x = analysis_res['x']
    shear = analysis_res['shear']
    ax1.plot(x, shear, 'b-')
    ax1.fill_between(x, shear, color='blue', alpha=0.1)
    ax1.set_ylabel("Shear (kN)")
    ax1.set_title(f"Shear Force Diagram (SFD) - {zone_name}")
    ax1.grid(True, linestyle=':')
    ax1.axhline(0, color='black', linewidth=0.8)
    
    # Max Shear Annotation
    v_max_idx = np.argmax(np.abs(shear))
    v_val = shear[v_max_idx]
    ax1.plot(x[v_max_idx], v_val, 'ro')
    ax1.annotate(f"V*={abs(v_val):.2f} kN", xy=(x[v_max_idx], v_val), xytext=(10, 10 if v_val>0 else -15), 
                 textcoords="offset points", color='red', fontweight='bold')
    
    # BMD
    moment = analysis_res['moment']
    ax2.plot(x, moment, 'r-')
    ax2.fill_between(x, moment, color='red', alpha=0.1)
    ax2.set_ylabel("Moment (kNm)")
    ax2.set_title(f"Bending Moment Diagram (BMD) - {zone_name}")
    ax2.grid(True, linestyle=':')
    ax2.axhline(0, color='black', linewidth=0.8)
    
    # Max Moment Annotation
    m_max_idx = np.argmax(np.abs(moment))
    m_val = moment[m_max_idx]
    ax2.plot(x[m_max_idx], m_val, 'bo')
    ax2.annotate(f"M*={abs(m_val):.2f} kNm", xy=(x[m_max_idx], m_val), xytext=(10, 10 if m_val>0 else -15), 
                 textcoords="offset points", color='blue', fontweight='bold')
    
    plt.tight_layout()
    return fig

# ==========================================
# MAIN LOGIC & PROCESSING
# ==========================================
if st.button("🚀 Run Analysis"):
    # 1. Structural Capacity
    Mn = structural.calculate_Mn(breaking_load, test_span, safety_factor)
    trib_width = wind_load.calculate_tributary_width(panel_w, panel_d, orient_key)
    
    # 2. Wind Analysis (0 deg vs 90 deg)
    ratio_0 = b_height / b_depth
    res_0 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, ratio_0)
    
    ratio_90 = b_height / b_width
    res_90 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, ratio_90)
    
    # Determine Governing Cpe
    if res_0['cpe'] < res_90['cpe']:
        base_cpe = res_0['cpe']
        governing_case = f"Wind 0° (Normal) | h/d={ratio_0:.2f}"
        direction_note = "Using Cpe from Wind 0° as it creates higher suction."
    else:
        base_cpe = res_90['cpe']
        governing_case = f"Wind 90° (Side) | h/b={ratio_90:.2f}"
        direction_note = "Using Cpe from Wind 90° as it creates higher suction."

    # 3. Zone Iteration
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
        # Calculate Pressure & Load
        p_z = wind_load.calculate_wind_pressure(v_des, base_cpe, Ka=ka, Kc=kc, Kl=z['kl'])
        w_z = p_z * trib_width
        
        # FEM Optimization
        span_z, fem_res_z = structural.optimize_span(Mn, w_z, num_spans, max_span=4.0)
        
        # Extract Results
        max_reaction_z = np.max(np.abs(fem_res_z['reactions']))
        max_moment_z = fem_res_z['max_moment']
        max_shear_z = np.max(np.abs(fem_res_z['shear']))
        
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
                'shear_max': max_shear_z,
                'reaction': max_reaction_z
            }

    # ==========================================
    # DISPLAY RESULTS
    # ==========================================
    st.divider()
    st.header("📊 Analysis Report Summary")
    
    # 1. INPUT SUMMARY (First, as requested)
    st.subheader("1. Input Summary & Geometry")
    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        st.markdown(f"**Rail Model:** {rail_brand} ({rail_model})")
        st.markdown(f"**Wind Region:** {region} (Vr={vr} m/s)")
        st.markdown(f"**Probability:** IL-{imp_level}, Life {design_life}y (1/{ret_period})")
        st.markdown(f"**Design Speed:** Vdes = {v_des:.2f} m/s")
        st.markdown(f"**Building:** {b_width}x{b_depth}x{b_height}m ({roof_type})")
    with col_in2:
        st.pyplot(plot_building_diagram(b_width, b_depth, roof_type))

    st.divider()

    # 2. WIND & LOAD DETAILS
    st.subheader("2. Wind Direction & Loading")
    col_wd1, col_wd2 = st.columns([1, 1])
    with col_wd1:
        st.markdown("**Directional Analysis (Cpe):**")
        st.write(f"- Wind 0° (Normal): Cpe = {res_0['cpe']:.2f} (h/d={ratio_0:.2f})")
        st.write(f"- Wind 90° (Parallel): Cpe = {res_90['cpe']:.2f} (h/b={ratio_90:.2f})")
        st.info(f"**Governing:** {governing_case}")
    with col_wd2:
        st.markdown("**Tributary Width:**")
        st.pyplot(plot_panel_load_diagram(panel_w, panel_d, orient_key, trib_width))

    st.divider()

    # 3. ZONE TABLE
    st.subheader("3. Zone Analysis Summary (RA1-RA4)")
    df_res = pd.DataFrame(results_list)
    st.dataframe(
        df_res.style.format("{:.3f}", subset=["Pressure (kPa)", "Line Load (kN/m)", "Max Span (m)", "Reaction (kN)", "M* (kNm)"])
              .format("{:.1f}", subset=["Kl"])
              .highlight_max(subset=["Pressure (kPa)", "Reaction (kN)", "M* (kNm)"], color='#ffcccc')
              .highlight_min(subset=["Max Span (m)"], color='#ffcccc'),
        use_container_width=True
    )

    st.divider()

    # 4. CRITICAL CASE DETAILS
    st.subheader(f"4. Critical Case Analysis ({worst_case_res['zone']})")
    col_crit1, col_crit2 = st.columns([1, 2])
    with col_crit1:
        st.markdown("### Critical Design Values")
        st.metric("M* (Design Moment)", f"{worst_case_res['moment']:.3f} kNm")
        st.metric("V* (Max Shear)", f"{worst_case_res['shear_max']:.2f} kN")
        st.metric("Max Reaction", f"{worst_case_res['reaction']:.2f} kN")
        st.caption(f"At Max Span: {worst_case_res['span']:.2f} m")
    with col_crit2:
        st.pyplot(plot_fem_diagrams_annotated(worst_case_res['fem'], worst_case_res['zone']))

    # ==========================================
    # REPORT GENERATION
    # ==========================================
    st.divider()
    st.header("📄 Plain Text Report")
    
    # Pack data for report generator
    input_dict = {
        'rail_brand': rail_brand, 'rail_model': rail_model,
        'region': region, 'imp_level': imp_level, 'design_life': design_life,
        'ret_period': ret_period, 'vr': vr, 'v_des': v_des,
        'md': md, 'ms': ms, 'mt': mt, 'mz_cat': mz_cat, 'tc': tc,
        'b_width': b_width, 'b_depth': b_depth, 'b_height': b_height,
        'roof_type': roof_type, 'roof_angle': roof_angle,
        'panel_w': panel_w, 'panel_d': panel_d, 'num_spans': num_spans
    }
    
    wind_dict = {
        'cpe_0': res_0['cpe'], 'ratio_0': ratio_0,
        'cpe_90': res90['cpe'], 'ratio_90': ratio_90,
        'governing_case': governing_case, 'note': direction_note,
        'trib_width': trib_width, 'ka': ka, 'kc': kc, 'cpe_base': base_cpe
    }
    
    struct_dict = {
        'Mn': Mn, 'break_load': breaking_load, 'test_span': test_span, 'sf': safety_factor
    }
    
    # Generate Report
    report_text = report.generate_full_report(input_dict, wind_dict, struct_dict, results_list, worst_case_res)
    
    st.code(report_text, language='text')
    st.download_button("💾 Download Full Report", report_text, "Solar_Rail_Report.txt")
