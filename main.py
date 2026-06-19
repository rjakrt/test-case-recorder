import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QInputDialog, QMessageBox)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from pynput import mouse, keyboard
from core_engine import TestCaseManager

SVG_ICONS = {
    "ready.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="#e0e0e0" stroke="#9e9e9e" stroke-width="2"/></svg>""",
    "record.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="#f44336"/></svg>""",
    "pause.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="8" y="7" width="3" height="10" fill="#ff9800"/><rect x="13" y="7" width="3" height="10" fill="#ff9800"/></svg>""",
    "cut.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>""",
    "export.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>""",
    "reset.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#2196f3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 2v6h6M21.5 22v-6h-6"/><path d="M22 11.5A10 10 0 0 0 3.2 7.2M2 12.5a10 10 0 0 0 18.8 4.2"/></svg>""",
    "camera.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#9c27b0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>"""
}

def setup_icons():
    if not os.path.exists("icons"):
        os.makedirs("icons")
    for filename, content in SVG_ICONS.items():
        filepath = os.path.join("icons", filename)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(content)

class RecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = TestCaseManager()
        self.is_recording = False
        
        self.mouse_listener = None
        self.keyboard_listener = None
        self.typed_buffer = ""
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Test Case Recorder")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setGeometry(100, 100, 250, 230) 
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel('Status: <img src="icons/ready.svg" width="14" height="14"> SIAP (Off)')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.btn_record = QPushButton(" Start Record")
        self.btn_record.setIcon(QIcon("icons/record.svg"))
        self.btn_record.clicked.connect(self.toggle_record)
        layout.addWidget(self.btn_record)
        
        self.btn_screenshot = QPushButton(" Take Screenshot")
        self.btn_screenshot.setIcon(QIcon("icons/camera.svg"))
        self.btn_screenshot.clicked.connect(self.trigger_screenshot)
        layout.addWidget(self.btn_screenshot)
        
        self.btn_new_case = QPushButton(" New Case (Save & Cut)")
        self.btn_new_case.setIcon(QIcon("icons/cut.svg"))
        self.btn_new_case.clicked.connect(self.prompt_new_case)
        layout.addWidget(self.btn_new_case)
        
        self.btn_export = QPushButton(" Export to Excel")
        self.btn_export.setIcon(QIcon("icons/export.svg"))
        self.btn_export.clicked.connect(self.export_data)
        layout.addWidget(self.btn_export)

        self.btn_reset = QPushButton(" Reset Session")
        self.btn_reset.setIcon(QIcon("icons/reset.svg"))
        self.btn_reset.clicked.connect(self.trigger_reset)
        layout.addWidget(self.btn_reset)
        
        self.setLayout(layout)

    def flush_typed_buffer(self):
        if self.typed_buffer.strip():
            self.engine.add_step(f"Ketik input: '{self.typed_buffer}'")
            self.typed_buffer = "" 

    def on_press(self, key):
        if not self.is_recording:
            return
            
        try:
            if hasattr(key, 'char') and key.char == '\x03': 
                self.flush_typed_buffer()
                self.engine.add_step("Tekan tombol 'CTRL + C'")
                return
            elif hasattr(key, 'char') and key.char == '\x16': 
                self.flush_typed_buffer()
                self.engine.add_step("Tekan tombol 'CTRL + V'")
                return
                
            if hasattr(key, 'char') and key.char is not None:
                self.typed_buffer += key.char
            elif key == keyboard.Key.space:
                self.typed_buffer += " "
            elif key == keyboard.Key.backspace:
                self.typed_buffer = self.typed_buffer[:-1]
            elif key in [keyboard.Key.enter, keyboard.Key.tab]:
                self.flush_typed_buffer()
                self.engine.add_step(f"Tekan tombol '{key.name.upper()}'")
                
            elif isinstance(key, keyboard.Key) and key.name is not None:
                if (key.name.startswith('f') and key.name[1:].isdigit()) or \
                   key in [keyboard.Key.esc, keyboard.Key.delete, keyboard.Key.insert]:
                    
                    self.flush_typed_buffer()
                    self.engine.add_step(f"Tekan tombol '{key.name.upper()}'")
        except Exception:
            pass

    def on_click(self, x, y, button, pressed):
        if pressed and self.is_recording:
            self.flush_typed_buffer()
            
            if button == mouse.Button.left:
                self.engine.capture_element_info(int(x), int(y))
            elif button == mouse.Button.right:
                self.engine.add_step("Klik Kanan (Context Menu)")

    def toggle_record(self):
        if not self.is_recording:
            self.is_recording = True
            self.btn_record.setText(" Pause Record")
            self.btn_record.setIcon(QIcon("icons/pause.svg"))
            self.status_label.setText('Status: <img src="icons/record.svg" width="14" height="14"> MEREKAM...')
            
            if self.mouse_listener is None:
                self.mouse_listener = mouse.Listener(on_click=self.on_click)
                self.mouse_listener.start()
            if self.keyboard_listener is None:
                self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
                self.keyboard_listener.start()
        else:
            self.is_recording = False
            self.btn_record.setText(" Start Record")
            self.btn_record.setIcon(QIcon("icons/record.svg"))
            self.status_label.setText('Status: <img src="icons/pause.svg" width="14" height="14"> PAUSED')

    def trigger_screenshot(self):
        """Fungsi untuk menangani klik tombol Screenshot"""
        if not self.is_recording:
            QMessageBox.warning(self, "Peringatan", "Harap klik Start Record terlebih dahulu sebelum mengambil Screenshot!")
            return
            
        self.flush_typed_buffer()
        
        self.hide()
        time.sleep(0.2)
        
        self.engine.capture_screenshot()
        
        self.show()
        
        self.status_label.setText('Status: <img src="icons/record.svg" width="14" height="14"> (SS TERSIMPAN) MEREKAM...')

    def prompt_new_case(self):
        self.flush_typed_buffer()
        was_recording = self.is_recording
        self.is_recording = False 
        
        if not self.engine.current_steps:
            QMessageBox.warning(self, "Peringatan", "Belum ada langkah yang terekam!")
            self.is_recording = was_recording
            return

        scenario_name, ok1 = QInputDialog.getText(self, "Simpan Skenario", "Nama Skenario:")
        if ok1 and scenario_name:
            expected_result, ok2 = QInputDialog.getText(self, "Simpan Skenario", "Expected Result:")
            if ok2:
                self.engine.save_current_case(scenario_name, expected_result)
                QMessageBox.information(self, "Sukses", f"Skenario '{scenario_name}' tersimpan di draf!")
        
        self.is_recording = was_recording

    def export_data(self):
        if not self.engine.test_cases:
            QMessageBox.warning(self, "Peringatan", "Belum ada Test Case yang disimpan di draf!")
            return
            
        filename = self.engine.export_to_excel()
        if filename:
            QMessageBox.information(self, "Sukses", f"File Excel berhasil dibuat!\nCek folder: {filename}")

    def trigger_reset(self):
        reply = QMessageBox.question(self, 'Konfirmasi Reset', 
                                     'Yakin mau reset sesi? Semua test case yang belum di-export akan hilang.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.typed_buffer = "" 
            self.engine.reset_session()
            
            if self.is_recording:
                self.toggle_record()
                
            self.status_label.setText('Status: <img src="icons/ready.svg" width="14" height="14"> SIAP (Telah Direset)')
            QMessageBox.information(self, "Reset Berhasil", "Sesi berhasil dibersihkan! Siap untuk pengujian aplikasi baru.")

if __name__ == '__main__':
    setup_icons()
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = RecorderApp()
    window.show()
    
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    sys.exit(app.exec())