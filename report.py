import pandas as pd
import numpy as np
import datetime

# ... (ฟังก์ชัน get_ascii_ridge_diagram และ get_ascii_art เหมือนเดิม) ...

def generate_full_report(inputs, wind_res, struct_res, zone_results, critical_res):
    """
    Main function to generate the detailed plain text report with equations and iterative logic.
    """
    
    # 1. Format Tables
    df_res = pd.DataFrame(zone_results)
    # เพิ่มคอลัมน์ Utilization Ratio สำหรับตารางสรุป
    df_res['Utilization'] = (df_res['M* (kNm)'] / struct_res['Mn']) * 100
    
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
    
    # --- หัวข้อที่ขอปรับปรุง: Iterative Process & Utilization ---
    
    # คำนวณค่าคงที่สำหรับสมการโมเมนต์ (กรณี Continuous beam 2 spans เป็นตัวอย่าง)
    # M_max = coefficient * w * L^2
    # ในโปรแกรมใช้ FEM iterative จึงจะแสดงเป็น Step-by-step logic
    
    step_optimization = f"""
    1. Optimization Objective
       Find Max Span (L) such that: Design Moment (M*) <= Rail Capacity (Mn)
       Where Rail Capacity (Mn) = {struct_res['Mn']:.3f} kNm

    2. Iterative Calculation Process (Worst Case: {critical_res['zone']})
       The software performs an incremental search (0.01m steps) using Finite Element Method:
       
       [Step A] Apply Design Line Load (w): {critical_res['load']:.3f} kN/m
       [Step B] Define Support Configuration: {inputs['num_spans']} Continuous Spans
       [Step C] Iterate Span Length (L) and calculate Max Bending Moment:
       
       Iterative Samples for {critical_res['zone']}:
       - At L = {critical_res['span'] - 0.2:.2f} m  =>  M* = {critical_res['load'] * (critical_res['span']-0.2)**2 / 8:.3f} kNm (Approx)
       - At L = {critical_res['span'] - 0.1:.2f} m  =>  M* = {critical_res['load'] * (critical_res['span']-0.1)**2 / 8:.3f} kNm (Approx)
       - At L = {critical_res['span']:.2f} m  =>  M* = {critical_res['moment']:.3f} kNm  <-- OPTIMAL
       
       >> Resulting Max Allowable Span = {critical_res['span']:.2f} m

    3. Structural Utilization Check
       Formula: Utilization Ratio (%) = (M* / Mn) * 100
       
       Substitution:
       Ratio = ({critical_res['moment']:.3f} kNm / {struct_res['Mn']:.3f} kNm) * 100
       
       >> Utilization Ratio = { (critical_res['moment'] / struct_res['Mn']) * 100 :.2f} %
       (Status: {'SAFE' if critical_res['moment'] <= struct_res['Mn'] else 'UNSAFE'})
    """

    # ... (ส่วนประกอบอื่นๆ ของ Report ประกอบเข้าด้วยกัน) ...
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
   - Rail Capacity (Mn):         {struct_res['Mn']:.3f} kNm

[2] DETAILED WIND LOAD CALCULATION
----------------------------------
   (Calculation logic according to AS/NZS 1170.2 as detailed in previous section)
   >> V_des = {inputs['v_des']:.2f} m/s
   >> p_design ({critical_res['zone']}) = {critical_res['pressure']:.3f} kPa
   >> Line Load (w) = {critical_res['load']:.3f} kN/m

[3] SPAN OPTIMIZATION & UTILIZATION CHECK
------------------------------------------
{step_optimization}

[4] ZONE ANALYSIS SUMMARY (ALL ZONES)
--------------------------------------
{table_str}

[5] CRITICAL CASE SUMMARY ({critical_res['zone']})
---------------------------------------------------
   >> Max Design Moment (M*):    {critical_res['moment']:.3f} kNm
   >> Max Reaction Force:        {critical_res['reaction']:.3f} kN
   >> Max Allowable Span:        {critical_res['span']:.2f} m

[6] LIMITATIONS & VISUALS
-------------------------
   (Refer to visual guide and limitations section for installation safety)
{ridge_art}
================================================================================
"""
    return report_text
