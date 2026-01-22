import math

# =============================================================================================
# 1. ฐานข้อมูลความเร็วลม (Wind Speed Data) - AS/NZS 1170.2 (UPDATED)
# =============================================================================================
WIND_DATA = {
    # --- Australia Regions (Non-cyclonic) ---
    "A0": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A1": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A2": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A3": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A4": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},
    "A5": {1: 30, 5: 32, 10: 34, 20: 37, 25: 37, 50: 39, 100: 41, 200: 43, 250: 43, 500: 45, 1000: 46, 2000: 48, 2500: 48, 5000: 50, 10000: 51},

    "B1": {1: 26, 5: 28, 10: 33, 20: 38, 25: 39, 50: 44, 100: 48, 200: 52, 250: 53, 500: 57, 1000: 60, 2000: 63, 2500: 64, 5000: 67, 10000: 69},
    "B2": {1: 26, 5: 28, 10: 33, 20: 38, 25: 39, 50: 44, 100: 48, 200: 52, 250: 53, 500: 57, 1000: 60, 2000: 63, 2500: 64, 5000: 67, 10000: 69},

    "C":  {1: 23, 5: 33, 10: 39, 20: 45, 25: 47, 50: 52, 100: 56, 200: 61, 250: 62, 500: 66, 1000: 70, 2000: 73, 2500: 74, 5000: 78, 10000: 81},
    "D":  {1: 23, 5: 35, 10: 43, 20: 51, 25: 53, 50: 60, 100: 66, 200: 72, 250: 74, 500: 80, 1000: 85, 2000: 90, 2500: 91, 5000: 95, 10000: 99},

    # --- New Zealand Regions ---
    "NZ1": {1: 31, 5: 35, 10: 37, 20: 39, 25: 39, 50: 41, 100: 42, 200: 43, 250: 44, 500: 45, 1000: 46, 2000: 47, 2500: 47, 5000: 48, 10000: 49},
    "NZ2": {1: 31, 5: 35, 10: 37, 20: 39, 25: 39, 50: 41, 100: 42, 200: 43, 250: 44, 500: 45, 1000: 46, 2000: 47, 2500: 47, 5000: 48, 10000: 49},
    "NZ3": {1: 37, 5: 42, 10: 44, 20: 46, 25: 46, 50: 48, 100: 50, 200: 51, 250: 51, 500: 53, 1000: 54, 2000: 55, 2500: 55, 5000: 56, 10000: 57},
    "NZ4": {1: 38, 5: 42, 10: 43, 20: 44, 25: 45, 50: 46, 100: 47, 200: 48, 250: 49, 500: 50, 1000: 50, 2000: 51, 2500: 52, 5000: 52, 10000: 53}
}

def get_return_period(importance_level, design_life):
    lookup = {
        (1, 5): 25,   (1, 25): 100,  (1, 50): 250,  (1, 100): 500,
        (2, 5): 50,   (2, 25): 250,  (2, 50): 500,  (2, 100): 1000,
        (3, 5): 100,  (3, 25): 500,  (3, 50): 1000, (3, 100): 2500,
        (4, 5): 250,  (4, 25): 1000, (4, 50): 2500, (4, 100): 10000
    }
    if (importance_level, design_life) in lookup:
        return lookup[(importance_level, design_life)]
    if importance_level == 1: return 100
    elif importance_level == 2: return 500
    elif importance_level == 3: return 1000
    else: return 2000

def get_vr_from_ari(region, ret_period):
    if region not in WIND_DATA:
        return 45.0 
    data = WIND_DATA[region]
    if ret_period in data:
        return float(data[ret_period])
    sorted_years = sorted(data.keys())
    for yr in sorted_years:
        if yr >= ret_period:
            return float(data[yr])
    return float(data[sorted_years[-1]])

def get_mz_cat(height, terrain_category):
    h = max(height, 3.0)
    if terrain_category <= 1.0:
        return 1.12 if h <= 5 else 1.05 + 0.05 * math.log(h)
    elif terrain_category <= 2.0:
        if h <= 5: return 0.91
        if h <= 10: return 1.00
        return 1.0 + 0.15 * math.log10(h/10)
    elif terrain_category <= 2.5:
        if h <= 5: return 0.87
        if h <= 10: return 0.92
        return 0.92 + 0.13 * math.log10(h/10)
    elif terrain_category <= 3.0:
        if h <= 5: return 0.83
        if h <= 10: return 0.83
        if h <= 15: return 0.89
        return 0.83 + 0.15 * math.log10(h/10)
    else:
        if h <= 10: return 0.75
        if h <= 20: return 0.75
        return 0.75 + 0.10 * math.log10(h/20)

def calculate_v_des_detailed(vr, md, mz_cat, ms, mt):
    return vr * md * (mz_cat * ms * mt)

def calculate_wind_pressure(v_des, c_fig, ka=1.0, kc=1.0, kl=1.0, p_dyn_factor=1.0):
    rho_air = 1.2
    q_z = 0.5 * rho_air * (v_des ** 2)
    p_design = q_z * c_fig * ka * kc * kl * p_dyn_factor
    return p_design / 1000.0

def calculate_tributary_width(panel_w, panel_d, orientation='width'):
    if orientation == 'width': return panel_d / 2.0
    else: return panel_w / 2.0

def solve_cpe_for_ratio(roof_angle, roof_type, h_d_ratio):
    cpe = -0.9 
    if "Monoslope" in roof_type:
        if roof_angle < 10: cpe = -1.2
        elif roof_angle < 20: cpe = -1.4
        else: cpe = -1.1
    elif "Gable" in roof_type:
        if roof_angle < 10: cpe = -0.9 if h_d_ratio < 0.5 else -1.3
        elif roof_angle < 20: cpe = -0.7 if h_d_ratio < 0.5 else -0.9
        else: cpe = -0.6
    return {'cpe': cpe, 'notes': 'Simplified look-up'}
