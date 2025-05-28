import sys
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QLineEdit, QDoubleSpinBox, 
                             QSpinBox, QGroupBox, QScrollArea, QTabWidget, QStackedWidget, 
                             QTextEdit, QSizePolicy, QGridLayout, QSlider)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

image_path_immersion = resource_path("image.png")
image_path_air = resource_path("image_air.png")

class CoolingCalculations:
    @staticmethod
    def calculateServerTemp(tCoolant, n, SA, L, tau, D, insulation, fluidType, Q, Aflow, Lchar, val):
        if val > 12:
            mult = (val - (val % 12))/12
            val = val - 12 * (mult)
            if val == 0:
                val = 12
        else:
            val = val
        if fluidType == "3M Novec 7000":
            k = 0.07
            Cp = 1300
            p = 1600
            mu = 4.5 * 10**-4
        if insulation == "Standard Fiberglass":
            D0 = 7
            FdD = math.exp(-D/D0)
        FaN = 0.75
        A0 = SA * 2
        AeFF = FaN * A0 * n
        fAgeT = 1 + 0.03 + (tau/8760)
        Lchar = A0 * 0.1
        Re = (p * (Q/Aflow)*Lchar)/mu
        Pr = (Cp*mu)/k
        h = (0.023*(Re**0.8)*(Pr**n))/Lchar
        return tCoolant + (L/(Q*100*Cp))*(fAgeT) + (val/2)

    @staticmethod
    def calculateACServerTemp(tAmbient, n, l, fanAirflow, fanEfficiency, dustAmount, heatSinkEfficiency, heatSinkSA):
        return ((tAmbient + (n*l))/(1232.5 * (l*fanAirflow) * fanEfficiency * (1-dustAmount))) * (heatSinkEfficiency * l * heatSinkSA)

    @staticmethod
    def calculateICoolingEnergy(tCoolant, n, SA, L, tau, D, insulation, fluidType, Q, Aflow, Lchar, val, L_pipe, epsilon=0.0001, pump_efficiency=0.65, safety_margin=True):
        server_temp = CoolingCalculations.calculateServerTemp(
            tCoolant, n, SA, L, tau, D, insulation, 
            fluidType, Q, Aflow, Lchar, val
        )
        if fluidType == "3M Novec 7000":
            p = 1600
            mu = 1.5e-3
        elif fluidType == "Mineral Oil":
            p = 850
            mu = 0.025
        elif fluidType == "Synthetic Oil":
            p = 900
            mu = 0.02
        elif fluidType == "Dielectric Fluid":
            p = 800
            mu = 0.015
        else:
            p = 1000
            mu = 0.01
        velocity = Q / Aflow
        Re = (p * velocity * Lchar) / mu
        if Re == 0:
            raise ValueError("Reynolds number cannot be zero")
        try:
            f = 0.25 / (math.log10((6.81/Re)**0.9 + (epsilon/(3.7*D))**1.11))**2
        except:
            f = 64/Re
        deltaP = f * (L_pipe/D) * 0.5 * p * velocity**2
        pump_power = (Q * deltaP) / (pump_efficiency * 1000)
        total_heat = n * L  
        heat_exchanger_power = total_heat * 0.10
        total_energy = pump_power + heat_exchanger_power
        if safety_margin:
            total_energy *= 1.25
        annual_cost = total_energy * 24 * 365 * 0.15
        
        return {
            'server_temp': round(server_temp, 1),
            'pump_power': round(pump_power, 2),
            'heat_exchanger_power': round(heat_exchanger_power, 2),
            'total_cooling_energy': round(total_energy, 2),
            'annual_cost': round(annual_cost, 2)
        }

    @staticmethod
    def calculateACoolingEnergy(tAmbient, n, l, fanAirflow, fanEfficiency, dustAmount, heatSinkEfficiency, heatSinkSA, duct_length, duct_diameter, duct_roughness=0.0001, safety_margin=True, chiller_cop=3.0, electricity_cost=0.15):
        server_temp = CoolingCalculations.calculateACServerTemp(tAmbient, n, l, fanAirflow, fanEfficiency, dustAmount, heatSinkEfficiency, heatSinkSA)
        rho_air = 1.225
        mu_air = 1.825e-5
        A_duct = math.pi * (duct_diameter/2)**2
        velocity = fanAirflow / A_duct
        Re = (rho_air * velocity * duct_diameter) / mu_air
        if Re == 0:
            raise ValueError("Reynolds number cannot be zero")
        try:
            f = 0.25 / (math.log10((6.81/Re)**0.9 + (duct_roughness/(3.7*duct_diameter))**1.11))**2
        except:
            f = 64/Re
        delta_p = f * (duct_length/duct_diameter) * 0.5 * rho_air * velocity**2
        fan_power = (fanAirflow * delta_p) / (fanEfficiency)
        total_heat = n * l
        chiller_power = total_heat / chiller_cop
        total_energy = fan_power + chiller_power
        if safety_margin:
            total_energy *= 1.25
        annual_cost = total_energy * 24 * 365 * electricity_cost
        
        return {
            'server_temp': round(server_temp, 1),
            'fan_power': round(fan_power, 2),
            'chiller_power': round(chiller_power, 2),
            'total_cooling_energy': round(total_energy, 2),
            'annual_cost': round(annual_cost, 2)
        }

