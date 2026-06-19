import pandas as pd
import os
import re 
from datetime import datetime
from pywinauto import Desktop
from openpyxl.styles import Alignment
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import ImageGrab, Image as PILImage

class TestCaseManager:
    def __init__(self):
        self.test_cases = []
        self.current_steps = []
        self.current_screenshots = []
        self.tc_counter = 1
        self.desktop = Desktop(backend="uia")

    def capture_element_info(self, x, y):
        try:
            element = self.desktop.from_point(x, y)
            
            parent_window = element.top_level_parent().window_text()
            if parent_window == "Test Case Recorder":
                return 

            element_name = element.window_text()
            element_type = element.element_info.control_type
            
            if element_name:
                step_text = f"Klik '{element_name}' ({element_type})"
                self.add_step(step_text)
                
        except Exception as e:
            self.add_step(f"Klik di area koordinat (X:{x}, Y:{y})")

    def add_step(self, step_text):
        if self.current_steps:
            last_step = self.current_steps[-1]
            
            if last_step == step_text:
                self.current_steps[-1] = f"{step_text} (2x)"
                return
            
            match = re.match(r"^(.*?) \((\d+)x\)$", last_step)
            if match and match.group(1) == step_text:
                count = int(match.group(2)) + 1
                self.current_steps[-1] = f"{step_text} ({count}x)"
                return

        self.current_steps.append(step_text)
        print(f"[*] Langkah terekam: {step_text}")

    def capture_screenshot(self):
        """Memotret layar dan menyimpannya ke folder"""
        if not os.path.exists("output/screenshots"):
            os.makedirs("output/screenshots")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"output/screenshots/SS_{timestamp}.png"
        
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        
        self.current_screenshots.append(filepath)
        self.add_step(f"📸 (Screenshot diambil: {os.path.basename(filepath)})")
        return filepath

    def save_current_case(self, scenario_name, expected_result):
        if not self.current_steps:
            return False 
            
        formatted_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(self.current_steps)])
        tc_id = f"TC-{self.tc_counter:03d}"
        
        case_data = {
            "ID": tc_id,
            "Skenario": scenario_name,
            "Steps": formatted_steps,
            "Expected Result": expected_result,
            "Status": "",
            "Notes (Screenshot)": "",
            "_screenshots_data": self.current_screenshots.copy()
        }
        
        self.test_cases.append(case_data)
        self.tc_counter += 1
        self.current_steps = [] 
        self.current_screenshots = [] 
        return True

    def reset_session(self):
        self.test_cases = []
        self.current_steps = []
        self.current_screenshots = []
        self.tc_counter = 1
        print("[*] Sesi telah direset.")

    def export_to_excel(self):
        if not self.test_cases:
            return None

        export_data = []
        for tc in self.test_cases:
            clean_tc = {k: v for k, v in tc.items() if not k.startswith('_')}
            export_data.append(clean_tc)

        df = pd.DataFrame(export_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not os.path.exists("output"):
            os.makedirs("output")
            
        filename = f"output/TestCase_Result_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Test Cases')
            worksheet = writer.sheets['Test Cases']
            
            worksheet.column_dimensions['B'].width = 25 
            worksheet.column_dimensions['C'].width = 45 
            worksheet.column_dimensions['D'].width = 30 
            worksheet.column_dimensions['F'].width = 45 
            
            for index, tc in enumerate(self.test_cases):
                row_num = index + 2 
                
                if tc['_screenshots_data']:
                    img_path = tc['_screenshots_data'][0] 
                    if os.path.exists(img_path):
                        pil_img = PILImage.open(img_path)
                        ratio = 300 / float(pil_img.size[0])
                        new_height = int((float(pil_img.size[1]) * float(ratio)))
                        
                        img = OpenpyxlImage(img_path)
                        img.width = 300
                        img.height = new_height
                        
                        worksheet.add_image(img, f"F{row_num}")
                        
                        worksheet.row_dimensions[row_num].height = (new_height * 0.75) + 15
                        
            for row in worksheet.iter_rows(min_row=2, max_col=6, max_row=len(df)+1):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
                
        return filename