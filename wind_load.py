import numpy as np

def interpolate_linear(val, x_list, y_list):
    """ Helper for linear interpolation """
    return np.interp(val, x_list, y_list)

def get_mz_cat(height, terrain_category):
    # Height breakpoints (m)
    z_vals = [3, 5, 10, 15, 20, 30, 40, 50]
    
    # Data for each Terrain Category (TC)
    mz_data = {
        1: [0.99, 1.05, 1.12, 1.16, 1.19, 1.22, 1.24, 1.25], 
        2: [0.91, 0.91, 1.00, 1.05, 1.08, 1.12, 1.14, 1.16], 
        2.5: [0.87, 0.87, 0.92, 0.97, 1.01, 1.06, 1.10, 1.13], 
        3: [0.83, 0.83, 0.83, 0.89, 0.94, 1.00, 1.04, 1.07], 
        4: [0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.85, 0.90] 
    }
    
    cat_vals = mz_data.get(terrain_category, mz_data[2])
    z_use = max(height, 3.0)
    return interpolate_linear(z_use, z_vals, cat_vals)

def get_return_period(importance_level, design_life=50):
    """
    AS/NZS 1170.0 Table 3.3 & F1: Annual Probability of Exceedance for ULS (Wind)
    simplified logic for standard cases.
    """
    # Standard ULS Return Periods (R) based on Importance Level (IL)
    # Ref AS/NZS 1170.0 Table 3.3 (approximate for Wind)
    # IL 1: 1/100
    # IL 2: 1/500
    # IL 3: 1/1000
    # IL 4: 1/2500
    
    # Note: If design life is not 50, strictly speaking P = 1 - (1-1/R)^N adjustments needed,
    # but standard usually dictates R based on IL directly for codified design.
    
    if importance_level == 1:
        return 100
    elif importance_level == 2:
        return 500
    elif importance_level == 3:
        return 1000
    elif importance_level == 4:
        return 2500
    else:
        return 500 # Default Normal

def get_vr_from_ari(region, return_period):
    """
    Get Regional Wind Speed (Vr) based on Region (A,B,C,D) and Return Period (R)
    Ref: AS/NZS 1170.2 Table 3.1 (2021 Edition)
    """
    # Defined Return Periods in Table 3.1
    r_points = [1, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500]
    
    # Data V_R (m/s)
    vr_data = {
        'A': [30, 32, 34, 37, 37, 39, 41, 43, 43, 45, 46, 48, 49], # A (Non-cyclonic)
        'B': [26, 28, 30, 33, 33, 36, 38, 40, 40, 43, 44, 46, 47], # B (Non-cyclonic) - Note: 1170.2-2021 might differ slightly, using std values
        'W': [30, 32, 34, 37, 37, 39, 41, 43, 43, 45, 46, 48, 49], # A/W (NZ)
        'C': [23, 33, 39, 45, 47, 52, 56, 61, 62, 66, 70, 73, 74], # C (Cyclonic)
        'D': [23, 35, 43, 51, 53, 60, 66, 72, 74, 80, 85, 89, 90]  # D (Severe Cyclonic)
    }
    
    # Interpolate for specific R (Standard uses log-linear or just table lookup)
    # We will use linear interpolation for simplicity between table points
    
    vals = vr_data.get(region, vr_data['A'])
    
    # Handle R > max
    if return_period > r_points[-1]:
        return vals[-1] # Cap at max table value or extrapolate (Safety: cap)
        
    return interpolate_linear(return_period, r_points, vals)

def calculate_v_des_detailed(Vr, Md, Mz_cat, Ms, Mt):
    return Vr * Md * Mz_cat * Ms * Mt

# --- Tables 5.3 Logic (Unchanged) ---
def get_table_5_3_A_value(ratio_val):
    if ratio_val >= 1.0: return -1.3
    elif ratio_val <= 0.5: return -0.9
    else: return interpolate_linear(ratio_val, [0.5, 1.0], [-0.9, -1.3])

def get_table_5_3_B_value(angle, ratio_val):
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
    if roof_angle < 10:
        val = get_table_5_3_A_value(ratio_val)
        return {'cpe': val, 'note': 'Table 5.3(A)'}
    
    cpe_up = get_table_5_3_B_value(roof_angle, ratio_val)
    cpe_down = get_table_5_3_C_value(roof_angle, ratio_val)
    
    if roof_type == 'Monoslope':
        if cpe_up < cpe_down: return {'cpe': cpe_up, 'note': 'Upwind Slope (Tab 5.3B)'}
        else: return {'cpe': cpe_down, 'note': 'Downwind Slope (Tab 5.3C)'}
    else:
        if cpe_up < cpe_down: return {'cpe': cpe_up, 'note': 'Windward Side (Tab 5.3B)'}
        else: return {'cpe': cpe_down, 'note': 'Leeward Side (Tab 5.3C)'}

def calculate_wind_pressure(V_des, Cpe, Ka=1.0, Kl=1.0, Kp=1.0, C_dyn=1.0):
    rho_air = 1.2
    C_fig = Cpe * Ka * Kc * Kl * Kp
    p = 0.5 * rho_air * (V_des**2) * C_fig * C_dyn
    return abs(p) / 1000.0

def calculate_tributary_width(panel_width, panel_depth, rail_parallel_to):
    if rail_parallel_to == 'width': return panel_depth / 2.0
    else: return panel_width / 2.0
