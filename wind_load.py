import math

# =============================================================================================
# 1. ฐานข้อมูลความเร็วลม (Wind Speed Data) - AS/NZS 1170.2
# =============================================================================================
# หน่วย: เมตร/วินาที (m/s)
# ข้อมูลอ้างอิงจากไฟล์: AS-NZS Wind speed.xlsx
# Key: Region Code
# Value: { Return Period (Years): Wind Speed (m/s) }

WIND_DATA = {
    # --- Australia Regions (Non-cyclonic) ---
    # Region A: ครอบคลุม A0 ถึง A5
    "A0": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A1": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A2": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A3": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A4": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A5": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},

    # Region B: ครอบคลุม B1, B2
    "B1": {1: 26, 5: 28, 10: 33, 20: 38, 25: 39, 50: 44, 100: 48, 200: 52, 250: 53, 500: 57, 1000: 60, 2000: 63, 2500: 64, 5000: 67, 10000: 69},
    "B2": {1: 26, 5: 28, 10: 33, 20: 38, 25: 39, 50: 44, 100: 48, 200: 52, 250: 53, 500: 57, 1000: 60, 2000: 63, 2500: 64, 5000: 67, 10000: 69},

    # --- Australia Regions (Cyclonic) ---
    "C":  {1: 23, 5: 33, 10: 39, 20: 45, 25: 47, 50: 52, 100: 56, 200: 61, 250: 62, 500: 66, 1000: 70, 2000: 73, 2500: 74, 5000: 78, 10000: 81},
    "D":  {1: 23, 5: 35, 10: 43, 20: 51, 25: 53, 50: 60, 100: 66, 200: 72, 250: 74, 500: 80, 1000: 85, 2000: 90, 2500: 91, 5000: 95, 10000: 99},

    # --- New Zealand Regions ---
    # Region NZ (1 to 2) - ใช้ข้อมูลชุดเดียวกันสำหรับ NZ1 และ NZ2
    "NZ1": {1: 31, 5: 35, 10: 37, 20: 39, 25: 39, 50: 41, 100: 42, 200: 43, 250: 44, 500: 45, 1000: 46, 2000: 47, 2500: 47, 5000: 48, 10000: 49},
    "NZ2": {1: 31, 5: 35, 10: 37, 20: 39, 25: 39, 50: 41, 100: 42, 200: 43, 250: 44, 500: 45, 1000: 46, 2000: 47, 2500: 47, 5000: 48, 10000: 49},
    # Region NZ3
    "NZ3": {1: 37, 5: 42, 10: 44, 20: 46, 25: 46, 50: 48, 100: 50, 200: 51, 250: 51, 500: 53, 1000: 54, 2000: 55, 2500: 55, 5000: 56, 10000: 57},
    # Region NZ4
    "NZ4": {1: 38, 5: 42, 10: 43, 20: 44, 25: 45, 50: 46, 100: 47, 200: 48, 250: 49, 500: 50, 1000: 50, 2000: 51, 2500: 52, 5000: 52, 10000: 53}
}

# =============================================================================================
# 2. ฟังก์ชันคำนวณและดึงค่า (Calculation & Utility Functions)
# =============================================================================================

def get_return_period(importance_level, design_life):
    """
    กำหนดค่า Annual Probability of Exceedance (1/R) ตาม AS/NZS 1170.0
    และแปลงเป็น Return Period (R)
    
    Args:
        importance_level (int): 1, 2, 3, or 4
        design_life (int): Years (e.g., 25, 50, 100)
    
    Returns:
        int: Return Period (Years)
    """
    # ตารางแบบ Simplified ตามมาตรฐานทั่วไป (ต้องตรวจสอบกับ AS/NZS 1170.0 Table 3.3 จริงอีกครั้งเพื่อความแม่นยำสูงสุด)
    # Mapping: (Importance Level, Design Life) -> Return Period
    lookup = {
        (1, 5): 25,   (1, 25): 100,  (1, 50): 250,  (1, 100): 500,
        (2, 5): 50,   (2, 25): 250,  (2, 50): 500,  (2, 100): 1000,
        (3, 5): 100,  (3, 25): 500,  (3, 50): 1000, (3, 100): 2500,
        (4, 5): 250,  (4, 25): 1000, (4, 50): 2500, (4, 100): 10000 # Extreme cases
    }
    
    # Default fallback logic if specific pair not in lookup (Approximation)
    if (importance_level, design_life) in lookup:
        return lookup[(importance_level, design_life)]
    
    # Fallback logic based on IL
    if importance_level == 1:
        if design_life <= 10: return 25
        return 100
    elif importance_level == 2:
        if design_life <= 10: return 50
        return 500
    elif importance_level == 3:
        if design_life <= 10: return 100
        return 1000
    else: # IL 4
        return 2000 # Very high

def get_vr_from_ari(region, ret_period):
    """
    ดึงค่า Vr (Regional Wind Speed) จากฐานข้อมูล WIND_DATA
    
    Args:
        region (str): รหัส Region (e.g., "A1", "C", "NZ1")
        ret_period (int): รอบปีการกลับคืน (Return Period)
    
    Returns:
        float: ความเร็วลม (m/s)
    """
    # Fallback to default if region not found
    if region not in WIND_DATA:
        return 45.0 
    
    data = WIND_DATA[region]
    
    # กรณีมีค่าตรงกับ Key ใน Dictionary
    if ret_period in data:
        return float(data[ret_period])
    
    # กรณีไม่มีค่าตรง ให้ใช้ค่าของปีที่ *มากกว่า* ที่ใกล้ที่สุด (Conservative approach)
    # เช่น ต้องการ 300 ปี แต่มีแค่ 250 กับ 500 -> ให้ใช้ค่าของ 500 ปี
    sorted_years = sorted(data.keys())
    for yr in sorted_years:
        if yr >= ret_period:
            return float(data[yr])
            
    # ถ้าเกินปีสูงสุดที่มี ให้ใช้ค่าสูงสุดที่มี
    return float(data[sorted_years[-1]])

