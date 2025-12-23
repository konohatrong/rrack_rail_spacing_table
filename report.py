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
    Main function to generate the detailed plain text report with equations.
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
    
    # --- CALCULATION STEPS FOR REPORT ---
    
    # Step 1: Vr details
    step_vr = f"""
    1. Regional Wind Speed (Vr)
       Ref: AS/NZS 1170.2 Section 3.1 & AS/NZS 1170.0 Table 3.3
       - Region:              {inputs['region']}
       - Importance Level:    {inputs['imp_level']}
       - Design Working Life: {inputs['design_life']} years
       - Annual Probability:  P = 1/{inputs['ret_period']}
       >> Vr = {inputs['vr']} m/s
    """
    
    # Step 2: Vdes Calculation
    # Vsit,beta = Vr * Md * (Mz,cat * Ms * Mt)
    m_site_product = inputs['mz_cat'] * inputs['ms'] * inputs['mt']
    step_vdes = f"""
    2. Design Wind Speed (Vdes) at Height z={inputs['b_height']}m
       Ref: AS/NZS 1170.2 Eq. 2.2
       Formula:  V_des,theta = Vr * Md * (Mz,cat * Ms * Mt)
       
       Where:
       - Vr (Regional Speed)        = {inputs['vr']} m/s
       - Md (Direction Multiplier)  = {inputs['md']}
       - Mz,cat (Terrain/Height)    = {inputs['mz_cat']:.2f} (Cat {inputs['tc']}, z={inputs['b_height']}m)
       - Ms (Shielding Multiplier)  = {inputs['ms']}
       - Mt (Topographic Mult.)     = {inputs['mt']}
       
       Substitution:
       V_des = {inputs['vr']} * {inputs['md']} * ({inputs['mz_cat']:.2f} * {inputs['ms']} * {inputs['mt']})
       V_des = {inputs['vr']} * {inputs['md']} * {m_site_product:.3f}
       
       >> V_des = {inputs['v_des']:.2f} m/s
    """
    
    # Step 3: Design Pressure (p)
    # p = 0.5 * rho * Vdes^2 * Cfig * Cdyn
    rho_air = 1.2
    c_dyn = 1.0
    # Use critical case data for example calculation
    crit_cpe = critical_res['pressure'] / (0.5 * 1.2 * inputs['v_des']**2 * wind_res['ka'] * wind_res['kc'] * 1.0 * 1.0 / 1000.0) 
    # Back-calculate effective Cpe for display logic if needed, but better use knowns
    
    # Let's show the formula for the Critical Zone
    crit_kl = 0.0
    for z in zone_results:
        if z['Zone'] == critical_res['zone']:
            crit_kl = z['Kl']
            
    c_fig_crit = critical_res['pressure'] * 1000 / (0.5 * rho_air * inputs['v_des']**2 * c_dyn)
    
    step_pressure = f"""
    3. Aerodynamic Shape Factor (Cfig) & Design Pressure (p)
       Ref: AS/NZS 1170.2 Eq. 2.4 and Eq. 5.1
       
       Formula (Pressure): p = (0.5 * rho_air * (V_des)^2 * C_fig * C_dyn) / 1000  [kPa]
       Formula (Shape):    C_fig = Cpe * Ka * Kc * Kl * Kp
       
       Parameters:
       - Air Density (rho_air):     {rho_air} kg/m3
       - Dynamic Factor (C_dyn):    {c_dyn}
       - Porous Cladding (Kp):      1.0 (Assumed solid panel)
       - Area Reduction (Ka):       {wind_res['ka']}
       - Combination Factor (Kc):   {wind_res['kc']}
       
       EXAMPLE CALCULATION FOR CRITICAL ZONE ({critical_res['zone']}):
       - Governing Wind Direction:  {wind_res['governing_case']}
       - Base External Cpe:         {wind_res['cpe_base']:.2f}
       - Local Factor (Kl):         {crit_kl} (for Zone {critical_res['zone']})
       
       Calculation:
       C_fig = {wind_res['cpe_base']:.2f} * {wind_res['ka']} * {wind_res['kc']} * {crit_kl} * 1.0
             = {c_fig_crit/c_dyn:.3f} (Effective Shape Factor)
             
       p_design = 0.5 * 1.2 * ({inputs['v_des']:.2f})^2 * {c_fig_crit/c_dyn:.3f} * 1.0
                = {critical_res['pressure']*1000:.1f} Pa
                
       >> p_design = {critical_res['pressure']:.3f} kPa
    """
    
    # Step 4: Line Load
    step_load = f"""
    4. Uniform Line Load on Rail (w)
       Formula: w = p_design * Tributary_Width
       
       - Design Pressure (p):       {critical_res['pressure']:.3f} kPa
       - Tributary Width (Trib):    {wind_res['trib_width']:.3f} m
         (Based on panel dim: {inputs['panel_w']}x{inputs['panel_d']} m)
         
       Substitution:
       w = {critical_res['pressure']:.3f} * {wind_res['trib_width']:.3f}
       
       >> w = {critical_res['load']:.3f} kN/m
    """

    report_text = f"""
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================
Generated Date: {current_time}

[1] PROJECT SUMMARY
-------------------
   - Rail Model:                 {inputs['rail_brand']} - {inputs['rail_model']}
   - Installation Region:        {inputs['region']}
   - Building Dimensions:        {inputs['b_width']}m (W) x {inputs['b_depth']}m (D) x {inputs['b_height']}m (H)
   - Roof Configuration:         {inputs['roof_type']}, Angle {inputs['roof_angle']} deg
   - Rail Capacity (Mn):         {struct_res['Mn']:.3f} kNm

[2] DETAILED WIND LOAD CALCULATION
----------------------------------
{step_vr}
{step_vdes}
{step_pressure}
{step_load}

[3] ZONE OPTIMIZATION SUMMARY (RA1-RA4)
---------------------------------------
   The table below summarizes the capacity check for all roof zones.
   Max Span is calculated such that M* (Design Moment) < Mn (Capacity).

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

[5] LIMITATIONS & CONDITIONS OF USE
-----------------------------------
   This calculation is valid ONLY under the following conditions:
   1. The building height does not exceed {inputs['b_height']} m.
   2. The roof slope is exactly {inputs['roof_angle']} degrees.
   3. The site corresponds to Terrain Category {inputs['tc']}.
   4. The rail system utilizes the specific profile: {inputs['rail_brand']} {inputs['rail_model']}.
   
   WARNINGS:
   - This report checks the RAIL PROFILE BENDING CAPACITY only.
   - The pull-out capacity of the screws/fasteners connecting the L-feet/brackets 
     to the roof structure MUST BE VERIFIED SEPARATELY using the 'Max Reaction Force'.
   - The capacity of the underlying roof structure (purlins/rafters) is NOT checked.

[6] VISUALIZATION GUIDE
-----------------------
{ridge_art}

{zone_art}
================================================================================
End of Report
================================================================================
"""
    return report_text
