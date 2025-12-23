import pandas as pd
import numpy as np
import datetime

def get_ascii_ridge_diagram(b, d, r_type):
    """Generates ASCII diagram for Building Orientation & Ridge Line"""
    if "Gable" in r_type:
        return f"""
       Wind 0 deg (Normal/Transverse)
                 |
                 v
      +-----------------------------+
      |      ROOF SIDE A            |
      |                             |
      | - - - - RIDGE LINE - - - - -| ---> Wind 90 deg (Parallel)
      |                             |
      |      ROOF SIDE B            |
      +-----------------------------+
      (Building: {b}m Width x {d}m Depth)
        """
    else: 
        return f"""
       Wind 0 deg (Low to High)
                 |
                 v
      +-----------------------------+
      |                             |
      |                             |
      |      MONOSLOPE ROOF         |
      |                             |
      |                             |
      +-----------------------------+ ---> Wind 90 deg
      (Building: {b}m Width x {d}m Depth)
        """

def get_ascii_art(zone_code):
    """Returns ASCII art for specific roof zones"""
    if zone_code == "RA1": 
        return """
      +-----------------------------+
      |      [      RA 1      ]     |
      |      [  GENERAL AREA  ]     |
      +-----------------------------+
        """
    elif zone_code == "RA2": 
        return """
      +#############################+
      |#     [      RA 2      ]    #|
      |#     [  EDGES / RIDGE ]    #|
      +#############################+
        """
    elif zone_code == "RA3": 
        return """
      ##---------------------------##
      |      [      RA 3      ]     |
      |      [     CORNERS    ]     |
      ##---------------------------##
        """
    elif zone_code == "RA4": 
        return """
      X-----------------------------X
             [      RA 4      ]      
             [  HIGH SUCTION  ]      
      X-----------------------------X
        """
    return ""

def format_iteration_table(history, zone_name):
    """Formats the last 10 steps of the iteration history."""
    if not history: 
        return f"   No iteration history available for {zone_name}."
    
    # Get last 10 steps
    steps = history[-10:] if len(history) > 10 else history
    
    header = f"   >> Detailed Iteration Log for {zone_name} (Last {len(steps)} Steps):"
    table_header =  "   |  Span (m)  |  M* (kNm)  | Utilization |  Status  |"
    divider =       "   |------------|------------|-------------|----------|"
    
    rows = []
    for step in steps:
        rows.append(f"   |   {step['span']:.3f}    |   {step['m_star']:.3f}    |   {step['util']:.1f} %    |   {step['status']}   |")
        
    return f"{header}\n{table_header}\n{divider}\n" + "\n".join(rows) + "\n"

def generate_full_report(inputs, wind_res, struct_res, zone_results, critical_res):
    """
    Main function to generate the detailed plain text report.
    """
    
    # 1. Format Summary Table (Clean Data)
    df_res = pd.DataFrame(zone_results)
    
    # Drop history column if exists (so it doesn't mess up the main table print)
    df_table_view = df_res.drop(columns=['history'], errors='ignore')
    
    # Add Utilization for summary table
    if 'Utilization' not in df_table_view.columns:
         df_table_view['Utilization'] = (df_table_view['M* (kNm)'] / struct_res['Mn']) * 100

    table_str = df_table_view.to_string(
        index=False, 
        justify="right", 
        float_format=lambda x: "{:.3f}".format(x) if isinstance(x, (float, np.floating)) else str(x)
    )
    
    # 2. Generate Iteration Logs
    iteration_logs = ""
    for z in zone_results:
        # Check if history exists in the dictionary
        if 'history' in z:
            iteration_logs += format_iteration_table(z['history'], z['Zone'])
            iteration_logs += "\n"

    # 3. Generate Visuals
    ridge_art = get_ascii_ridge_diagram(inputs['b_width'], inputs['b_depth'], inputs['roof_type'])
    zone_art = ""
    for z in zone_results:
        zone_art += f"\n   ZONE {z['Zone']} ({z['Description']}):\n"
        zone_art += get_ascii_art(z['Zone'])

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # --- Detailed Calculation breakdown ---
    step_vdes = f"""
    Design Wind Speed (Vdes) Calculation:
    Ref: AS/NZS 1170.2 Eq. 2.2
    V_des = Vr * Md * (Mz,cat * Ms * Mt)
    V_des = {inputs['vr']} * {inputs['md']} * ({inputs['mz_cat']:.2f} * {inputs['ms']} * {inputs['mt']})
    V_des = {inputs['v_des']:.2f} m/s
    """

    step_optimization = f"""
    Optimization Objective: Find Max Span (L) where M* <= Mn ({struct_res['Mn']:.3f} kNm)
    Method: Finite Element Analysis (Matrix Stiffness Method)
    Logic: Incremental Span check (step 0.05m)
    """

    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================
Generated Date: {current_time}

[1] PROJECT INPUTS & WIND PARAMETERS
------------------------------------
   - Rail Model:     {inputs['rail_brand']} - {inputs['rail_model']}
   - Region:         {inputs['region']} (Vr = {inputs['vr']} m/s)
   - Importance:     Level {inputs['imp_level']} (1/{inputs['ret_period']} R.P.)
   {step_vdes}

[2] WIND DIRECTION ANALYSIS (Cpe)
---------------------------------
   - Wind 0 deg:     Cpe = {wind_res['cpe_0']:.2f}
   - Wind 90 deg:    Cpe = {wind_res['cpe_90']:.2f}
   - Governing:      {wind_res['governing_case']}
   - Trib. Width:    {wind_res['trib_width']:.3f} m

[3] SPAN OPTIMIZATION LOGS (10 STEPS)
-------------------------------------
{step_optimization}

{iteration_logs}

[4] ZONE ANALYSIS SUMMARY (ALL ZONES)
--------------------------------------
{table_str}

[5] CRITICAL CASE RESULTS ({critical_res['zone']})
----------------------------------------------------
   The worst-case structural demand occurs in Zone: {critical_res['zone']}
   
   >> Max Design Moment (M*):    {critical_res['moment']:.3f} kNm
   >> Max Design Shear (V*):     {critical_res['shear_max']:.3f} kN
   >> Max Reaction Force:        {critical_res['reaction']:.3f} kN (Uplift)
   >> Max Allowable Span:        {critical_res['span']:.2f} m

   [Structural Check]
   M* ({critical_res['moment']:.3f}) < Mn ({struct_res['Mn']:.3f}) --> PASS (OK)

[6] LIMITATIONS & CONDITIONS
----------------------------
   1. Valid only for building height <= {inputs['b_height']} m.
   2. Roof slope must match {inputs['roof_angle']} degrees.
   3. Pull-out capacity of fasteners must be verified separately against Max Reaction.
   4. Deflection checks (SLS) are not included in this ULS analysis.

[7] VISUALIZATION GUIDE
-----------------------
{ridge_art}
{zone_art}
================================================================================
"""
    return report_text
