import pandas as pd
import numpy as np
import datetime

def get_ascii_ridge_diagram(b, d, r_type):
    if "Gable" in r_type:
        return f"""
       Wind 0 deg (Normal)
             |
             v
      +-----------------------------+
      |      ROOF SIDE A            |
      | - - - - RIDGE LINE - - - - -| ---> Wind 90 deg
      |      ROOF SIDE B            |
      +-----------------------------+
      (Building: {b}m W x {d}m D)
        """
    else: 
        return f"""
       Wind 0 deg
             |
             v
      +-----------------------------+
      |      MONOSLOPE ROOF         |
      +-----------------------------+ ---> Wind 90 deg
      (Building: {b}m W x {d}m D)
        """

def get_ascii_art(zone_code):
    if zone_code == "RA1": return "[ RA 1: GENERAL AREA ]"
    elif zone_code == "RA2": return "[ RA 2: EDGES / RIDGE ]"
    elif zone_code == "RA3": return "[ RA 3: CORNERS ]"
    elif zone_code == "RA4": return "[ RA 4: HIGH SUCTION ]"
    return ""

def format_iteration_table(history, zone_name):
    """Formats the last 10 steps of the iteration history."""
    if not history or len(history) == 0: 
        return f"   [No iteration history recorded for {zone_name}]"
    
    # Get last 10 steps
    steps = history[-10:]
    
    header = f"   >> Iteration Log for {zone_name} (Last {len(steps)} Steps):"
    table_header =  "   |  Span (m)  |  M* (kNm)  | Util (%) | Status |"
    divider =       "   |------------|------------|----------|--------|"
    
    rows = []
    for step in steps:
        # Ensure values exist and handle formatting safely
        sp = step.get('span', 0.0)
        ms = step.get('m_star', 0.0)
        ut = step.get('util', 0.0)
        st = step.get('status', '-')
        rows.append(f"   |   {sp:.3f}    |   {ms:.3f}    |   {ut:.1f}   |   {st}   |")
        
    return f"{header}\n{table_header}\n{divider}\n" + "\n".join(rows) + "\n"

def generate_full_report(inputs, wind_res, struct_res, zone_results, critical_res):
    
    # 1. Format Summary Table (Clean Data)
    df_res = pd.DataFrame(zone_results)
    
    # Drop history for clean main table
    if 'history' in df_res.columns:
        df_res = df_res.drop(columns=['history'])
        
    if 'Utilization' not in df_res.columns:
         df_res['Utilization'] = (df_res['M* (kNm)'] / struct_res['Mn']) * 100

    table_str = df_res.to_string(
        index=False, justify="right", 
        float_format=lambda x: "{:.3f}".format(x) if isinstance(x, (float, np.floating)) else str(x)
    )
    
    # 2. Generate Iteration Logs
    iteration_logs = ""
    for z in zone_results:
        # Check if history exists
        hist = z.get('history', [])
        iteration_logs += format_iteration_table(hist, z.get('Zone', 'Unknown'))
        iteration_logs += "\n"

    # 3. Visuals
    ridge_art = get_ascii_ridge_diagram(inputs['b_width'], inputs['b_depth'], inputs['roof_type'])
    zone_art = ""
    for z in zone_results:
        zone_art += f"\n   ZONE {z.get('Zone')} ({z.get('Description')}):\n"
        zone_art += get_ascii_art(z.get('Zone'))

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # --- Detailed Calculations ---
    step_vdes = f"""
    1. Design Wind Speed (Vdes) Verification:
       Ref: AS/NZS 1170.2 Eq. 2.2
       Formula: V_des = Vr * Md * (Mz,cat * Ms * Mt)
       
       Substitution:
       - Vr (Region {inputs['region']}, R=1/{inputs['ret_period']}): {inputs['vr']} m/s
       - Md (Direction): {inputs['md']}
       - Mz,cat (Cat {inputs['tc']}, z={inputs['b_height']}m): {inputs['mz_cat']:.2f}
       - Ms (Shielding): {inputs['ms']}
       - Mt (Topographic): {inputs['mt']}
       
       Calculation:
       V_des = {inputs['vr']} * {inputs['md']} * ({inputs['mz_cat']:.2f} * {inputs['ms']} * {inputs['mt']})
             = {inputs['v_des']:.2f} m/s
    """

    step_cpe = f"""
    2. External Pressure Coefficient (Cpe) Selection:
       Ref: AS/NZS 1170.2 Section 5.3
       Roof Type: {inputs['roof_type']} (Angle: {inputs['roof_angle']} deg)
       
       [Check 1] Wind 0 deg (Normal to Ridge):
       - Ratio h/d = {inputs['b_height']}/{inputs['b_depth']} = {wind_res['ratio_0']:.2f}
       - Interpolated Cpe = {wind_res['cpe_0']:.2f}
       
       [Check 2] Wind 90 deg (Parallel to Ridge):
       - Ratio h/b = {inputs['b_height']}/{inputs['b_width']} = {wind_res['ratio_90']:.2f}
       - Interpolated Cpe = {wind_res['cpe_90']:.2f}
       
       >> GOVERNING CASE: {wind_res['governing_case']}
       >> BASE Cpe: {wind_res['cpe_base']:.2f}
    """

    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================
