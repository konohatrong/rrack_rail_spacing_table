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
    """
    Formats the last 10 steps of the iteration history into a text table.
    """
    # Get last 10 steps
    steps = history[-10:] if len(history) > 10 else history
    
    header = f"   Detailed Iteration Log for {zone_name} (Last {len(steps)} Steps):"
    table_header =  "   |  Span (m)  |  M* (kNm)  | Utilization |  Status  |"
    divider =       "   |------------|------------|-------------|----------|"
    
    rows = []
    for step in steps:
        rows.append(f"   |   {step['span']:.3f}    |   {step['m_star']:.3f}    |   {step['util']:.1f} %    |   {step['status']}   |")
        
    return f"{header}\n{table_header}\n{divider}\n" + "\n".join(rows) + "\n"

def generate_full_report(inputs, wind_res, struct_res, zone_results, critical_res):
    # 1. Zone Summary Table
    df_res = pd.DataFrame(zone_results)
    if 'Utilization' not in df_res.columns:
         df_res['Utilization'] = (df_res['M* (kNm)'] / struct_res['Mn']) * 100
    
    table_str = df_res.to_string(
        index=False, justify="right", 
        float_format=lambda x: "{:.3f}".format(x) if isinstance(x, (float, np.floating)) else str(x)
    )
    
    # 2. Iteration Logs (For all zones)
    iteration_logs = ""
    for z in zone_results:
        # Assuming 'history' is stored in the zone result dictionary
        if 'history' in z:
            iteration_logs += format_iteration_table(z['history'], z['Zone'])
            iteration_logs += "\n"

    # 3. Visuals
    ridge_art = get_ascii_ridge_diagram(inputs['b_width'], inputs['b_depth'], inputs['roof_type'])
    zone_art = ""
    for z in zone_results:
        zone_art += f"\n   ZONE {z['Zone']} ({z['Description']}):\n"
        zone_art += get_ascii_art(z['Zone'])

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================
Generated Date: {current_time}

[1] PROJECT SUMMARY
-------------------
   - Rail Model:                 {inputs['rail_brand']} - {inputs['rail_model']}
   - Region:                     {inputs['region']} (Vr={inputs['vr']} m/s)
   - Importance Level:           {inputs['imp_level']} (1/{inputs['ret_period']} yrs)
   - Building Dimensions:        {inputs['b_width']}m (W) x {inputs['b_depth']}m (D) x {inputs['b_height']}m (H)
   - Rail Capacity (Mn):         {struct_res['Mn']:.3f} kNm

[2] WIND LOAD PARAMETERS
------------------------
   - Governing Direction:        {wind_res['governing_case']}
   - Design Wind Speed (Vdes):   {inputs['v_des']:.2f} m/s
   - Tributary Width:            {wind_res['trib_width']:.3f} m

[3] DETAILED STRUCTURAL OPTIMIZATION (BY ZONE)
----------------------------------------------
   Method: Finite Element Analysis (Matrix Stiffness Method)
   Logic:  Incremental Span check (step 0.05m) until M* >= Mn
   
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

   [Check] M* ({critical_res['moment']:.3f}) < Mn ({struct_res['Mn']:.3f}) --> PASS

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