class RackDataDialog(QWidget):
    def __init__(self, cooling_type, parent=None):
        super().__init__(parent)
        self.cooling_type = cooling_type
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        if self.cooling_type == "Immersion":
            
            self.coolant_temp = QDoubleSpinBox()
            self.coolant_temp.setRange(-50, 150)
            self.coolant_temp.setSuffix(" °C")
            self.coolant_temp.setValue(25)
            
            self.server_count = QSpinBox()
            self.server_count.setRange(1, 100)
            self.server_count.setValue(20)
            
            self.surface_area = QDoubleSpinBox()
            self.surface_area.setRange(0.1, 100)
            self.surface_area.setSuffix(" m²")
            self.surface_area.setValue(0.5)
            
            self.load = QDoubleSpinBox()
            self.load.setRange(0, 100000)
            self.load.setSuffix(" W")
            self.load.setValue(200)
            
            self.run_time = QDoubleSpinBox()
            self.run_time.setRange(0, 8760)
            self.run_time.setSuffix(" hours")
            
            self.distance = QDoubleSpinBox()
            self.distance.setRange(0, 100)
            self.distance.setSuffix(" m")
            self.distance.setValue(5)
            
            self.insulation_type = QComboBox()
            self.insulation_type.addItems(["None", "Standard Fiberglass", "Foam", "Fiberglass", "Aerogel"])
            
            self.fluid_type = QComboBox()
            self.fluid_type.addItems(["3M Novec 7000", "Mineral Oil", "Synthetic Oil", "Dielectric Fluid"])
            
            self.flow_rate = QDoubleSpinBox()
            self.flow_rate.setRange(0, 100)
            self.flow_rate.setSuffix(" L/min")
            self.flow_rate.setValue(0.05)
            
            self.flow_area = QDoubleSpinBox()
            self.flow_area.setRange(0, 10)
            self.flow_area.setSuffix(" cm²")
            self.flow_area.setValue(0.00785)
            
            
            layout.addWidget(QLabel("Coolant Temperature:"))
            layout.addWidget(self.coolant_temp)
            layout.addWidget(QLabel("Number of Servers:"))
            layout.addWidget(self.server_count)
            layout.addWidget(QLabel("Server Surface Area:"))
            layout.addWidget(self.surface_area)
            layout.addWidget(QLabel("Load:"))
            layout.addWidget(self.load)
            layout.addWidget(QLabel("Run Time:"))
            layout.addWidget(self.run_time)
            layout.addWidget(QLabel("Distance from Heat Exchanger:"))
            layout.addWidget(self.distance)
            layout.addWidget(QLabel("Insulation Type:"))
            layout.addWidget(self.insulation_type)
            layout.addWidget(QLabel("Fluid Type:"))
            layout.addWidget(self.fluid_type)
            layout.addWidget(QLabel("Coolant Flow Rate:"))
            layout.addWidget(self.flow_rate)
            layout.addWidget(QLabel("Cross Sectional Flow Area:"))
            layout.addWidget(self.flow_area)
            
        else:  
            self.ambient_temp = QDoubleSpinBox()
            self.ambient_temp.setRange(-50, 150)
            self.ambient_temp.setSuffix(" °C")
            self.ambient_temp.setValue(25)
            
            self.server_count = QSpinBox()
            self.server_count.setRange(1, 100)
            self.server_count.setValue(20)
            
            self.load = QDoubleSpinBox()
            self.load.setRange(0, 100000)
            self.load.setSuffix(" W")
            self.load.setValue(200)
            
            self.fan_airflow = QDoubleSpinBox()
            self.fan_airflow.setRange(0, 10)
            self.fan_airflow.setSuffix(" m³/s")
            self.fan_airflow.setValue(0.085)
            
            self.fan_efficiency = QDoubleSpinBox()
            self.fan_efficiency.setRange(0, 1)
            self.fan_efficiency.setValue(0.55)
            
            self.dust_amount = QDoubleSpinBox()
            self.dust_amount.setRange(0, 1)
            self.dust_amount.setValue(0.1)
            
            self.heat_sink_efficiency = QDoubleSpinBox()
            self.heat_sink_efficiency.setRange(0, 1)
            self.heat_sink_efficiency.setValue(0.75)
            
            self.heat_sink_sa = QDoubleSpinBox()
            self.heat_sink_sa.setRange(0, 10)
            self.heat_sink_sa.setSuffix(" m²")
            self.heat_sink_sa.setValue(1.2)
            
            
            layout.addWidget(QLabel("Ambient Temperature:"))
            layout.addWidget(self.ambient_temp)
            layout.addWidget(QLabel("Number of Servers:"))
            layout.addWidget(self.server_count)
            layout.addWidget(QLabel("Load:"))
            layout.addWidget(self.load)
            layout.addWidget(QLabel("Fan Airflow:"))
            layout.addWidget(self.fan_airflow)
            layout.addWidget(QLabel("Fan Efficiency:"))
            layout.addWidget(self.fan_efficiency)
            layout.addWidget(QLabel("Dust Amount:"))
            layout.addWidget(self.dust_amount)
            layout.addWidget(QLabel("Heat Sink Efficiency:"))
            layout.addWidget(self.heat_sink_efficiency)
            layout.addWidget(QLabel("Heat Sink Surface Area:"))
            layout.addWidget(self.heat_sink_sa)
            
        self.setLayout(layout)
    
    def get_data(self):
        if self.cooling_type == "Immersion":
            return {
                "coolant_temp": self.coolant_temp.value(),
                "server_count": self.server_count.value(),
                "surface_area": self.surface_area.value(),
                "load": self.load.value(),
                "run_time": self.run_time.value(),
                "distance": self.distance.value(),
                "insulation_type": self.insulation_type.currentText(),
                "fluid_type": self.fluid_type.currentText(),
                "flow_rate": self.flow_rate.value(),
                "flow_area": self.flow_area.value()
            }
        else:
            return {
                "ambient_temp": self.ambient_temp.value(),
                "server_count": self.server_count.value(),
                "load": self.load.value(),
                "fan_airflow": self.fan_airflow.value(),
                "fan_efficiency": self.fan_efficiency.value(),
                "dust_amount": self.dust_amount.value(),
                "heat_sink_efficiency": self.heat_sink_efficiency.value(),
                "heat_sink_sa": self.heat_sink_sa.value()
            }

