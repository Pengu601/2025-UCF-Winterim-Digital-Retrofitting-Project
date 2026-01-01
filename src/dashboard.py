import matplotlib.pyplot as plt
from collections import deque
import numpy as np

class TelemetryGraph:
    def __init__(self, max_points=100):
        self.max_points = max_points
        # Pre-fill with zeros so the graph line starts "full"
        self.data = deque([0] * max_points, maxlen=max_points)
        
        # 1. Enable Interactive Mode (CRITICAL)
        plt.ion() 
        
        # 2. Create the Window
        # This will pop up a separate window named "Figure 1"
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot(self.data, color='red', linewidth=2)
        
        # Styling
        self.ax.set_title("Real-Time Telemetry")
        self.ax.set_ylabel("Pressure (PSI)")
        self.ax.set_xlabel("Time (Frames)")
        self.ax.set_ylim(0, 100) 
        self.ax.grid(True, linestyle='--', alpha=0.5)
        
        # 3. Force the window to appear immediately
        plt.show(block=False)

    def update(self, new_value):
        """
        Adds a new reading and refreshes the graph.
        """
        self.data.append(new_value)
        self.line.set_ydata(self.data)
        
        # Optional: Auto-scale Y-axis if pressure exceeds 100
        if new_value > self.ax.get_ylim()[1]:
             self.ax.set_ylim(0, new_value * 1.2)
        
        # 4. The "Heartbeat" (CRITICAL)
        # This forces the graph to redraw and handles window events (clicks/moves)
        # Without this, the window freezes.
        plt.pause(0.001)

    def close(self):
        plt.close(self.fig)