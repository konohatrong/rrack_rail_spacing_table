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
    div.stButton > button { width: 100%; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Solar Rail Design & Analysis (AS/NZS 1170.2:2021)")
st.markdown("**Structural Engineer & Software Developer:** Aluminum Rail Analysis for Solar PV")

# ... (Data Loading Functions เหมือนเดิม) ...
@st.cache_data
def load_rail_data():
    try:
        url = "https://raw.githubusercontent.com/konohatrong/rrack_rail_spacing_table/main/rail_data.csv"
        df = pd.read_csv(url)
        return df
    except Exception:
        data = {
            'Brand': ['Generic', 'SolarRail-X'],
            'Model': ['Standard', 'SR-40Heavy'],
            'Breaking Load (kN)': [5.0, 7.5],
            'Test Span (m)': [1.0, 1.2]
        }
        return pd.DataFrame(data)

def get_csv_template():
    df = pd.DataFrame(columns=['Brand', 'Model', 'Breaking Load (kN)', 'Test Span (m)'])
    return df.to_csv(index=False)

df_rails = load_rail_data()

# ... (Sidebar Inputs เหมือนเดิม) ...
st.sidebar.header("1. Wind Parameters (AS/NZS 1170.0/1170.2)")
st.sidebar.markdown("**Step A: Importance & Probability**")
region_list = ["A0", "A1", "A2", "A3", "A4", "A5", "B1", "B2", "C", "D"]
region = st.sidebar.selectbox("Wind Region", region_list, index=1)
imp_level = st.sidebar.selectbox("Importance Level (IL)", [1, 2, 3, 4], index=1)
design_life = st.sidebar.selectbox("Design Working Life (Years)", [5, 25, 50, 100], index=2)

ret_period = wind_load.get_return_period(imp_level, design_life)
vr = wind_load.get_vr_from_ari(region, ret_period)
st.sidebar.info(f"**Calculated Values:**\n- Return Period (R): 1/{ret_period}\n- Regional Speed ($V_R$): {vr} m/s")

st.sidebar.markdown("**Step B: Site Multipliers**")
md = st.sidebar.number_input("Direction Multiplier, Md", value=1.0, min_value=0.8, max_value=1.0)
tc = st.sidebar.selectbox("Terrain Category (TC)", [1, 2, 2.5, 3, 4], index=3)
b_height = st.sidebar.number_input("Building/Roof Height, z (m)", value=6.0, min_value=1.0)
ms = st.sidebar.number_input("Shielding Multiplier, Ms", value=1.0)
mt = st.sidebar.number_input("Topographic Multiplier, Mt", value=1.0)

mz_cat = wind_load.get_mz_cat(b_height, tc)
v_des = wind_load.calculate_v_des_detailed(vr, md, mz_cat, ms, mt)
st.sidebar.success(f"**Design Wind Speed ($V_{{des}}$) = {v_des:.2f} m/s**")

st.sidebar.header("2. Geometry")
b_width = st.sidebar.number_input("Building Width, b (m)", value=20.0)
b_depth = st.sidebar.number_input("Building Depth, d (m)", value=15.0)
roof_type = st.sidebar.radio("Roof Shape", ["Monoslope", "Gable Roof"])
roof_angle = st.sidebar.number_input("Roof Angle (Degrees)", min_value=0.0, max_value=60.0, value=10.0, step=0.5)

st.sidebar.header("3. Panel & Rail")
panel_w = st.sidebar.number_input("Panel Width (m)", 1.134)
panel_d = st.sidebar.number_input("Panel Depth (m)", 2.279)
rail_orient = st.sidebar.selectbox("Rail Parallel to", ["Panel Width", "Panel Depth"])
orient_key = 'width' if rail_orient == "Panel Width" else 'depth'
ka = st.sidebar.number_input("Ka", 1.0)
kc = st.sidebar.number_input("Kc", 1.0)

st.sidebar.header("4. Structural Data")
st.sidebar.download_button("📥 Download Template", get_csv_template(), "rail_template.csv", "text/csv")
rail_opts = ["Custom Input"] + [f"{r['Brand']} - {r['Model']}" for i, r in df_rails.iterrows()]
sel_rail = st.sidebar.selectbox("Select Rail", rail_opts)

if sel_rail != "Custom Input":
    r_data = df_rails[(df_rails['Brand'] == sel_rail.split(" - ")[0]) & (df_rails['Model'] == sel_rail.split(" - ")[1])].iloc[0]
    def_brand, def_model, def_bk, def_sp = r_data['Brand'], r_data['Model'], float(r_data['Breaking Load (kN)']), float(r_data['Test Span (m)'])
    dis = True
else:
    def_brand, def_model, def_bk, def_sp, dis = "Custom", "-", 5.0, 1.0, False

rail_brand = st.sidebar.text_input("Brand", def_brand, disabled=dis)
rail_model = st.sidebar.text_input("Model", def_model, disabled=dis)
breaking_load = st.sidebar.number_input("Breaking Load (kN)", def_bk, disabled=dis)
test_span = st.sidebar.number_input("Test Span (m)", def_sp, disabled=dis)
safety_factor = st.sidebar.number_input("Safety Factor", 1.1)
num_spans = st.sidebar.slider("Spans", 1, 5, 2)

# ... (Visualization Functions - plot_building_diagram, plot_panel_load_diagram, plot_fem_diagrams_annotated เหมือนเดิม) ...
# เพื่อความกระชับ ขอละไว้ในส่วนนี้ (ใช้ function เดิมจากคำตอบก่อนหน้าได้เลย)
def plot_building_diagram(b, d, r_type):
    fig, ax = plt.subplots(figsize=(5, 3))
    rect = patches.Rectangle((0, 0), b, d, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)
    ax.text(b/2, -d*0.15, f"Width b = {b}m", ha='center', color='blue', fontweight='bold', family='sans-serif')
    ax.text(-b*0.15, d/2, f"Depth d = {d}m", ha='right', va='center', rotation=90, color='green', fontweight='bold', family='sans-serif')
    ax.arrow(b/2, d+d*0.3, 0, -d*0.2, head_width=b*0.05, head_length=d*0.05, fc='red', ec='red')
    ax.text(b/2, d+d*0.35, "Wind 0° (Normal)", ha='center', color='red', fontsize=8, family='sans-serif')
    ax.arrow(-b*0.3, d/2, b*0.2, 0, head_width=d*0.05, head_length=b*0.05, fc='orange', ec='orange')
    ax.text(-b*0.35, d/2, "Wind 90° (Parallel)", ha='center', va='center', rotation=90, color='orange', fontsize=8, family='sans-serif')
    if "Gable" in r_type:
        ax.plot([0, b], [d/2, d/2], color='purple', linestyle='-.', linewidth=2.5)
        ax.text(b*0.02, d/2 + d*0.03, "RIDGE LINE", color='purple', fontsize=9, fontweight='bold', ha='left')
    ax.set_xlim(-b*0.5, b*1.5); ax.set_ylim(-d*0.3, d*1.5); ax.axis('off')
    return fig

def plot_panel_load_diagram(pw, pd, orient, trib_w):
    fig, ax = plt.subplots(figsize=(5, 5))
    panel = patches.Rectangle((0, 0), pw, pd, linewidth=2, edgecolor='black', facecolor='white', label='Panel')
    ax.add_patch(panel)
    if orient == 'width':
        rail_y1, rail_y2 = pd * 0.25, pd * 0.75
        ax.axhline(rail_y1, color='blue', linewidth=3, linestyle='--', label='Rail')
        ax.axhline(rail_y2, color='blue', linewidth=3, linestyle='--')
        rect_trib = patches.Rectangle((0, 0), pw, pd/2, linewidth=0, facecolor='red', alpha=0.2, label='Trib. Area')
        ax.add_patch(rect_trib)
        dim_x = pw + 0.15
        ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, pd/2), arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
        ax.text(dim_x + 0.05, pd/4, f"Trib = {trib_w:.3f} m", color='red', rotation=90, va='center')
    else:
        rail_x1, rail_x2 = pw * 0.25, pw * 0.75
        ax.axvline(rail_x1, color='blue', linewidth=3, linestyle='--', label='Rail')
        ax.axvline(rail_x2, color='blue', linewidth=3, linestyle='--')
        rect_trib = patches.Rectangle((0, 0), pw/2, pd, linewidth=0, facecolor='red', alpha=0.2, label='Trib. Area')
        ax.add_patch(rect_trib)
        dim_y = pd + 0.15
        ax.annotate('', xy=(0, dim_y), xytext=(pw/2, dim_y), arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
        ax.text(pw/4, dim_y + 0.05, f"Trib = {trib_w:.3f} m", color='red', ha='center')
    ax.text(pw/2, -0.1, f"Width = {pw}m", ha='center'); ax.text(-0.1, pd/2, f"Depth = {pd}m", va='center', rotation=90)
    ax.set_xlim(-0.3, pw + 0.5); ax.set_ylim(-0.3, pd + 0.5); ax.set_aspect('equal'); ax.axis('off')
    return fig

def plot_fem_diagrams_annotated(analysis_res, zone_name):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    x = analysis_res['x']
    shear = analysis_res['shear']
    ax1.plot(x, shear, 'b-'); ax1.fill_between(x, shear, color='blue', alpha=0.1)
    ax1.set_ylabel("Shear (kN)"); ax1.set_title(f"SFD - {zone_name}"); ax1.grid(True, ls=':')
    v_max_idx = np.argmax(np.abs(shear)); v_val = shear[v_max_idx]
    ax1.plot(x[v_max_idx], v_val, 'ro')
    ax1.annotate(f"V*={abs(v_val):.2f}", xy=(x[v_max_idx], v_val), xytext=(10, 10), textcoords="offset points", color='red', fontweight='bold')
    
    moment = analysis_res['moment']
    ax2.plot(x, moment, 'r-'); ax2.fill_between(x, moment, color='red', alpha=0.1)
    ax2.set_ylabel("Moment (kNm)"); ax2.set_title(f"BMD - {zone_name}"); ax2.grid(True, ls=':')
    m_max_idx = np.argmax(np.abs(moment)); m_val = moment[m_max_idx]
    ax2.plot(x[m_max_idx], m_val, 'bo')
    ax2.annotate(f"M*={abs(m_val):.2f}", xy=(x[m_max_idx], m_val), xytext=(10, 10), textcoords="offset points", color='blue', fontweight='bold')
    plt.tight_layout()
    return fig

# ==========================================
# MAIN LOGIC
# ==========================================
if st.button("🚀 Run Analysis"):
    Mn = structural.calculate_Mn(breaking_load, test_span, safety_factor)
    trib_width = wind_load.calculate_tributary_width(panel_w, panel_d, orient_key)
    
    r0 = b_height / b_depth; res0 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, r0)
    r90 = b_height / b_width; res90 = wind_load.solve_cpe_for_ratio(roof_angle, roof_type, r90)
    
    if res0['cpe'] < res90['cpe']:
        base_cpe, gov_case, note = res0['cpe'], f"Wind 0° (h/d={r0:.2f})", "Normal Wind Direction"
    else:
        base_cpe, gov_case, note = res90['cpe'], f"Wind 90° (h/b={r90:.2f})", "Parallel Wind Direction"

    zones = [{"code": "RA1", "desc": "General Area", "kl": 1.0}, {"code": "RA2", "desc": "Edges/Ridge", "kl": 1.5}, 
             {"code": "RA3", "desc": "Corners", "kl": 2.0}, {"code": "RA4", "desc": "High Suction", "kl": 3.0}]
    
    results, worst_res, max_p = [], None, -1.0
    
    for z in zones:
        p_z = wind_load.calculate_wind_pressure(v_des, base_cpe, ka, kc, z['kl'])
        w_z = p_z * trib_width
        span, fem = structural.optimize_span(Mn, w_z, num_spans, max_span=4.0)
        rxn, mom, shr = np.max(np.abs(fem['reactions'])), fem['max_moment'], np.max(np.abs(fem['shear']))
        
        results.append({"Zone": z['code'], "Description": z['desc'], "Kl": z['kl'], "Pressure (kPa)": p_z, "Line Load (kN/m)": w_z, "Max Span (m)": span, "Reaction (kN)": rxn, "M* (kNm)": mom})
        if p_z > max_p:
            max_p = p_z
            worst_res = {'zone': z['code'], 'pressure': p_z, 'span': span, 'fem': fem, 'load': w_z, 'moment': mom, 'shear_max': shr, 'reaction': rxn}

    # --- OUTPUT ---
    st.divider(); st.header("📊 Analysis Report Summary")
    
    # 1. INPUT & GEOMETRY
    st.subheader("1. Input Summary"); c1, c2 = st.columns([1, 1])
    with c1: st.write(f"**Rail:** {rail_brand} ({rail_model})"); st.write(f"**Region:** {region} (Vr={vr} m/s)"); st.write(f"**Vdes:** {v_des:.2f} m/s")
    with c2: st.pyplot(plot_building_diagram(b_width, b_depth, roof_type))

    # 2. WIND & TRIB
    st.divider(); st.subheader("2. Wind & Load Analysis"); c1, c2 = st.columns([1, 1])
    with c1: st.write(f"**Wind 0°:** {res0['cpe']:.2f}"); st.write(f"**Wind 90°:** {res90['cpe']:.2f}"); st.info(f"**Governing:** {gov_case}")
    with c2: st.pyplot(plot_panel_load_diagram(panel_w, panel_d, orient_key, trib_width))

    # 3. ZONES
    st.divider(); st.subheader("3. Zone Analysis (RA1-RA4)"); df_res = pd.DataFrame(results)
    st.dataframe(df_res.style.format("{:.3f}", subset=["Pressure (kPa)","Line Load (kN/m)","Max Span (m)","Reaction (kN)","M* (kNm)"]).highlight_max(["Pressure (kPa)"], color='#ffcccc'), use_container_width=True)

    # 4. CRITICAL
    st.divider(); st.subheader(f"4. Critical Case: {worst_res['zone']}"); c1, c2 = st.columns([1, 2])
    with c1: st.metric("M*", f"{worst_res['moment']:.3f}"); st.metric("V*", f"{worst_res['shear_max']:.3f}"); st.metric("Reaction", f"{worst_res['reaction']:.3f}")
    with c2: st.pyplot(plot_fem_diagrams_annotated(worst_res['fem'], worst_res['zone']))

    # REPORT
    st.divider(); st.header("📄 Plain Text Report")
    input_dict = {
        'rail_brand': rail_brand, 'rail_model': rail_model, 'region': region, 'imp_level': imp_level, 'design_life': design_life, 'ret_period': ret_period, 'vr': vr, 'v_des': v_des,
        'md': md, 'ms': ms, 'mt': mt, 'mz_cat': mz_cat, 'tc': tc, 'b_width': b_width, 'b_depth': b_depth, 'b_height': b_height, 'roof_type': roof_type, 'roof_angle': roof_angle,
        'panel_w': panel_w, 'panel_d': panel_d
    }
    wind_dict = {
        'cpe_0': res0['cpe'], 'ratio_0': r0, 'cpe_90': res90['cpe'], 'ratio_90': r90, 'governing_case': gov_case, 'note': note,
        'trib_width': trib_width, 'ka': ka, 'kc': kc, 'cpe_base': base_cpe
    }
    struct_dict = {'Mn': Mn, 'break_load': breaking_load, 'test_span': test_span, 'sf': safety_factor}
    
    report_text = report.generate_full_report(input_dict, wind_dict, struct_dict, results, worst_res)
    st.code(report_text, language='text')
    st.download_button("💾 Download Full Report", report_text, "Solar_Rail_Report.txt")
