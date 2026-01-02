import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button, RadioButtons, TextBox
from collections import deque
import numpy as np
import cv2
from helpers import calculate_angle

class Dashboard:
    def __init__(self, config_callback=None, calibration_callback=None, min_angle_callback=None, 
                 min_angle=0, max_angle=0, max_points=100):
        self.max_points = max_points
        self.data = deque([0] * max_points, maxlen=max_points)
        self.config_callback = config_callback
        self.calibration_callback = calibration_callback
        self.min_angle_callback = min_angle_callback
        
        # Active Configuration (for static display)
        self.min_angle = min_angle
        self.max_angle = max_angle
        
        # Calibration State
        self.calibration_mode = 0 # 0: Off, 1: Color, 2: Input PSI, 3: Min Angle, 4: Max Angle
        self.calib_min_psi = 0
        self.calib_max_psi = 100
        self.calib_min_angle = 0
        self.calib_max_angle = 0
        self.current_raw_angle = 0 # Store latest angle for capture
        
        # Enable Interactive Mode
        plt.ion()
        
        # Create the main figure
        self.fig = plt.figure(figsize=(14, 8))
        self.fig.canvas.manager.set_window_title("Digital Retrofitting Dashboard")
        
        # Grid Layout: 3 rows, 2 columns
        self.gs = gridspec.GridSpec(3, 2, width_ratios=[1, 1], height_ratios=[1, 1, 0.5])
        
        # 1. Webcam Feed (Left Half)
        self.ax_webcam = self.fig.add_subplot(self.gs[:, 0])
        self.ax_webcam.set_title("Live Webcam Feed")
        self.ax_webcam.axis('off')
        self.im_webcam = None

        # 2. Live Graph (Top Right)
        self.ax_graph = self.fig.add_subplot(self.gs[0, 1])
        self.line, = self.ax_graph.plot(self.data, color='red', linewidth=2)
        self.ax_graph.set_title("Pressure History")
        self.ax_graph.set_ylabel("PSI")
        self.ax_graph.set_xlabel("Time")
        self.ax_graph.set_ylim(0, 100)
        self.ax_graph.grid(True, linestyle='--', alpha=0.5)

        # 3. PSI Reading (Middle Right)
        self.ax_psi = self.fig.add_subplot(self.gs[1, 1])
        self.ax_psi.axis('off')
        self.text_psi = self.ax_psi.text(0.5, 0.5, "--.- PSI", 
                                        ha='center', va='center', fontsize=40, color='gray', fontweight='bold')

        # 4. Configuration (Bottom Right)
        self.ax_config = self.fig.add_subplot(self.gs[2, 1])
        self.ax_config.set_title("Configuration")
        self.ax_config.axis('off')
        
        # Calibrate Button (Centered in right panel)
        # Right panel x range is roughly 0.5 to 1.0. Center is 0.75.
        # Button width is 0.15. Start x = 0.75 - (0.15/2) = 0.675
        self.ax_calib_btn = self.fig.add_axes([0.675, 0.1, 0.15, 0.08])
        self.btn_calib = Button(self.ax_calib_btn, 'Calibrate Gauge')
        self.btn_calib.on_clicked(self.start_calibration)
        
        # --- Calibration Widgets (Hidden initially) ---
        self.calib_widgets = [] # Stores Axes
        self.calib_components = [] # Stores Widgets (Buttons, TextBoxes)
        
        plt.tight_layout()
        plt.show(block=False)

    def on_color_change(self, label):
        color_map = {'Red': 'red', 'Black': 'black', 'Blue': 'blue'}
        selected_color = color_map.get(label, 'red')
        print(f"Needle color changed to: {selected_color}")
        if self.config_callback:
            self.config_callback(selected_color)

    def start_calibration(self, event):
        self.calibration_mode = 1
        self.clear_right_panel()
        self.setup_calibration_step1()

    def clear_right_panel(self):
        # Hide normal widgets
        self.ax_graph.set_visible(False)
        self.ax_psi.set_visible(False)
        self.ax_config.set_visible(False)
        self.ax_calib_btn.set_visible(False)
        
    def cleanup_calibration_widgets(self):
        # Safely disconnect and remove widgets to prevent event conflicts
        for widget in self.calib_components:
            if isinstance(widget, TextBox):
                widget.stop_typing()
            if hasattr(widget, 'disconnect_events'):
                widget.disconnect_events()
        
        for ax in self.calib_widgets:
            if ax in self.fig.axes:
                ax.remove()
        
        self.calib_components = []
        self.calib_widgets = []

    def restore_right_panel(self):
        # Show normal widgets
        self.ax_graph.set_visible(True)
        self.ax_psi.set_visible(True)
        self.ax_config.set_visible(True)
        self.ax_calib_btn.set_visible(True)
        
        self.cleanup_calibration_widgets()
        self.calibration_mode = 0

    def setup_calibration_step1(self):
        # Step 1: Needle Color
        ax_title = self.fig.add_subplot(self.gs[0, 1])
        ax_title.axis('off')
        ax_title.text(0.5, 0.5, "Step 1: Select Needle Color", ha='center', fontsize=16)
        self.calib_widgets.append(ax_title)

        # Radio Buttons for Needle Color
        ax_radio = self.fig.add_axes([0.65, 0.4, 0.2, 0.2]) 
        self.radio = RadioButtons(ax_radio, ('Red', 'Black', 'Blue'))
        self.radio.on_clicked(self.on_color_change)
        self.calib_widgets.append(ax_radio)
        self.calib_components.append(self.radio)
        
        # Next Button
        ax_next = self.fig.add_axes([0.7, 0.2, 0.1, 0.05])
        self.btn_next = Button(ax_next, 'Next')
        self.btn_next.on_clicked(self.on_step1_next)
        self.calib_widgets.append(ax_next)
        self.calib_components.append(self.btn_next)

    def on_step1_next(self, event):
        self.cleanup_calibration_widgets()
        self.calibration_mode = 2
        self.setup_calibration_step2()

    def setup_calibration_step2(self):
        # Step 2: Input PSI Range
        ax_title = self.fig.add_subplot(self.gs[0, 1])
        ax_title.axis('off')
        ax_title.text(0.5, 0.5, "Step 2: Enter Gauge Range", ha='center', fontsize=16)
        self.calib_widgets.append(ax_title)

        # Min PSI Input
        ax_min = self.fig.add_axes([0.6, 0.5, 0.1, 0.05])
        self.txt_min = TextBox(ax_min, 'Min PSI: ', initial="0")
        self.calib_widgets.append(ax_min)
        self.calib_components.append(self.txt_min)
        
        # Max PSI Input
        ax_max = self.fig.add_axes([0.8, 0.5, 0.1, 0.05])
        self.txt_max = TextBox(ax_max, 'Max PSI: ', initial="100")
        self.calib_widgets.append(ax_max)
        self.calib_components.append(self.txt_max)
        
        # Next Button
        ax_next = self.fig.add_axes([0.7, 0.3, 0.1, 0.05])
        self.btn_next = Button(ax_next, 'Next')
        self.btn_next.on_clicked(self.on_step2_next)
        self.calib_widgets.append(ax_next)
        self.calib_components.append(self.btn_next)

    def on_step2_next(self, event):
        try:
            self.calib_min_psi = float(self.txt_min.text)
            self.calib_max_psi = float(self.txt_max.text)
            
            self.cleanup_calibration_widgets()
            
            self.calibration_mode = 3
            self.setup_calibration_step3()
        except ValueError:
            print("Invalid PSI input")

    def setup_calibration_step3(self):
        # Step 3: Capture Min Angle
        ax_instr = self.fig.add_subplot(self.gs[0, 1])
        ax_instr.axis('off')
        ax_instr.text(0.5, 0.5, f"Step 3: Set Needle to {self.calib_min_psi} PSI\n\nAlign gauge in the green circle.\nEnsure needle is detected.", ha='center', fontsize=14)
        self.calib_widgets.append(ax_instr)
        
        ax_cap = self.fig.add_axes([0.7, 0.3, 0.15, 0.05])
        self.btn_cap_min = Button(ax_cap, 'Capture Min Angle')
        self.btn_cap_min.on_clicked(self.on_capture_min)
        self.calib_widgets.append(ax_cap)
        self.calib_components.append(self.btn_cap_min)

    def on_capture_min(self, event):
        self.calib_min_angle = self.current_raw_angle
        print(f"Captured Min Angle: {self.calib_min_angle}")
        
        # Immediate update for visual feedback
        if self.min_angle_callback:
            self.min_angle_callback(self.calib_min_angle)
        
        self.cleanup_calibration_widgets()
        
        self.calibration_mode = 4
        self.setup_calibration_step4()

    def setup_calibration_step4(self):
        # Step 4: Capture Max Angle
        ax_instr = self.fig.add_subplot(self.gs[0, 1])
        ax_instr.axis('off')
        ax_instr.text(0.5, 0.5, f"Step 4: Set Needle to {self.calib_max_psi} PSI\n\nMove needle to max position.", ha='center', fontsize=14)
        self.calib_widgets.append(ax_instr)
        
        ax_cap = self.fig.add_axes([0.7, 0.3, 0.15, 0.05])
        self.btn_cap_max = Button(ax_cap, 'Capture Max Angle')
        self.btn_cap_max.on_clicked(self.on_capture_max)
        self.calib_widgets.append(ax_cap)
        self.calib_components.append(self.btn_cap_max)

    def on_capture_max(self, event):
        self.calib_max_angle = self.current_raw_angle
        print(f"Captured Max Angle: {self.calib_max_angle}")
        
        # Finish
        if self.calibration_callback:
            self.calibration_callback(
                self.calib_min_angle, self.calib_max_angle,
                self.calib_min_psi, self.calib_max_psi
            )
            
        self.restore_right_panel()

    def update(self, processed_frame, psi_value, raw_angle=None):
        """
        Updates the dashboard with new data.
        """
        self.current_raw_angle = raw_angle if raw_angle is not None else 0
        
        # Update Webcam
        if processed_frame is not None:
            h, w = processed_frame.shape[:2]
            cx, cy = int(w/2), int(h/2)
            # Expanded radius to match typical gauge detection size (approx 45% of height)
            r = int(h * 0.45)
            
            # --- Static Overlays (Always Visible) ---
            # 1. Green Guide Circle
            cv2.circle(processed_frame, (cx, cy), r, (0, 255, 0), 2)
            cv2.putText(processed_frame, "ALIGN GAUGE", (cx-60, cy-r-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 2. Blue Ticker Lines (Based on current calibration)
            # Draw short ticks (15% of radius)
            tick_len = int(r * 0.15)
            
            # Min Angle Ticker
            rad_min = np.radians(self.min_angle)
            x_min_out = int(cx + r * np.cos(rad_min))
            y_min_out = int(cy - r * np.sin(rad_min))
            x_min_in = int(cx + (r - tick_len) * np.cos(rad_min))
            y_min_in = int(cy - (r - tick_len) * np.sin(rad_min))
            
            cv2.line(processed_frame, (x_min_in, y_min_in), (x_min_out, y_min_out), (255, 0, 0), 3)
            cv2.putText(processed_frame, "MIN", (x_min_out, y_min_out), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Max Angle Ticker
            rad_max = np.radians(self.max_angle)
            x_max_out = int(cx + r * np.cos(rad_max))
            y_max_out = int(cy - r * np.sin(rad_max))
            x_max_in = int(cx + (r - tick_len) * np.cos(rad_max))
            y_max_in = int(cy - (r - tick_len) * np.sin(rad_max))
            
            cv2.line(processed_frame, (x_max_in, y_max_in), (x_max_out, y_max_out), (255, 0, 0), 3)
            cv2.putText(processed_frame, "MAX", (x_max_out, y_max_out), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Draw Calibration Overlay if needed
            if self.calibration_mode > 0:
                if self.calibration_mode in [3, 4]:
                    cv2.putText(processed_frame, f"Angle: {self.current_raw_angle:.1f}", (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Convert BGR (OpenCV) to RGB (Matplotlib)
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            if self.im_webcam is None:
                self.im_webcam = self.ax_webcam.imshow(frame_rgb)
            else:
                self.im_webcam.set_data(frame_rgb)

        # Only update Graph/PSI if NOT in calibration mode
        if self.calibration_mode == 0:
            # Update PSI Text & Graph
            if psi_value is not None:
                self.text_psi.set_text(f"{psi_value:.1f} PSI")
                
                # Dynamic Color Coding
                if psi_value > 90: 
                    self.text_psi.set_color('red')
                elif psi_value > 75: 
                    self.text_psi.set_color('orange')
                else: 
                    self.text_psi.set_color('green')
                
                self.data.append(psi_value)
                
                # Auto-scale Y-axis
                if psi_value > self.ax_graph.get_ylim()[1]:
                    self.ax_graph.set_ylim(0, psi_value * 1.2)
            else:
                self.text_psi.set_text("NO READING")
                self.text_psi.set_color('gray')
                self.data.append(self.data[-1] if self.data else 0)

            self.line.set_ydata(self.data)
        
        # Redraw
        plt.pause(0.001)

    def close(self):
        plt.close(self.fig)