class RackDataWindow(QWidget):
    """A separate window for rack data entry."""
    def __init__(self, cooling_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rack Data Entry")
        self.setMinimumSize(350, 500)
        self.cooling_type = cooling_type
        self.rack_id = None

        self.data_layout = QVBoxLayout()
        self.current_rack_label = QLabel("No rack selected")
        self.data_layout.addWidget(self.current_rack_label)

        self.data_entry_widget = RackDataDialog(self.cooling_type)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.data_entry_widget)
        self.data_layout.addWidget(scroll)

        self.save_btn = QPushButton("Save Data")
        self.data_layout.addWidget(self.save_btn)

        self.setLayout(self.data_layout)

    def set_rack(self, rack_id, data, cooling_type):
        self.rack_id = rack_id
        self.current_rack_label.setText(f"Rack {rack_id}")
        
        if self.cooling_type != cooling_type:
            self.data_layout.removeWidget(self.data_entry_widget)
            self.data_entry_widget.deleteLater()
            self.data_entry_widget = RackDataDialog(cooling_type)
            scroll = self.data_layout.itemAt(1).widget()
            scroll.setWidget(self.data_entry_widget)
            self.cooling_type = cooling_type
        
        if data:
            if cooling_type == "Immersion":
                self.data_entry_widget.coolant_temp.setValue(data.get("coolant_temp", 0))
                self.data_entry_widget.server_count.setValue(data.get("server_count", 1))
                self.data_entry_widget.surface_area.setValue(data.get("surface_area", 0))
                self.data_entry_widget.load.setValue(data.get("load", 0))
                self.data_entry_widget.run_time.setValue(data.get("run_time", 0))
                self.data_entry_widget.distance.setValue(data.get("distance", 0))
                insulation_index = self.data_entry_widget.insulation_type.findText(data.get("insulation_type", ""))
                if insulation_index >= 0:
                    self.data_entry_widget.insulation_type.setCurrentIndex(insulation_index)
                fluid_index = self.data_entry_widget.fluid_type.findText(data.get("fluid_type", ""))
                if fluid_index >= 0:
                    self.data_entry_widget.fluid_type.setCurrentIndex(fluid_index)
                self.data_entry_widget.flow_rate.setValue(data.get("flow_rate", 0))
                self.data_entry_widget.flow_area.setValue(data.get("flow_area", 0))
            else:
                self.data_entry_widget.ambient_temp.setValue(data.get("ambient_temp", 0))
                self.data_entry_widget.server_count.setValue(data.get("server_count", 1))
                self.data_entry_widget.load.setValue(data.get("load", 0))
                self.data_entry_widget.fan_airflow.setValue(data.get("fan_airflow", 0))
                self.data_entry_widget.fan_efficiency.setValue(data.get("fan_efficiency", 0))
                self.data_entry_widget.dust_amount.setValue(data.get("dust_amount", 0))
                self.data_entry_widget.heat_sink_efficiency.setValue(data.get("heat_sink_efficiency", 0))
                self.data_entry_widget.heat_sink_sa.setValue(data.get("heat_sink_sa", 0))

    def get_data(self):
        return self.data_entry_widget.get_data()

class DataCenterSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Center Cooling Efficiency Simulator")
        self.rack_data = {}  
        self.current_cooling_type = "Immersion"
        self.data_window = None  
        self.current_rack_id = None  
        self.current_image_path = image_path_immersion
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        cooling_group = QGroupBox("Cooling Type")
        cooling_layout = QVBoxLayout()
        self.cooling_selector = QComboBox()
        self.cooling_selector.addItems(["Immersion Cooling", "Air Cooling"])
        self.cooling_selector.currentTextChanged.connect(self.change_cooling_type)
        cooling_layout.addWidget(self.cooling_selector)
        self.calculate_btn = QPushButton("Calculate Efficiency")
        self.calculate_btn.clicked.connect(self.calculate_efficiency)
        cooling_layout.addWidget(self.calculate_btn)
        self.apply_all_btn = QPushButton("Apply Current Rack to All")
        self.apply_all_btn.clicked.connect(self.apply_to_all)
        cooling_layout.addWidget(self.apply_all_btn)
        self.output_toggle = QPushButton("Show Output")
        self.output_toggle.setCheckable(True)
        self.output_toggle.toggled.connect(self.toggle_output)
        cooling_layout.addWidget(self.output_toggle)
        cooling_group.setLayout(cooling_layout)
        left_layout.addWidget(cooling_group)

        self.output_panel = QGroupBox("Simulation Output")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        self.output_panel.setLayout(output_layout)
        self.output_panel.setVisible(False)
        left_layout.addWidget(self.output_panel)
        left_layout.addStretch()
        main_layout.addWidget(left_panel, 1)  

        
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        
        image_container = QWidget()
        image_layout = QVBoxLayout()
        image_container.setLayout(image_layout)
        self.dc_image = QLabel()
        self.dc_image.setScaledContents(True)
        self.dc_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.dc_image)
        right_layout.addWidget(image_container)

        
        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_container.setLayout(button_layout)
        column_labels = QHBoxLayout()
        column_labels.setSpacing(10)
        for col in range(5):
            label = QLabel(chr(65+col))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            column_labels.addWidget(label)
        button_layout.addLayout(column_labels)

        self.rack_grid = QWidget()
        self.rack_layout = QGridLayout(self.rack_grid)
        self.rack_layout.setSpacing(4)
        self.rack_layout.setContentsMargins(0, 0, 0, 0)
        self.rack_buttons = []
        for col in range(5):
            for row in range(12):
                rack_id = f"{chr(65+col)}{row+1}"
                btn = QPushButton(str(row+1))
                btn.setObjectName(rack_id)
                btn.clicked.connect(self.rack_clicked)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                self.rack_layout.addWidget(btn, row, col)
                self.rack_buttons.append(btn)
        button_layout.addWidget(self.rack_grid)
        button_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(button_container)

        main_layout.addWidget(right_panel, 3)

        self.setCentralWidget(main_widget)
        self.show()  
        self.showMaximized()  
        self.update_image()

    def resizeEvent(self, event):
        self.update_image()
        self.adjust_rack_grid()
        return super().resizeEvent(event)

    def update_image(self):
        
        if hasattr(self, "dc_image"):
            right_panel = self.centralWidget().layout().itemAt(1).widget()
            width = right_panel.width()
            height = right_panel.height()
            img_height = int(height * 0.45)
            img_width = int(width * 0.9)
            pixmap = QPixmap(self.current_image_path)
            if not pixmap.isNull():
                self.dc_image.setPixmap(pixmap.scaled(img_width, img_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.dc_image.setMinimumSize(1, 1)
                self.dc_image.setMaximumSize(img_width, img_height)

    def adjust_rack_grid(self):
        
        if not self.rack_buttons:
            return
        grid_widget = self.rack_grid
        grid_width = grid_widget.width()
        grid_height = grid_widget.height()
        cols = 5
        rows = 12
        btn_width = max(40, grid_width // cols - 8)
        btn_height = max(24, grid_height // rows - 8)
        font_size = max(8, min(btn_width, btn_height) // 3)
        for btn in self.rack_buttons:
            btn.setMinimumSize(0, 0)
            btn.setMaximumSize(16777215, 16777215)
            
            font = btn.font()
            font.setPointSize(font_size)
            btn.setFont(font)

    def rack_clicked(self):
        sender = self.sender()
        rack_id = sender.objectName()
        self.current_rack_id = rack_id  
        
        if self.data_window is None:
            self.data_window = RackDataWindow(self.current_cooling_type)
            self.data_window.save_btn.clicked.connect(self.save_data)
        
        data = self.rack_data.get(rack_id, None)
        self.data_window.set_rack(rack_id, data, self.current_cooling_type)
        self.data_window.show()
        self.data_window.raise_()
        self.data_window.activateWindow()

    def save_data(self):
        
        if self.data_window is None or self.data_window.rack_id is None:
            return
        rack_id = self.data_window.rack_id
        
        self.rack_data[rack_id] = dict(self.data_window.get_data())

    def change_cooling_type(self):
        cooling_text = self.cooling_selector.currentText()
        self.current_cooling_type = "Immersion" if "Immersion" in cooling_text else "Air"
        self.rack_data = {}
        
        if self.current_cooling_type == "Immersion":
            self.current_image_path = image_path_immersion
        else:
            self.current_image_path = image_path_air
        self.update_image()
        if self.data_window is not None:
            self.data_window.set_rack(self.data_window.rack_id, None, self.current_cooling_type)

    def apply_to_all(self):
        
        if self.data_window is None or self.data_window.rack_id is None:
            return
        current_rack = self.data_window.rack_id
        if current_rack not in self.rack_data:
            self.save_data()
        
        current_data = dict(self.rack_data[current_rack])
        for col in range(5):
            for row in range(12):
                rack_id = f"{chr(65+col)}{row+1}"
                self.rack_data[rack_id] = dict(current_data)

    def toggle_output(self, checked):
        self.output_panel.setVisible(checked)

    def calculate_efficiency(self):
        """Calculate efficiency for all racks using provided formulas"""
        if not self.rack_data:
            self.output_text.setText("No rack data available. Please enter data first.")
            return
            
        output_text = "Cooling System Performance Analysis\n"
        output_text += "="*50 + "\n\n"
        
        for rack_id, data in self.rack_data.items():
            output_text += f"Rack {rack_id}:\n"
            
            if self.current_cooling_type == "Immersion":
                try:
                    results = CoolingCalculations.calculateICoolingEnergy(
                        tCoolant=data.get("coolant_temp", 25),
                        n=data.get("server_count", 20),
                        SA=data.get("surface_area", 0.5),
                        L=data.get("load", 200),
                        tau=data.get("run_time", 0),
                        D=data.get("distance", 5),
                        insulation=data.get("insulation_type", "Standard Fiberglass"),
                        fluidType=data.get("fluid_type", "3M Novec 7000"),
                        Q=data.get("flow_rate", 0.05),
                        Aflow=data.get("flow_area", 0.00785),
                        Lchar=0.01,
                        val=int(rack_id[1:]),
                        L_pipe=20
                    )
                    output_text += f"  Server Temperature: {results['server_temp']} °C\n"
                    output_text += f"  Pump Power: {results['pump_power']} kW\n"
                    output_text += f"  Heat Exchanger Power: {results['heat_exchanger_power']} kW\n"
                    output_text += f"  Total Cooling Energy: {results['total_cooling_energy']} kWh/year\n"
                    output_text += f"  Annual Cost: ${results['annual_cost']}\n\n"
                except Exception as e:
                    output_text += f"  Error: {e}\n"
                    continue
            else:
                try:
                    results = CoolingCalculations.calculateACoolingEnergy(
                        tAmbient=data.get("ambient_temp", 25),
                        n=data.get("server_count", 20),
                        l=data.get("load", 200),
                        fanAirflow=data.get("fan_airflow", 0.085),
                        fanEfficiency=data.get("fan_efficiency", 0.55),
                        dustAmount=data.get("dust_amount", 0.1),
                        heatSinkEfficiency=data.get("heat_sink_efficiency", 0.75),
                        heatSinkSA=data.get("heat_sink_sa", 1.2),
                        duct_length=20,
                        duct_diameter=0.1,
                        safety_margin=True,
                        chiller_cop=3.0,
                        electricity_cost=0.15
                    )
                    output_text += f"  Server Temperature: {results['server_temp']} °C\n"
                    output_text += f"  Fan Power: {results['fan_power']} kW\n"
                    output_text += f"  Chiller Power: {results['chiller_power']} kW\n"
                    output_text += f"  Total Cooling Energy: {results['total_cooling_energy']} kWh/year\n"
                    output_text += f"  Annual Cost: ${results['annual_cost']}\n\n"
                except Exception as e:
                    output_text += f"  Error: {e}\n"
                    continue
        
        self.output_text.setText(output_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataCenterSimulator()
    window.show()  
    window.showMaximized()  
    sys.exit(app.exec())