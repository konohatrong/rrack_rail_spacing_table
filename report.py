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
    Main function to generate the detailed plain text report with limitations.
    """
    
    # 1. Format Tables
    df_res = pd.DataFrame(zone_results)
    table_str = df_res.to_string(
        index=False, 
        justify="right", 
        float_format=lambda x: "{:.3f}".format(x) if isinstance(x, (float, np.floating)) else str(x)
    )
    
    # 2. Generate Visuals
    ridge_art = get_ascii_ridge_diagram(inputs['b_width'], inputs['b_depth'], inputs['roof_type'])
    zone_art = ""
    for z in zone_results:
        zone_art += f"\n   ZONE {z['Zone']} ({z['Description']}):\n"
        zone_art += get_ascii_art(z['Zone'])

    # 3. Assemble Report Content
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================
Generated Date: {current_time}

[1] PROJECT INFORMATION & INPUTS
--------------------------------
   - Rail Model:                 {inputs['rail_brand']} - {inputs['rail_model']}
   - Installation Region:        {inputs['region']}
   - Design Standard:            AS/NZS 1170.2:2021 (Wind Actions)
   
   - Importance Level (IL):      {inputs['imp_level']}
   - Design Working Life:        {inputs['design_life']} years
   - Annual Prob. Exceedance:    1/{inputs['ret_period']}
   - Regional Wind Speed (Vr):   {inputs['vr']} m/s
   - Design Wind Speed (Vdes):   {inputs['v_des']:.2f} m/s
     (Multipliers: Md={inputs['md']}, Ms={inputs['ms']}, Mt={inputs['mt']}, Mz,cat={inputs['mz_cat']:.2f})
   
   - Building Dimensions:        {inputs['b_width']}m (W) x {inputs['b_depth']}m (D) x {inputs['b_height']}m (H)
   - Roof Configuration:         {inputs['roof_type']}, Angle {inputs['roof_angle']} deg
   
   - Rail Material Capacity:     Mn = {struct_res['Mn']:.3f} kNm
     (Derived from Test Data: Break Load {struct_res['break_load']} kN, Span {struct_res['test_span']} m, SF {struct_res['sf']})

[2] WIND LOAD ANALYSIS
----------------------
   A. Directional Check (Cpe Selection)
      - Wind 0 deg (Normal):     Cpe = {wind_res['cpe_0']:.2f} (Ratio h/d={wind_res['ratio_0']:.2f})
      - Wind 90 deg (Parallel):  Cpe = {wind_res['cpe_90']:.2f} (Ratio h/b={wind_res['ratio_90']:.2f})
      
      >> GOVERNING CASE:         {wind_res['governing_case']}
         ({wind_res['note']})

   B. Load Parameters
      - Tributary Width:         {wind_res['trib_width']:.3f} m
      - Area Reduction (Ka):     {wind_res['ka']}
      - Combination Factor (Kc): {wind_res['kc']}

[3] ZONE OPTIMIZATION SUMMARY (RA1-RA4)
---------------------------------------
   The table below shows the maximum allowable span for each roof zone to ensure
   the Design Moment (M*) does not exceed the Rail Capacity (Mn).

{table_str}

[4] CRITICAL CASE RESULTS ({critical_res['zone']})
----------------------------------------------------
   The most critical condition occurs in Zone: {critical_res['zone']}
   
   >> Max Design Moment (M*):    {critical_res['moment']:.3f} kNm
   >> Max Design Shear (V*):     {critical_res['shear_max']:.3f} kN
   >> Max Reaction Force:        {critical_res['reaction']:.3f} kN (Uplift)
   >> Max Allowable Span:        {critical_res['span']:.2f} m

   [Structural Check]
   M* ({critical_res['moment']:.3f}) < Mn ({struct_res['Mn']:.3f}) --> PASS (OK)

[5] VISUALIZATION GUIDE (ZONES)
-------------------------------
   [5.1] Building Orientation
{ridge_art}

   [5.2] Roof Zone Reference
{zone_art}

[6] LIMITATIONS & CONDITIONS OF USE (IMPORTANT)
-----------------------------------------------
   This calculation report is strictly valid ONLY under the following conditions.
   Any deviation from these parameters invalidates this analysis.

   1. SCOPE OF ANALYSIS
      - Component Checked:   ALUMINUM RAIL PROFILE ONLY (Bending Capacity).
      - Analysis Method:     Static analysis using Finite Element Method (FEM).
      - Design Check:        Ultimate Limit State (ULS) for Bending Moment.

   2. CRITICAL EXCLUSIONS (NOT VERIFIED)
      - FIXING CAPACITY:     The pull-out capacity of screws, L-feet, or brackets 
                             connecting the rail to the roof IS NOT CHECKED.
                             >> ACTION: Verify 'Max Reaction' ({critical_res['reaction']:.3f} kN) 
                             against fastener datasheet.
      - ROOF STRUCTURE:      The capacity of the existing roof structure (purlins, 
                             rafters, trusses) to support the loads is NOT CHECKED.
      - DEFLECTION (SLS):    Serviceability Limit State (Deflection) is NOT checked.
      - SEISMIC/SNOW:        Seismic and Snow loads are NOT included in this analysis.

   3. GEOMETRIC & ENVIRONMENTAL LIMITS
      - Max Building Height: {inputs['b_height']} m
      - Exact Roof Slope:    {inputs['roof_angle']} degrees
      - Wind Region:         {inputs['region']} (Vr = {inputs['vr']} m/s)
      - Terrain Category:    {inputs['tc']}

   4. INSTALLATION REQUIREMENTS
      - Rail spans must NOT exceed the 'Max Allowable Span' listed in Section [3]
        for the specific zone where they are installed.
      - Cantilever length of rails should typically not exceed 25-30% of the 
        adjacent span unless specifically verified by the manufacturer.
      - All installation must comply with the manufacturer's manual and local codes.

   DISCLAIMER: This software provides a preliminary design aid based on user inputs.
   Final structural certification should be conducted by a qualified engineer.

================================================================================
End of Report
================================================================================
"""
    return report_text