Generated Date: {current_time}

[1] PROJECT INPUTS
------------------
   - Rail Model:     {inputs['rail_brand']} - {inputs['rail_model']}
   - Geometry:       {inputs['b_width']}m (W) x {inputs['b_depth']}m (D) x {inputs['b_height']}m (H)
   - Roof:           {inputs['roof_type']} @ {inputs['roof_angle']} deg
   - Rail Capacity:  Mn = {struct_res['Mn']:.3f} kNm

[2] WIND ANALYSIS DETAILS
-------------------------
{step_vdes}
{step_cpe}
    3. Design Pressure & Load:
       - Tributary Width: {wind_res['trib_width']:.3f} m
       - Area Reduction (Ka): {wind_res['ka']}
       - Comb. Factor (Kc): {wind_res['kc']}
       
       p_design = 0.5 * 1.2 * V_des^2 * Cpe * Ka * Kc * Kl
       w_rail   = p_design * Tributary_Width

[3] SPAN OPTIMIZATION LOGS (LAST 10 STEPS)
------------------------------------------
   Method: Finite Element Analysis (Matrix Stiffness)
   Objective: Find Span L where M* <= Mn
   
{iteration_logs}

[4] SUMMARY OF RESULTS (ALL ZONES)
----------------------------------
{table_str}

[5] CRITICAL CASE RESULTS ({critical_res['zone']})
----------------------------------------------------
   The worst-case structural demand occurs in Zone: {critical_res['zone']}
   
   >> Max Design Moment (M*):    {critical_res['moment']:.3f} kNm
   >> Max Design Shear (V*):     {critical_res['shear_max']:.3f} kN
   >> Max Reaction Force:        {critical_res['reaction']:.3f} kN
   >> Max Allowable Span:        {critical_res['span']:.2f} m

   [Safety Check]
   M* ({critical_res['moment']:.3f}) <= Mn ({struct_res['Mn']:.3f}) --> PASS

[6] LIMITATIONS & CONDITIONS OF USE
-----------------------------------
   1. Valid Scope:
      - Zones: RA1, RA2, RA3, RA4.
      - Design Standard: AS/NZS 1170.2:2021.
      - Configuration: Continuous beam with {inputs['num_spans']} spans.
      
   2. Geometric Limits:
      - Max Height: {inputs['b_height']} m.
      - Roof Angle: {inputs['roof_angle']} deg.
      
   3. Exclusions:
      - This report DOES NOT verify the roof structure capacity.
      - Fastener Pull-out capacity must be checked against Max Reaction ({critical_res['reaction']:.3f} kN).

[7] VISUALIZATION GUIDE
-----------------------
{ridge_art}
{zone_art}
================================================================================
"""
    return report_text
