import numpy as np

class WindLoadCalculator:
    def __init__(self):
        # 1. ข้อมูลความเร็วลมใหม่ (AS/NZS Updated)
        self.wind_data = {
            "R": np.array([1, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000]),
            "NZ_1_2": np.array([31, 35, 37, 39, 39, 41, 42, 43, 44, 45, 46, 47, 47, 48, 49]),
            "NZ_3":   np.array([37, 42, 44, 46, 46, 48, 50, 51, 51, 53, 54, 55, 55, 56, 57]),
            "NZ_4":   np.array([38, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50, 51, 52, 52, 53]),
            "A":      np.array([30, 32, 34, 37, 37, 39, 41, 43, 43, 45, 46, 48, 48, 50, 51]),
            "B":      np.array([26, 28, 33, 38, 39, 44, 48, 52, 53, 57, 60, 63, 64, 67, 69]),
            "C":      np.array([23, 33, 39, 45, 47, 52, 56, 61, 62, 66, 70, 73, 74, 78, 81]),
            "D":      np.array([23, 35, 43, 51, 53, 60, 66, 72, 74, 80, 85, 90, 91, 95, 99]),
        }

        # 2. Return Period Map
        self.return_period_map = {
            (1, 5): 25, (2, 5): 50, (3, 5): 100, (4, 5): 250,
            (1, 25): 50, (2, 25): 100, (3, 25): 250, (4, 25): 500,
            (1, 50): 100, (2, 50): 500, (3, 50): 1000, (4, 50): 2500,
            (1, 100): 250, (2, 100): 1000, (3, 100): 2500, (4, 100): 2500,
        }

    def get_return_period(self, importance_level, design_life):
        """คืนค่า Return Period (R)"""
        return self.return_period_map.get((importance_level, design_life), 500)

    def get_regional_wind_speed(self, region, return_period):
        """คำนวณ VR จาก Region และ Return Period"""
        if region not in self.wind_data:
            return 0
        return np.interp(return_period, self.wind_data["R"], self.wind_data[region])

    def get_terrain_multiplier(self, height, terrain_category):
        """
        คำนวณ Mz,cat (Terrain/Height Multiplier) ตาม AS/NZS 1170.2 Table 4.1
        """
        # Interpolation Table for Mz,cat based on Height (m)
        # H: 3, 5, 10, 15, 20, 30, 40, 50
        h_refs = [3, 5, 10, 15, 20, 30, 40, 50]
        
        mz_data = {
            1: [0.97, 1.01, 1.12, 1.16, 1.19, 1.22, 1.24, 1.25], # Cat 1
            2: [0.91, 0.91, 1.00, 1.05, 1.08, 1.12, 1.16, 1.18], # Cat 2
            3: [0.83, 0.83, 0.83, 0.89, 0.94, 1.00, 1.04, 1.07], # Cat 3
            4: [0.75, 0.75, 0.75, 0.75, 0.75, 0.80, 0.85, 0.90]  # Cat 4
        }
        
        if terrain_category not in mz_data:
            return 1.0
            
        # Clamp height between 3m and 50m for lookup (standard range)
        h_calc = max(3, min(height, 50))
        return np.interp(h_calc, h_refs, mz_data[terrain_category])

    def calculate_site_wind_speed(self, V_R, Mz_cat, Ms=1.0, Mt=1.0, Md=1.0):
        """
        คำนวณ V_sit,beta = V_R * Md * (Mz,cat * Ms * Mt)
        """
        V_sit = V_R * Md * (Mz_cat * Ms * Mt)
        return V_sit

    def calculate_design_pressure(self, V_sit, C_fig=1.0, C_dyn=1.0):
        """
        คำนวณ p = 0.5 * rho * V_sit^2 * C_fig * C_dyn
        rho_air approx 1.2 kg/m3
        """
        p = 0.5 * 1.2 * (V_sit ** 2) * C_fig * C_dyn
        return p / 1000 # Convert to kPa
