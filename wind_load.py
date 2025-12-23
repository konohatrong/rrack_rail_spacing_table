import numpy as np

def interpolate_linear(val, x_list, y_list):
    """ Helper for linear interpolation """
    return np.interp(val, x_list, y_list)

def get_mz_cat(height, terrain_category):
    """
    AS/NZS 1170.2 Table 4.1: Terrain/Height Multipliers (Mz,cat)
    Simplified interpolation for standard categories.
    """
    # Height breakpoints (m)
    z_vals = [3, 5, 10, 15, 20, 30, 40, 50]
    
    # Data for each Terrain Category (TC)
    mz_data = {
        1: [0.99, 1.05, 1.12, 1.16, 1.19, 1.22, 1.24, 1.25], # TC 1 (Very Exposed)
        2: [0.91, 0.91, 1.00, 1.05, 1.08, 1.12, 1.14, 1.16], # TC 2 (Open)
        2.5: [0.87, 0.87, 0.92, 0.97, 1.01, 1.06, 1.10, 1.13], # TC 2.5
        3: [0.83, 0.83, 0.83, 0.89, 0.94, 1.00, 1.04, 1.07], # TC 3 (Suburban)
        4: [0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.85, 0.90]  # TC 4 (Urban/City)
    }
    
    # Select closest TC (or fallback to TC 2)
    # Note: dict keys must match the type passed from slider (int or float)
    cat_vals = mz_data.get(terrain_category, mz_data[2])
    
    # Ensure height is at least 3m (Standard minimum)
    z_use = max(height, 3.0)
    
    # Interpolate Mz,cat
    return interpolate_linear(z_use, z_vals, cat_vals)

def calculate_v_des_detailed(Vr, Md, Mz_cat, Ms, Mt):
    """
    AS/NZS 1170.2 Eq 2.2: V_sit,beta = Vr * Md * (Mz,cat * Ms * Mt)
    """
    return Vr * Md * Mz_cat * Ms * Mt

# --- Tables 5.3 Logic ---

def get_table_5_3_A_value(ratio_val):
    """ ratio_val can be h/d or h/b """
    if ratio_val >= 1.0:
        return -1.3
    elif ratio_val <= 0.5:
        return -0.9
    else:
        return interpolate_linear(ratio_val, [0.5, 1.0], [-0.9, -1.3])

def get_table_5_3_B_value(angle, ratio_val):
    # Curve values for Upwind Slope
    cpe_hd_025 = [(10, -0.7), (15, -0.5), (20, -0.3), (25, -0.2), (30, -0.2), (35, 0.0), (45, 0.0)]
    cpe_hd_050 = [(10, -0.9), (15, -0.7), (20, -0.4), (25, -0.3), (30, -0.2), (35, -0.2), (45, 0.0)]
    cpe_hd_100 = [(10, -1.3), (15, -1.0), (20, -0.7), (25, -0.5), (30, -0.3), (35, -0.2), (45, 0.0)]
    
    val_025 = interpolate_linear(angle, [x[0] for x in cpe_hd_025], [x[1] for x in cpe_hd_025])
    val_050 = interpolate_linear(angle, [x[0] for x in cpe_hd_050], [x[1] for x in cpe_hd_050])
    val_100 = interpolate_linear(angle, [x[0] for x in cpe_hd_100], [x[1] for x in cpe_hd_100])
    
    if ratio_val <= 0.25: return val_025
    elif ratio_val >= 1.0: return val_100
    else: return np.interp(ratio_val, [0.25, 0.5, 1.0], [val_025, val_050, val_100])

def get_table_5_3_C_value(angle, ratio_val):
    # Curve values for Downwind Slope
    cpe_hd_025 = [(10, -0.3), (15, -0.5), (20, -0.6), (25, -0.6), (45, -0.6)]
    cpe_hd_050 = [(10, -0.5), (15, -0.5), (20, -0.6), (25, -0.6), (45, -0.6)]
    cpe_hd_100 = [(10, -0.7), (15, -0.6), (20, -0.6), (25, -0.6), (45, -0.6)]
    
    val_025 = interpolate_linear(angle, [x[0] for x in cpe_hd_025], [x[1] for x in cpe_hd_025])
    val_050 = interpolate_linear(angle, [x[0] for x in cpe_hd_050], [x[1] for x in cpe_hd_050])
    val_100 = interpolate_linear(angle, [x[0] for x in cpe_hd_100], [x[1] for x in cpe_hd_100])
    
    if ratio_val <= 0.25: return val_025
    elif ratio_val >= 1.0: return val_100
    else: return np.interp(ratio_val, [0.25, 0.5, 1.0], [val_025, val_050, val_100])

def solve_cpe_for_ratio(roof_angle, roof_type, ratio_val):
    """
    Generic solver for a given geometric ratio (h/d or h/b)
    """
    if roof_angle < 10:
        val = get_table_5_3_A_value(ratio_val)
        return {'cpe': val, 'note': 'Table 5.3(A)'}
    
    # Alpha >= 10
    cpe_up = get_table_5_3_B_value(roof_angle, ratio_val)
    cpe_down = get_table_5_3_C_value(roof_angle, ratio_val)
    
    if roof_type == 'Monoslope':
        # Monoslope worst case check
        if cpe_up < cpe_down:
            return {'cpe': cpe_up, 'note': 'Upwind Slope (Tab 5.3B)'}
        else:
            return {'cpe': cpe_down, 'note': 'Downwind Slope (Tab 5.3C)'}
    else:
        # Gable worst case
        if cpe_up < cpe_down:
            return {'cpe': cpe_up, 'note': 'Windward Side (Tab 5.3B)'}
        else:
            return {'cpe': cpe_down, 'note': 'Leeward Side (Tab 5.3C)'}

def calculate_wind_pressure(V_des, Cpe, Ka=1.0, Kc=1.0, Kl=1.0, Kp=1.0, C_dyn=1.0):
    rho_air = 1.2
    C_fig = Cpe * Ka * Kc * Kl * Kp
    p = 0.5 * rho_air * (V_des**2) * C_fig * C_dyn
    return abs(p) / 1000.0

def calculate_tributary_width(panel_width, panel_depth, rail_parallel_to):
    """
    คำนวณ Tributary Width สำหรับรางรับแผง
    """
    if rail_parallel_to == 'width':
        # รางขนานกับด้านกว้างของแผง (Landscape) -> รับน้ำหนักครึ่งหนึ่งของด้านลึก
        return panel_depth / 2.0
    else:
        # รางขนานกับด้านลึกของแผง (Portrait) -> รับน้ำหนักครึ่งหนึ่งของด้านกว้าง
        return panel_width / 2.0