import streamlit as st
import structural
import wind_load
import report
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import datetime  # Import datetime to fix NameError

# Set page configuration
st.set_page_config(page_title="Solar Rail Design (AS/NZS 1170.2)", layout="wide")

st.markdown("""
<style>
    .reportview-container .main .block-container{ font-family: 'Tahoma', sans-serif; }
    h1, h2, h3 { font-family: 'Tahoma', sans-serif; }
    div.stButton > button { width: 100%; font-weight: bold; }
    .stDownloadButton > button { width: 100%; border-color: #4CAF50; color: #4CAF50; }
    .calculation-box { background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; margin-bottom: 10px; }
    .info-box { background-color: #e7f3fe; padding: 15px; border-radius: 5px; border-left: 4px solid #2196f3; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Solar Rail Design & Analysis (AS/NZS 1170.2:2021)")
st.markdown("**Structural Engineer & Software Developer:** Aluminum Rail Analysis for Solar PV")

# ==========================================
# 0. DATA FUNCTIONS
# ==========================================
@st.cache_data
def load_rail_data():
    try:
        url = "https://raw.githubusercontent.com/konohatrong/rrack_rail_spacing_table/main/rail_data.csv"
        df = pd.read_csv(url)
        return df
    except Exception:
        data = {'Brand': ['Generic'], 'Model': ['Standard'], 'Breaking Load (kN)': [5.0], 'Test Span (m)': [1.0]}
        return pd.DataFrame(data)

def get_csv_template():
    df = pd.DataFrame(columns=['Brand', 'Model', 'Breaking Load (kN)', 'Test Span (m)'])
    return df.to_csv(index=False)

df_rails = load_rail_data()

# ==========================================
# SIDEBAR INPUTS
# ==========================================

# --- 0. PROJECT INFO ---
st.sidebar.header("0. Project Details")
project_name = st.sidebar.text_input("Project Name", "Solar Rooftop Project")
project_loc = st.sidebar.text_input("Location", "Bangkok, Thailand")
engineer_name = st.sidebar.text_input("Engineer Name", "-")

st.sidebar.markdown("---")

st.sidebar.header("1. Wind Parameters")
# --- FIXED: ADDED NZ REGIONS HERE ---
region = st.sidebar.selectbox("Wind Region", 
    ["A0", "A1", "A2", "A3", "A4", "A5", "B1", "B2", "C", "D", "NZ1", "NZ2", "NZ3", "NZ4"], 
    index=1
)
imp_level = st.sidebar.selectbox("Importance Level (IL)", [1, 2, 3, 4], index=1)
design_life = st.sidebar.selectbox("Design Life (Years)", [5, 25, 50, 100], index=2)

ret_period = wind_load.get_return_period(imp_level, design_life)
vr = wind_load.get_vr_from_ari(region, ret_period)
st.sidebar.info(f"R = 1/{ret_period} yr | Vr = {vr} m/s")

st.sidebar.markdown("**Step B: Site Multipliers**")
md = st.sidebar.number_input("Md", 1.0, step=0.05)
tc = st.sidebar.selectbox("Terrain Category (TC)", [1, 2, 2.5, 3, 4], index=3)
b_height = st.sidebar.number_input("Roof Height (m)", 6.0)
ms = st.sidebar.number_input("Ms", 1.0)
mt = st.sidebar.number_input("Mt", 1.0)

mz_cat = wind_load.get_mz_cat(b_height, tc)
v_des = wind_load.calculate_v_des_detailed(vr, md, mz_cat, ms, mt)
st.sidebar.success(f"Vdes = {v_des:.2f} m/s")

st.sidebar.header("2. Geometry")
b_width = st.sidebar.number_input("Building Width (m)", 20.0)
b_depth = st.sidebar.number_input("Building Depth (m)", 15.0)
roof_type = st.sidebar.radio("Roof Shape", ["Monoslope", "Gable Roof"])
roof_angle = st.sidebar.number_input("Roof Angle (deg)", 10.0)

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
    def_brand, def_model, def_bk, def_sp, dis = r_data['Brand'], r_data['Model'], float(r_data['Breaking Load (kN)']), float(r_data['Test Span (m)']), True
else:
    def_brand, def_model, def_bk, def_sp, dis = "Custom", "-", 5.0, 1.0, False

rail_brand = st.sidebar.text_input("Brand", def_brand, disabled=dis)
rail_model = st.sidebar.text_input("Model", def_model, disabled=dis)
breaking_load = st.sidebar.number_input("Breaking Load (kN)", def_bk, disabled=dis)
test_span = st.sidebar.number_input("Test Span (m)", def_sp, disabled=dis)
safety_factor = st.sidebar.number_input("Safety Factor", value=1.1, min_value=0.001, step=0.01, format="%.3f")
num_spans = st.sidebar.slider("Spans", 1, 5, 2)

# ==========================================
# VISUALIZATION FUNCTIONS
# ==========================================
def plot_building_diagram(b, d, r_type):
    fig, ax = plt.subplots(figsize=(5, 3))
    rect = patches.Rectangle((0, 0), b, d, linewidth=2, edgecolor='black', facecolor='#f0f0f0')
    ax.add_patch(rect)
    ax.text(b/2, -d*0.15, f"Width {b}m", ha='center', color='blue')
    ax.text(-b*0.15, d/2, f"Depth {d}m", ha='right', va='center', rotation=90, color='green')
    ax.arrow(b/2, d+d*0.3, 0, -d*0.2, head_width=b*0.05, fc='red', ec='red')
    ax.text(b/2, d+d*0.35, "Wind 0°", ha='center', color='red')
    ax.arrow(-b*0.3, d/2, b*0.2, 0, head_width=d*0.05, fc='orange', ec='orange')
    ax.text(-b*0.35, d/2, "Wind 90°", ha='center', va='center', rotation=90, color='orange')
    if "Gable" in r_type:
        ax.plot([0, b], [d/2, d/2], color='purple', linestyle='-.')
        ax.text(b*0.02, d/2+d*0.02, "RIDGE", color='purple', fontsize=8)
    ax.set_xlim(-b*0.5, b*1.5); ax.set_ylim(-d*0.3, d*1.5); ax.axis('off')
    return fig

def plot_panel_load(pw, pd, orient, tw):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.add_patch(patches.Rectangle((0, 0), pw, pd, fill=False, edgecolor='black'))
    if orient == 'width':
        ax.axhline(pd*0.25, color='blue', ls='--'); ax.axhline(pd*0.75, color='blue', ls='--')
        ax.add_patch(patches.Rectangle((0, 0), pw, pd/2, color='red', alpha=0.2))
        ax.annotate('', xy=(pw+0.1, 0), xytext=(pw+0.1, pd/2), arrowprops=dict(arrowstyle='<->', color='red'))
        ax.text(pw+0.2, pd/4, f"Trib: {tw:.3f}m", color='red', rotation=90, va='center')
    else:
        ax.axvline(pw*0.25, color='blue', ls='--'); ax.axvline(pw*0.75, color='blue', ls='--')
        ax.add_patch(patches.Rectangle((0, 0), pw/2, pd, color='red', alpha=0.2))
        ax.annotate('', xy=(0, pd+0.1), xytext=(pw/2, pd+0.1), arrowprops=dict(arrowstyle='<->', color='red'))
        ax.text(pw/4, pd+0.2, f"Trib: {tw:.3f}m", color='red', ha='center')
    ax.set_xlim(-0.2, pw+0.5); ax.set_ylim(-0.2, pd+0.5); ax.axis('off')
    return fig

def plot_fem(res, zone):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(res['x'], res['shear'], 'b-'); ax1.fill_between(res['x'], res['shear'], color='blue', alpha=0.1)
    ax1.set_ylabel("Shear (kN)"); ax1.set_title(f"SFD - {zone}"); ax1.grid(True, ls=':')
    v_max = np.argmax(np.abs(res['shear'])); ax1.plot(res['x'][v_max], res['shear'][v_max], 'ro')
    ax1.annotate(f"V*={abs(res['shear'][v_max]):.2f}", xy=(res['x'][v_max], res['shear'][v_max]), xytext=(5,10), textcoords="offset points", color='red', fontweight='bold')
    
    ax2.plot(res['x'], res['moment'], 'r-'); ax2.fill_between(res['x'], res['moment'], color='red', alpha=0.1)
    ax2.set_ylabel("Moment (kNm)"); ax2.set_title(f"BMD - {zone}"); ax2.grid(True, ls=':')
    m_max = np.argmax(np.abs(res['moment'])); ax2.plot(res['x'][m_max], res['moment'][m_max], 'bo')
    ax2.annotate(f"M*={abs(res['moment'][m_max]):.2f}", xy=(res['x'][m_max], res['moment'][m_max]), xytext=(5,10), textcoords="offset points", color='blue', fontweight='bold')
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
        base_cpe, gov_case, note = res0['cpe'], f"Wind 0° (Normal) | h/d={r0:.2f}", "Wind 0° is critical"
    else:
        base_cpe, gov_case, note = res90['cpe'], f"Wind 90° (Parallel) | h/b={r90:.2f}", "Wind 90° is critical"

    zones = [{"code": "RA1", "desc": "General", "kl": 1.0}, {"code": "RA2", "desc": "Edges", "kl": 1.5}, 
             {"code": "RA3", "desc": "Corners", "kl": 2.0}, {"code": "RA4", "desc": "High Suction", "kl": 3.0}]
    
    results, worst_res, max_p = [], None, -1.0
    
    for z in zones:
        p_z = wind_load.calculate_wind_pressure(v_des, base_cpe, ka, kc, z['kl'])
        w_z = p_z * trib_width
        span, fem, history = structural.optimize_span(Mn, w_z, num_spans, max_span=4.0)
        
        rxn = np.abs(fem['reactions'])
        rxn_edge = fem['rxn_edge']
        rxn_int = fem['rxn_internal']
        mom, shr = fem['max_moment'], np.max(np.abs(fem['shear']))
        
        results.append({
            "Zone": z['code'], "Description": z['desc'], "Kl": z['kl'],
            "Pressure (kPa)": p_z, "Line Load (kN/m)": w_z, "Max Span (m)": span,
            "Reaction (kN)": np.max(rxn), "M* (kNm)": mom, "history": history
        })
        if p_z > max_p:
            max_p = p_z
            worst_res = {
                'zone': z['code'], 'pressure': p_z, 'span': span, 'fem': fem, 
                'load': w_z, 'moment': mom, 'shear_max': shr, 
                'reaction': np.max(rxn), 'rxn_edge': rxn_edge, 'rxn_int': rxn_int
            }

    st.session_state['results'] = results
    st.session_state['worst_res'] = worst_res
    st.session_state['wind_data'] = {'res0': res0, 'r0': r0, 'res90': res90, 'r90': r90, 'gov_case': gov_case, 'note': note, 'base_cpe': base_cpe, 'trib_width': trib_width}
    st.session_state['struct_data'] = {'Mn': Mn, 'break_load': breaking_load, 'test_span': test_span, 'sf': safety_factor}
    st.session_state['has_run'] = True

# ==========================================
# OUTPUT
# ==========================================
if 'has_run' in st.session_state and st.session_state['has_run']:
    res_list = st.session_state['results']
    w_res = st.session_state['worst_res']
    w_dat = st.session_state['wind_data']
    s_dat = st.session_state['struct_data']

    st.divider(); st.header("📊 Analysis Report Summary")
    
    # 1. Verification
    st.subheader("1. Detailed Input Verification")
    st.markdown('<div class="calculation-box">', unsafe_allow_html=True)
    st.markdown(f"**Design Wind Speed ($V_{{des}}$): {v_des:.2f} m/s**")
    st.markdown(f"- Formula: $V_R \cdot M_d \cdot (M_{{z,cat}} \cdot M_s \cdot M_t)$")
    st.markdown(f"- Subst: {vr} * {md} * ({mz_cat:.2f} * {ms} * {mt})")
    st.markdown('</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1: st.write(f"**Rail:** {rail_brand}"); st.write(f"**Mn:** {s_dat['Mn']:.3f} kNm")
    with c2: st.pyplot(plot_building_diagram(b_width, b_depth, roof_type))

    # 2. Wind
    st.divider(); st.subheader("2. Wind Analysis ($C_{p,e}$ Selection)")
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("#### External Pressure Coefficient ($C_{p,e}$)")
    w1, w2 = st.columns(2)
    with w1:
        st.write("**Case 1: Wind 0° (Normal)**")
        st.write(f"- h/d Ratio: {b_height}/{b_depth} = **{w_dat['r0']:.2f}**")
        st.write(f"- Cpe: **{w_dat['res0']['cpe']:.2f}**")
    with w2:
        st.write("**Case 2: Wind 90° (Parallel)**")
        st.write(f"- h/b Ratio: {b_height}/{b_width} = **{w_dat['r90']:.2f}**")
        st.write(f"- Cpe: **{w_dat['res90']['cpe']:.2f}**")
        
    st.warning(f"**Selected Governing Case:** {w_dat['gov_case']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    c_trib1, c_trib2 = st.columns([1, 1])
    with c_trib1:
        st.markdown("#### Load Parameters")
        st.write(f"- **Tributary Width:** {w_dat['trib_width']:.3f} m")
        st.write(f"- **Ka (Area Red.):** {ka}")
        st.write(f"- **Kc (Comb.):** {kc}")
    with c_trib2:
        st.pyplot(plot_panel_load(panel_w, panel_d, orient_key, w_dat['trib_width']))

    # 3. Table
    st.divider(); st.subheader("3. Zone Analysis Summary")
    df_res = pd.DataFrame(res_list)
    df_disp = df_res.drop(columns=['history'], errors='ignore')
    
    st.dataframe(
        df_disp[["Zone", "Pressure (kPa)", "Line Load (kN/m)", "Max Span (m)", "M* (kNm)", "Reaction (kN)"]]
        .style.format({
            "Pressure (kPa)": "{:.3f}",
            "Line Load (kN/m)": "{:.3f}",
            "Max Span (m)": "{:.2f}",
            "M* (kNm)": "{:.3f}",
            "Reaction (kN)": "{:.2f}"
        }),
        use_container_width=True
    )

    # 4. Critical
    st.divider(); st.subheader(f"4. Critical Case Analysis ({w_res['zone']})")
    
    col_crit1, col_crit2 = st.columns([1, 2])
    with col_crit1:
        st.markdown("### Design Values")
        st.metric("Max Span", f"{w_res['span']:.2f} m")
        st.metric("Design Moment (M*)", f"{w_res['moment']:.3f} kNm")
        
        st.markdown("---")
        st.markdown("### Reaction Forces")
        st.metric("Max End Reaction (Edge)", f"{w_res['rxn_edge']:.3f} kN")
        st.metric("Max Int. Reaction (Mid)", f"{w_res['rxn_int']:.3f} kN")
        
    with col_crit2:
        st.pyplot(plot_fem(w_res['fem'], w_res['zone']))

    # REPORT GENERATION
    st.divider(); st.header("📄 Plain Text & PDF Report")
    
    inp_d = {
        'project_name': project_name, 'project_location': project_loc, 'engineer': engineer_name,
        'rail_brand': rail_brand, 'rail_model': rail_model, 'region': region, 'imp_level': imp_level, 'design_life': design_life,
        'ret_period': ret_period, 'vr': vr, 'v_des': v_des, 'md': md, 'ms': ms, 'mt': mt, 'mz_cat': mz_cat, 'tc': tc,
        'b_width': b_width, 'b_depth': b_depth, 'b_height': b_height, 'roof_type': roof_type, 'roof_angle': roof_angle,
        'panel_w': panel_w, 'panel_d': panel_d, 'num_spans': num_spans
    }
    w_d = {
        'cpe_0': w_dat['res0']['cpe'], 'ratio_0': w_dat['r0'], 'cpe_90': w_dat['res90']['cpe'], 'ratio_90': w_dat['r90'],
        'governing_case': w_dat['gov_case'], 'note': w_dat['note'], 'trib_width': w_dat['trib_width'], 'ka': ka, 'kc': kc, 'cpe_base': w_dat['base_cpe']
    }
    
    rep_text = report.generate_full_report(inp_d, w_d, s_dat, res_list, w_res)
    
    # FILENAME GENERATION
    clean_proj_name = project_name.strip().replace(" ", "_") if project_name else "Solar_Project"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    fname = f"{clean_proj_name}_Report_{date_str}"

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button("💾 Download Text Report", rep_text, f"{fname}.txt")
    with col_d2:
        try:
            pdf_bytes = report.create_pdf_report(rep_text)
            st.download_button("💾 Download PDF Report", pdf_bytes, f"{fname}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"PDF Gen Error: {e} (Require fpdf2)")

    st.code(rep_text, language='text')
