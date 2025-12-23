import pandas as pd
import numpy as np
import datetime
from fpdf import FPDF

# ==========================================
# ASCII ART ASSETS
# ==========================================
def get_report_logo():
    """
    Returns the custom ASCII Art Logo from ascii-art.txt
    """
    return r"""
                                                                                                                       
      ..:::::::-:..    .-----::.          .--.          ..:---:....-:.     ::..   .:---:...:::.     
       :**********+.   .@#++++#@#.       .*@@-.      .:*@%#+++#%- :@*.   .*@=.  .#%*=-=**..-:.:     
       :***=:::+****.  :@+    ..@#.      -@-*@.     .#@=..        :@*.  -@*.   .@=.       .+.=:     
       :***=  ..****:..:@+.     #@      :%#.:%#.    *@:.          :@* .#%:.    .@#.         ..      
       ........=***+...:@+    .=@-      *%.  =@-  .:@-.           :@*=@-        -@%-.               
       :**********=.  .:@%##%@%=.     .=@-.  .*@. .-@:            :@@@*.         .:#@@+:..          
       :****+****=.   .:@=...*@=      :%%=----=%#. :@-            :@+.#@-           ..=@#.          
       :***= .=****.   :@=   .=@+.   .*@======-+@-  *%.           :@+..-@#.            :@+          
       :***=  .-****:..-@=    .+@=.  =@=        #@. .#%-..      ..:@+.  .*@=.. ...    .-@=          
       :***=    :****:.-@=      +@+.:%#.        :@#. .:%@@*+=+%@-.:@+.    :@%: :@@*==+%%-           
      ......    ..........      .......         ....    ...::...  ....     ....  ......             
                                                                                            
    """

def get_ascii_ridge_diagram(b, d, r_type):
    if "Gable" in r_type:
        return f"""
       Wind 0 deg (Normal/Transverse)
                 |
                 v
      +-----------------------------+
      |      ROOF SIDE A            |
      | - - - - RIDGE LINE - - - - -| ---> Wind 90 deg (Parallel)
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
      |      MONOSLOPE ROOF         |
      +-----------------------------+ ---> Wind 90 deg
      (Building: {b}m Width x {d}m Depth)
        """

def get_ascii_art(zone_code):
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
    if not history or len(history) == 0: 
        return f"   [No iteration history recorded for {zone_name}]"
    
    # Get last 10 steps
    steps = history[-10:]
    
    header = f"   >> Iteration Log for {zone_name} (Last {len(steps)} Steps):"
    table_header =  "   |  Span (m)  |  M* (kNm)  | Util (%) | Status |"
    divider =       "   |------------|------------|----------|--------|"
    
    rows = []
    for step in steps:
        sp = step.get('span', 0.0); ms = step.get('m_star', 0.0)
        ut = step.get('util', 0.0); st = step.get('status', '-')
        rows.append(f"   |   {sp:.3f}    |   {ms:.3f}    |   {ut:.1f}   |   {st}   |")
    return f"{header}\n{table_header}\n{divider}\n" + "\n".join(rows) + "\n"

# ==========================================
# MAIN REPORT GENERATOR
# ==========================================
def generate_full_report(inputs, wind_res, struct_res, zone_results, critical_res):
    
    # 1. Format Tables
    df_res = pd.DataFrame(zone_results)
    df_clean = df_res.drop(columns=['history'], errors='ignore')
    if 'Utilization' not in df_clean.columns:
         df_clean['Utilization'] = (df_clean['M* (kNm)'] / struct_res['Mn']) * 100

    table_str = df_clean.to_string(index=False, justify="right", float_format=lambda x: "{:.3f}".format(x) if isinstance(x, (float, np.floating)) else str(x))
    
    # 2. Generate Iteration Logs
    iteration_logs = ""
    for z in zone_results:
        hist = z.get('history', [])
        iteration_logs += format_iteration_table(hist, z.get('Zone', 'Unknown')) + "\n"

    # 3. Visuals
    ridge_art = get_ascii_ridge_diagram(inputs['b_width'], inputs['b_depth'], inputs['roof_type'])
    zone_art = ""
    for z in zone_results:
        zone_art += f"\n   ZONE {z.get('Zone')} ({z.get('Description')}):\n" + get_ascii_art(z.get('Zone'))

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logo = get_report_logo()

    # --- Detailed Calculation breakdown ---
    step_vdes = f"""
    1. Design Wind Speed (Vdes) Calculation:
       Ref: AS/NZS 1170.2 Eq. 2.2
       Formula: V_des = Vr * Md * (Mz,cat * Ms * Mt)
       
       Substitution:
       - Vr (Region {inputs['region']}, R=1/{inputs['ret_period']}yr): {inputs['vr']} m/s
       - Md (Direction): {inputs['md']}
       - Mz,cat (Cat {inputs['tc']}, z={inputs['b_height']}m): {inputs['mz_cat']:.2f}
       - Ms (Shielding): {inputs['ms']}
       - Mt (Topographic): {inputs['mt']}
       
       Calculation:
       V_des = {inputs['vr']} * {inputs['md']} * ({inputs['mz_cat']:.2f} * {inputs['ms']} * {inputs['mt']})
             = {inputs['v_des']:.2f} m/s
    """

    step_cpe = f"""
    2. External Pressure Coefficient (Cpe) Analysis:
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
{logo}
================================================================================
                    SOLAR RAIL STRUCTURAL CALCULATION REPORT
                          Standard: AS/NZS 1170.2:2021
================================================================================

[0] PROJECT DETAILS
-------------------
   Project Name:      {inputs.get('project_name', '-')}
   Location:          {inputs.get('project_location', '-')}
   Engineer:          {inputs.get('engineer', '-')}
   Generated Date:    {current_time}

[1] TECHNICAL INPUTS
--------------------
   - Rail Model:      {inputs['rail_brand']} - {inputs['rail_model']}
   - Region:          {inputs['region']} (Vr = {inputs['vr']} m/s)
   - Probability:     Level {inputs['imp_level']} / Life {inputs['design_life']} yr (R=1/{inputs['ret_period']})
   - Geometry:        {inputs['b_width']}m (W) x {inputs['b_depth']}m (D) x {inputs['b_height']}m (H)

[2] WIND ANALYSIS DETAILS
-------------------------
{step_vdes}
{step_cpe}
{step_load}
{step_optimization}

[3] SPAN OPTIMIZATION LOGS (LAST 10 STEPS PER ZONE)
---------------------------------------------------
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
   M* ({critical_res['moment']:.3f}) <= Mn ({struct_res['Mn']:.3f}) --> PASS (OK)

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

[7] VISUALIZATION GUIDE
-----------------------
{ridge_art}
{zone_art}
================================================================================
"""
    return report_text

def create_pdf_report(report_string):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Courier", size=8)
    safe_text = report_string.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 4, safe_text)
    return bytes(pdf.output())