def get_mz_cat(height, terrain_category):
    """
    คำนวณค่าตัวคูณสภาพภูมิประเทศ Mz,cat (Terrain/Height Multiplier)
    ตาม AS/NZS 1170.2 Table 4.1 (Simplified)
    
    Args:
        height (float): ความสูงอาคาร (m)
        terrain_category (float): 1, 1.5, 2, 2.5, 3, 4
    """
    # ตาราง Mz,cat อย่างง่ายสำหรับความสูงมาตรฐาน (Interpolation possible)
    # (Height, TC): Mz,cat
    # นี่คือการประมาณค่าจากมาตรฐาน
    h = max(height, 3.0) # ต่ำสุด 3m
    
    # Logic การคำนวณแบบ Logarithmic profile อย่างง่ายสำหรับ TC ต่างๆ
    # Mz,cat = K * ln(h/z0) (สูตรประมาณการทางวิศวกรรมลมทั่วไป)
    
    # กำหนดค่าคงที่คร่าวๆ เพื่อให้ได้ค่าใกล้เคียงตารางมาตรฐาน
    # TC1: Very exposed
    if terrain_category <= 1.0:
        return 1.12 if h <= 5 else 1.05 + 0.05 * math.log(h)
    
    # TC2: Open terrain
    elif terrain_category <= 2.0:
        if h <= 5: return 0.91
        if h <= 10: return 1.00
        return 1.0 + 0.15 * math.log10(h/10)
        
    # TC2.5: Transitional
    elif terrain_category <= 2.5:
        if h <= 5: return 0.87
        if h <= 10: return 0.92
        return 0.92 + 0.13 * math.log10(h/10)

    # TC3: Suburban
    elif terrain_category <= 3.0:
        if h <= 5: return 0.83
        if h <= 10: return 0.83
        if h <= 15: return 0.89
        return 0.83 + 0.15 * math.log10(h/10) # Approximation

    # TC4: Dense urban
    else:
        if h <= 10: return 0.75
        if h <= 20: return 0.75
        return 0.75 + 0.10 * math.log10(h/20)

def calculate_v_des_detailed(vr, md, mz_cat, ms, mt):
    """
    คำนวณความเร็วลมออกแบบ V_sit,beta (Design Wind Speed)
    Formula: V_des = Vr * Md * (Mz,cat * Ms * Mt)
    """
    return vr * md * (mz_cat * ms * mt)

def calculate_wind_pressure(v_des, c_fig, ka=1.0, kc=1.0, kl=1.0, p_dyn_factor=1.0):
    """
    คำนวณแรงดันลมออกแบบ (Design Wind Pressure, p)
    p = 0.5 * rho * (V_des)^2 * C_fig * C_dyn
    โดย C_fig = Cpe * Ka * Kc * Kl * Kp
    """
    rho_air = 1.2 # kg/m3 density of air
    
    # Dynamic pressure qz
    q_z = 0.5 * rho_air * (v_des ** 2)
    
    # Design pressure in Pascals (Pa) -> convert to kPa
    p_design = q_z * c_fig * ka * kc * kl * p_dyn_factor
    return p_design / 1000.0 # Return kPa

def calculate_tributary_width(panel_w, panel_d, orientation='width'):
    """
    คำนวณความกว้างรับลม (Tributary Width) สำหรับราง
    """
    # ถ้าวางรางขนานกับด้านกว้างของแผง (Rail // Width) -> รับโหลดครึ่งหนึ่งของความลึก
    if orientation == 'width': 
        return panel_d / 2.0
    # ถ้าวางรางขนานกับด้านลึกของแผง (Rail // Depth) -> รับโหลดครึ่งหนึ่งของความกว้าง
    else: 
        return panel_w / 2.0

def solve_cpe_for_ratio(roof_angle, roof_type, h_d_ratio):
    """
    หาค่า Cpe (External Pressure Coefficient) ตามประเภทหลังคาและมุม
    (Simplified lookup logic based on AS/NZS 1170.2 Section 5)
    """
    # ค่าสมมติสำหรับการสาธิต (ต้องใช้ตารางจริงเยอะมากในการเขียนให้ครบทุกเคส)
    # คืนค่า Cpe ที่เป็นลบ (Suction/Uplift) ที่วิกฤตที่สุด
    
    cpe = -0.9 # Default generic uplift
    
    if "Monoslope" in roof_type:
        if roof_angle < 10:
            cpe = -1.2 # Flat/Low pitch mono
        elif roof_angle < 20:
            cpe = -1.4
        else:
            cpe = -1.1
            
    elif "Gable" in roof_type:
        # Gable logic depends heavily on wind direction (0 or 90) and h/d
        if roof_angle < 10:
            cpe = -0.9 if h_d_ratio < 0.5 else -1.3 # Example logic
        elif roof_angle < 20:
            cpe = -0.7 if h_d_ratio < 0.5 else -0.9
        else:
            cpe = -0.6
            
    return {'cpe': cpe, 'notes': 'Simplified look-up'}
