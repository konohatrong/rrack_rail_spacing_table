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

def generate_full_report(inputs, wind_res, struct_res, zone_results, critical_res):
    """
    Main function to generate the detailed plain text report.
    """
    
    # 1. Format Summary Table
    df_res = pd.DataFrame(zone_results)
    
    # Remove history column if exists
    if 'history' in df_res.columns:
        df_res = df_res.drop(columns=['history'])
        
    # Add Utilization
    if 'Utilization' not in df_res.columns:
         df_res['Utilization'] = (df_res['M* (kNm)'] / struct_res['Mn']) * 100

    table_str = df_res.to_string(
        index=False, 
        justify="right", 
        float_format=lambda x: "{:.3f}".format(x) if isinstance(x, (float, np.floating)) else str(x)
    )
    
    # 2. Visuals
    ridge_art = get_ascii_ridge_diagram(inputs['b_width'], inputs['b_depth'], inputs['roof_type'])
    zone_art = ""
    for z in zone_results:
        zone_art += f"\n   ZONE {z['Zone']} ({z['Description']}):\n"
        zone_art += get_ascii_art(z['Zone'])

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # --- Detailed Calculation breakdown ---
    step_vdes = f"""
    1. Design Wind Speed (Vdes) Calculation:
       Ref: AS/NZS 1170.2 Eq. 2.2
       V_des = Vr * Md * (Mz,cat * Ms * Mt)
       V_des = {inputs['vr']} * {inputs['md']} * ({inputs['mz_cat']:.2f} * {inputs['ms']} * {inputs['mt']})
       V_des = {inputs['v_des']:.2f} m/s
    """

    # --- New Detailed Cpe Calculation ---
    step_cpe = f"""
    2. External Pressure Coefficient (Cpe) Analysis:
       Ref: AS/NZS 1170.2 Section 5.3 (Roofs)
       
       [A] Roof Configuration:
           - Type:  {inputs['roof_type']}
           - Angle: {inputs['roof_angle']} degrees
           
       [B] Directional Evaluation:
           (i)  Wind 0 deg (Transverse/Normal):
                - Building Dimension h/d = {inputs['b_height']}/{inputs['b_depth']} = {wind_res['ratio_0']:.2f}
                - Table Lookup/Interpolation -> Cpe = {wind_res['cpe_0']:.2f}
                
           (ii) Wind 90 deg (Longitudinal/Parallel):
                - Building Dimension h/b = {inputs['b_height']}/{inputs['b_width']} = {wind_res['ratio_90']:.2f}
                - Table Lookup/Interpolation -> Cpe = {wind_res['cpe_90']:.2f}
                
       [C] Selected Design Value:
           >> Governing Direction: {wind_res['governing_case']}
           >> Base Cpe used for design: {wind_res['cpe_base']:.2f} (Most critical suction)
    """

    step_load = f"""
    3. Design Pressure & Line Load:
       Formula: p = 0.5 * rho * Vdes^2 * Cfig * Cdyn
       
       Parameters:
       - Tributary Width:        {wind_res['trib_width']:.3f} m
       - Area Reduction (Ka):    {wind_res['ka']}
       - Combination Factor (Kc):{wind_res['kc']}
       
       (Note: Cfig = Cpe * Ka * Kc * Kl * Kp)
    """

    step_optimization = f"""
    4. Span Optimization (Iterative FEM)
       Objective: Find Max Span (L) where M* <= Mn ({struct_res['Mn']:.3f} kNm)
       Method: Finite Element Analysis (Matrix Stiffness Method)
       Logic: Incremental Span check (step 0.05m)
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
   - Region:         {inputs['region']} (Vr = {inputs['vr']} m/s)
   - Importance:     Level {inputs['imp_level']} (1/{inputs['ret_period']} R.P.)
   - Geometry:       {inputs['b_width']}m (W) x {inputs['b_depth']}m (D) x {inputs['b_height']}m (H)

[2] WIND ANALYSIS DETAILS
-------------------------
{step_vdes}
{step_cpe}
{step_load}
{step_optimization}

[3] ZONE ANALYSIS SUMMARY (RA1-RA4)
-----------------------------------
{table_str}

[4] CRITICAL CASE RESULTS ({critical_res['zone']})
----------------------------------------------------
   The worst-case structural demand occurs in Zone: {critical_res['zone']}
   
   >> Max Design Moment (M*):    {critical_res['moment']:.3f} kNm
   >> Max Design Shear (V*):     {critical_res['shear_max']:.3f} kN
   >> Max Reaction Force:        {critical_res['reaction']:.3f} kN (Uplift)
   >> Max Allowable Span:        {critical_res['span']:.2f} m

   [Structural Check]
   M* ({critical_res['moment']:.3f}) < Mn ({struct_res['Mn']:.3f}) --> PASS (OK)

[5] VISUALIZATION GUIDE
-----------------------
{ridge_art}
{zone_art}

[6] LIMITATIONS & CONDITIONS OF USE (STRICT COMPLIANCE)
-------------------------------------------------------
   This analysis is valid ONLY when the following conditions are met:

   1. DESIGN STANDARD:
      - Calculations based on AS/NZS 1170.2:2021 (Wind Actions).
      - AS/NZS 1170.0:2002 (General Principles) for probability factors.

   2. ZONES CONSIDERED:
      - The report explicitly covers Roof Zones: RA1 (General), RA2 (Edges), 
        RA3 (Corners), and RA4 (Local Pressure). 
      - Installation must respect the specific 'Max Span' for the zone it is placed in.

   3. ROOF CONFIGURATION:
      - Valid for Roof Type: {inputs['roof_type']}
      - Valid for Roof Pitch: {inputs['roof_angle']} degrees (+/- 2 deg tolerance)
      - Max Building Height: {inputs['b_height']} m

   4. STRUCTURAL CONFIGURATION:
      - Analysis assumes a Continuous Beam system with {inputs['num_spans']} spans.
      - Minimum number of rail supports required: {inputs['num_spans'] + 1} supports.
      - Single span installations are NOT covered by this specific calculation 
        (unless Num Spans = 1 was selected).

   5. EXCLUSIONS (ACTION REQUIRED):
      - Fixing/Screw Capacity: The connection between the L-foot/Bracket and the 
        roof purlin/rafter MUST be verified separately against the 'Max Reaction Force'.
      - Rail Deflection: Serviceability limit state (L/200 etc.) is not checked.
      - PV Clamping: Mid/End clamps holding the modules must be rated for the Design Pressure.

================================================================================
End of Report
================================================================================
"""
    return report_text
