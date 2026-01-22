import numpy as np

class WindLoadCalculator:
    def __init__(self):
        # 1. ข้อมูลความเร็วลม (Regional Wind Speeds) จากไฟล์ AS-NZS Wind speed.xlsx
        # หน่วย: เมตร/วินาที (m/s)
        self.wind_data = {
            # Return Periods (R)
            "R": np.array([1, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000]),
            
            # Regions
            "NZ_1_2": np.array([31, 35, 37, 39, 39, 41, 42, 43, 44, 45, 46, 47, 47, 48, 49]),
            "NZ_3":   np.array([37, 42, 44, 46, 46, 48, 50, 51, 51, 53, 54, 55, 55, 56, 57]),
            "NZ_4":   np.array([38, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50, 51, 52, 52, 53]),
            "A":      np.array([30, 32, 34, 37, 37, 39, 41, 43, 43, 45, 46, 48, 48, 50, 51]), # Non-cyclonic A (0-5)
            "B":      np.array([26, 28, 33, 38, 39, 44, 48, 52, 53, 57, 60, 63, 64, 67, 69]), # Non-cyclonic B (1,2)
            "C":      np.array([23, 33, 39, 45, 47, 52, 56, 61, 62, 66, 70, 73, 74, 78, 81]), # Cyclonic C (max)
            "D":      np.array([23, 35, 43, 51, 53, 60, 66, 72, 74, 80, 85, 90, 91, 95, 99]), # Cyclonic D (max)
        }

        # 2. ตารางแปลง Importance Level & Design Life -> Annual Probability of Exceedance (1/R)
        # อ้างอิงมาตรฐาน AS/NZS 1170.0 Table 3.3 (โดยประมาณสำหรับ Wind/ULS)
        # Key format: (Importance Level, Design Life years) -> Return Period (R)
        self.return_period_map = {
            # Design Life 5 Years (Construction/Temporary)
            (1, 5): 25,
            (2, 5): 50,
            (3, 5): 100,
            (4, 5): 250, # Approximate scaling

            # Design Life 25 Years
            (1, 25): 50,
            (2, 25): 100,
            (3, 25): 250,
            (4, 25): 500,

            # Design Life 50 Years (Standard)
            (1, 50): 100,   # Low hazard
            (2, 50): 500,   # Normal structures
            (3, 50): 1000,  # Major structures
            (4, 50): 2500,  # Post-disaster structures

            # Design Life 100 Years
            (1, 100): 250,
            (2, 100): 1000,
            (3, 100): 2500,
            (4, 100): 2500, # Or higher depending on specific code interpretation (e.g. 1/5000)
        }

    def get_return_period(self, importance_level, design_life):
        """
        คำนวณ Return Period (R) จาก Importance Level และ Design Life
        """
        # พยายามหาค่าตรงๆ จากตาราง
        key = (importance_level, design_life)
        if key in self.return_period_map:
            return self.return_period_map[key]
        
        # ถ้าไม่มีค่าตรงๆ ให้ใช้ Logic พื้นฐานของ AS/NZS 1170.0 สำหรับ 50 ปีเป็นฐาน
        # หรือแจ้งเตือนให้ผู้ใช้ระบุ Return Period เอง
        print(f"Warning: No standard mapping found for IL={importance_level}, Life={design_life} years.")
        print("Defaulting to standard 50-year design life mapping logic.")
        
        # Fallback logic (Standard 50 years)
        if importance_level == 1: return 100
        if importance_level == 2: return 500
        if importance_level == 3: return 1000
        if importance_level == 4: return 2500
        return 500

    def get_wind_speed(self, region, importance_level=2, design_life=50, return_period=None):
        """
        คำนวณความเร็วลม (VR)
        - region: 'NZ_1_2', 'NZ_3', 'NZ_4', 'A', 'B', 'C', 'D'
        - return_period: ระบุค่า R เอง (ถ้ามีค่านี้จะข้ามการคำนวณจาก IL/Life)
        """
        
        # 1. Determine Return Period (R)
        if return_period is None:
            R = self.get_return_period(importance_level, design_life)
        else:
            R = return_period

        # 2. Validate Region
        if region not in self.wind_data:
            raise ValueError(f"Invalid region: {region}. Available: {list(self.wind_data.keys())[1:]}")

        # 3. Interpolate Wind Speed from Data
        # ใช้ Linear Interpolation สำหรับค่า R ที่อยู่ระหว่างจุดข้อมูล
        # ในทางวิศวกรรมลม กราฟมักจะเป็นเส้นตรงเมื่อพล็อต V กับ log(R) แต่เนื่องจากข้อมูลมีความละเอียดพอสมควร
        # การใช้ Linear Interpolation กับค่า R หรือ V ก็ให้ผลใกล้เคียงกันสำหรับการใช้งานทั่วไป
        # เพื่อความแม่นยำสูงสุดตามตาราง เราจะใช้ numpy.interp
        
        V_R = np.interp(R, self.wind_data["R"], self.wind_data[region])
        
        return round(V_R, 2), R

# --- ตัวอย่างการใช้งาน ---
if __name__ == "__main__":
    calc = WindLoadCalculator()

    # Case 1: Standard House in Sydney (Region A, IL 2, 50 years)
    v_sydney, r_sydney = calc.get_wind_speed(region="A", importance_level=2, design_life=50)
    print(f"Sydney (Region A, IL2, 50y): R={r_sydney} years, Vr={v_sydney} m/s")

    # Case 2: Hospital in Cyclonic Area (Region C, IL 4, 50 years)
    v_cyclone, r_cyclone = calc.get_wind_speed(region="C", importance_level=4, design_life=50)
    print(f"Cyclone Hospital (Region C, IL4, 50y): R={r_cyclone} years, Vr={v_cyclone} m/s")

    # Case 3: Temporary Shed in NZ (Region NZ_3, IL 1, 5 years)
    v_temp, r_temp = calc.get_wind_speed(region="NZ_3", importance_level=1, design_life=5)
    print(f"Temp Shed NZ (Region NZ3, IL1, 5y): R={r_temp} years, Vr={v_temp} m/s")
    
    # Case 4: Manual Return Period (e.g. 10000 years check)
    v_extreme, r_extreme = calc.get_wind_speed(region="D", return_period=10000)
    print(f"Extreme Check (Region D, R=10000): Vr={v_extreme} m/s")
