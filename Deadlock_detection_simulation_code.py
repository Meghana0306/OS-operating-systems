import psutil
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import numpy as np

class AIDeadlockDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Process Monitoring Dashboard")
        self.root.geometry("1600x900") 

        self.cpu_history = []
        self.time_history = []

        self.risk_history = []
        self.time_history_risk = []

        self.processes = []

        self.ai_model = None  

        style = ttk.Style()
        style.theme_use("clam")

        self.configure_styles()

        # Setup GUI components
        self.setup_gui()

        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

    def configure_styles(self):
        style = ttk.Style()
        # Configure general styles
        style.configure("TLabel", font=("Arial", 40), background="#f0f0f0")
        style.configure("TButton", font=("Arial", 28), background="#ff4d4d", foreground="white")
        style.configure("Treeview.Heading", font=("Arial", 28, "bold"), background="#d9e6f2", foreground="#333333")
        style.configure("Treeview", font=("Arial", 24), rowheight=50, background="#ffffff", foreground="#333333")
        style.map("Treeview", background=[("selected", "#add8e6")])

        # Custom style for frames
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabelframe", background="#f0f0f0", foreground="#333333")
        style.configure("TLabelframe.Label", font=("Arial", 28, "bold"), background="#f0f0f0", foreground="#333333")

    def setup_gui(self):
        # Set background color for the root window
        self.root.configure(bg="#f0f0f0")

        # Create a canvas and scrollbar for the entire window
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Section 1: Title and Metrics
        section1_frame = ttk.Frame(scrollable_frame)
        section1_frame.pack(fill="x", pady=20)

        # Title Label
        title_label = ttk.Label(section1_frame, text="Real-Time Process Monitoring Dashboard", font=("Arial", 56, "bold"), background="#f0f0f0", foreground="#2c3e50")
        title_label.pack(pady=20)

        # Frame for System Metrics
        metrics_frame = ttk.Frame(section1_frame)
        metrics_frame.pack(pady=20, padx=80, fill="x")

        # CPU Usage Label
        self.cpu_label = ttk.Label(metrics_frame, text="CPU Usage: 0.0% (Normal)", font=("Arial", 40), foreground="#2c3e50")
        self.cpu_label.pack(side="left", padx=80)

        # Memory Usage Label
        self.memory_label = ttk.Label(metrics_frame, text="Memory Usage: 0.0% (Normal)", font=("Arial", 40), foreground="#2c3e50")
        self.memory_label.pack(side="left", padx=80)

        # Deadlock Status Label
        self.deadlock_label = ttk.Label(metrics_frame, text="Deadlock Status: None Detected", font=("Arial", 40), foreground="#2c3e50")
        self.deadlock_label.pack(side="left", padx=80)

        # Section 2: Process List Table
        section2_frame = ttk.Frame(scrollable_frame)
        section2_frame.pack(fill="x", pady=20)

        self.setup_process_table(section2_frame)

        # Section 3: Side-by-Side Time-Based Charts, Bar Chart, and Quit Button
        section3_frame = ttk.Frame(scrollable_frame)
        section3_frame.pack(fill="x", pady=20)

        # Frame for Side-by-Side Time-Based Charts
        time_charts_frame = ttk.Frame(section3_frame)
        time_charts_frame.pack(pady=20, padx=80, fill="x")

        # CPU Usage History Chart (Left)
        self.setup_cpu_chart(time_charts_frame)

        # Deadlock Risk Over Time Chart (Right)
        self.setup_deadlock_risk_time_chart(time_charts_frame)

        # Deadlock Risk Bar Chart
        self.setup_deadlock_risk_chart(section3_frame)

        # Quit Button
        quit_button = ttk.Button(section3_frame, text="Quit", command=self.quit, style="TButton")
        quit_button.pack(pady=20)

    def setup_process_table(self, parent_frame):
        # Frame for the table
        table_frame = ttk.LabelFrame(parent_frame, text="Process List", padding=30, labelanchor="n")
        table_frame.pack(pady=20, padx=80, fill="x")

        # Define columns
        columns = ("PID", "Name", "CPU %", "Memory %", "Status")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)  # Reduced height to fit section

        self.table.heading("PID", text="PID")
        self.table.heading("Name", text="Name")
        self.table.heading("CPU %", text="CPU %")
        self.table.heading("Memory %", text="Memory %")
        self.table.heading("Status", text="Status")

        self.table.column("PID", width=200, anchor="center")
        self.table.column("Name", width=400, anchor="center")
        self.table.column("CPU %", width=200, anchor="center")
        self.table.column("Memory %", width=200, anchor="center")
        self.table.column("Status", width=300, anchor="center")

        self.table.tag_configure("oddrow", background="#e6f0fa")
        self.table.tag_configure("evenrow", background="#ffffff")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)

    def setup_cpu_chart(self, parent_frame):
        chart_frame = ttk.LabelFrame(parent_frame, text="CPU Usage History Over Time", padding=20, labelanchor="n")
        chart_frame.pack(side="left", padx=20, fill="both", expand=True)

        self.fig_cpu, self.ax_cpu = plt.subplots(figsize=(10, 6))  # Adjusted height to fit section
        self.ax_cpu.set_title("CPU Usage History Over Time", fontsize=24, color="#2c3e50")
        self.ax_cpu.set_xlabel("Time (s)", fontsize=20, color="#2c3e50")
        self.ax_cpu.set_ylabel("CPU Usage (%)", fontsize=20, color="#2c3e50")
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.tick_params(axis='both', labelsize=16, colors="#2c3e50")
        self.ax_cpu.grid(True, linestyle="--", alpha=0.7)

        # Embed in Tkinter
        self.canvas_cpu = FigureCanvasTkAgg(self.fig_cpu, master=chart_frame)
        self.canvas_cpu.get_tk_widget().pack(fill="both", expand=True)

    def setup_deadlock_risk_time_chart(self, parent_frame):
        # Frame for the deadlock risk over time chart
        chart_frame = ttk.LabelFrame(parent_frame, text="Deadlock Risk Over Time", padding=20, labelanchor="n")
        chart_frame.pack(side="left", padx=20, fill="both", expand=True)

        # Matplotlib figure with increased size
        self.fig_risk_time, self.ax_risk_time = plt.subplots(figsize=(10, 6))  # Adjusted height to fit section
        self.ax_risk_time.set_title("Deadlock Risk Over Time", fontsize=24, color="#2c3e50")
        self.ax_risk_time.set_xlabel("Time (s)", fontsize=20, color="#2c3e50")
        self.ax_risk_time.set_ylabel("Number of High-Risk Processes", fontsize=20, color="#2c3e50")
        self.ax_risk_time.set_ylim(0, 10)
        self.ax_risk_time.tick_params(axis='both', labelsize=16, colors="#2c3e50")
        self.ax_risk_time.grid(True, linestyle="--", alpha=0.7)

        # Embed in Tkinter
        self.canvas_risk_time = FigureCanvasTkAgg(self.fig_risk_time, master=chart_frame)
        self.canvas_risk_time.get_tk_widget().pack(fill="both", expand=True)

    def setup_deadlock_risk_chart(self, parent_frame):
        # Frame for the deadlock risk bar chart
        chart_frame = ttk.LabelFrame(parent_frame, text="Top Processes by CPU Usage (Deadlock Risk)", padding=30, labelanchor="n")
        chart_frame.pack(pady=20, padx=80, fill="x")

        # Matplotlib figure for bar chart
        self.fig_risk, self.ax_risk = plt.subplots(figsize=(16, 6))
        self.ax_risk.set_title("Top Processes by CPU Usage (Deadlock Risk)", fontsize=28, color="#2c3e50")
        self.ax_risk.set_xlabel("Process Name", fontsize=24, color="#2c3e50")
        self.ax_risk.set_ylabel("CPU Usage (%)", fontsize=24, color="#2c3e50")
        self.ax_risk.tick_params(axis='both', labelsize=20, colors="#2c3e50")
        self.ax_risk.grid(True, linestyle="--", alpha=0.7)

        # Embed in Tkinter
        self.canvas_risk = FigureCanvasTkAgg(self.fig_risk, master=chart_frame)
        self.canvas_risk.get_tk_widget().pack(fill="both", expand=True)

    def update_dashboard(self):
        # Fetch system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent

        # Update CPU and Memory Labels with color indicators
        cpu_status = "Normal" if cpu_usage < 80 else "High"
        cpu_color = "#27ae60" if cpu_status == "Normal" else "#e74c3c"
        memory_status = "Normal" if memory_usage < 80 else "High"
        memory_color = "#27ae60" if memory_status == "Normal" else "#e74c3c"
        self.cpu_label.config(text=f"CPU Usage: {cpu_usage:.1f}% ({cpu_status})", foreground=cpu_color)
        self.memory_label.config(text=f"Memory Usage: {memory_usage:.1f}% ({memory_status})", foreground=memory_color)

        # Update Process List and check for deadlocks
        self.processes = self.update_process_table()

        # Detect deadlock (placeholder)
        deadlock_status = self.detect_deadlock(self.processes)
        deadlock_color = "#e74c3c" if deadlock_status == "Deadlock Detected" else "#27ae60"
        self.deadlock_label.config(text=f"Deadlock Status: {deadlock_status}", foreground=deadlock_color)

        # Update CPU Usage History Chart
        self.update_cpu_chart(cpu_usage)

        # Update Deadlock Risk Bar Chart
        self.update_deadlock_risk_chart()

        # Update Deadlock Risk Over Time Chart
        self.update_deadlock_risk_time_chart()

    def update_process_table(self):
        # Clear the table
        for item in self.table.get_children():
            self.table.delete(item)

        # Fetch process details
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "memory_percent": proc.info['memory_percent'],
                    "status": proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage (descending)
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

        # Insert top 10 processes with alternating row colors
        for idx, proc in enumerate(processes[:10]):
            proc_status = "Normal"
            if proc['cpu_percent'] > 90 or proc['memory_percent'] > 90:
                proc_status = "Risk"
            row_tag = "oddrow" if idx % 2 else "evenrow"
            self.table.insert("", "end", values=(
                proc['pid'],
                proc['name'],
                f"{proc['cpu_percent']:.1f}",
                f"{proc['memory_percent']:.1f}",
                f"{proc['status']} ({proc_status})"
            ), tags=(row_tag,))

        return processes

    def detect_deadlock(self, processes):
        # Placeholder for deadlock detection
        high_risk_count = sum(1 for proc in processes if proc['cpu_percent'] > 90 or proc['memory_percent'] > 90)
        return "Deadlock Detected" if high_risk_count > 3 else "None Detected"

    def update_cpu_chart(self, cpu_usage):
        # Update history
        current_time = time.time() - self.start_time
        self.cpu_history.append(cpu_usage)
        self.time_history.append(current_time)

        # Limit to last 60 seconds
        if len(self.time_history) > 60:
            self.cpu_history.pop(0)
            self.time_history.pop(0)

        # Debug: Print data to ensure it's being generated
        print(f"CPU Chart Data - Time: {self.time_history}, CPU Usage: {self.cpu_history}")

        # Update the plot
        self.ax_cpu.clear()
        self.ax_cpu.plot(self.time_history, self.cpu_history, marker='o', markersize=8, linewidth=2, label="CPU Usage", color="#3498db")
        self.ax_cpu.set_title("CPU Usage History Over Time", fontsize=24, color="#2c3e50")
        self.ax_cpu.set_xlabel("Time (s)", fontsize=20, color="#2c3e50")
        self.ax_cpu.set_ylabel("CPU Usage (%)", fontsize=20, color="#2c3e50")
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.tick_params(axis='both', labelsize=16, colors="#2c3e50")
        self.ax_cpu.grid(True, linestyle="--", alpha=0.7)
        self.ax_cpu.legend(fontsize=16)
        self.canvas_cpu.draw()

    def update_deadlock_risk_chart(self):
        # Get top 5 processes by CPU usage
        top_processes = self.processes[:5]
        if not top_processes:
            print("No processes to display in bar chart")
            return

        # Extract data for the bar chart
        names = [proc['name'][:15] + "..." if len(proc['name']) > 15 else proc['name'] for proc in top_processes]
        cpu_usages = [proc['cpu_percent'] for proc in top_processes]
        risks = [proc['cpu_percent'] > 90 or proc['memory_percent'] > 90 for proc in top_processes]

        # Debug: Print data to ensure it's being generated
        print(f"Bar Chart Data - Names: {names}, CPU Usages: {cpu_usages}, Risks: {risks}")

        # Set colors based on risk
        colors = ["#e74c3c" if risk else "#3498db" for risk in risks]

        # Update the bar chart
        self.ax_risk.clear()
        bars = self.ax_risk.bar(names, cpu_usages, color=colors, edgecolor="#2c3e50", linewidth=1.5)
        self.ax_risk.set_title("Top Processes by CPU Usage (Deadlock Risk)", fontsize=28, color="#2c3e50")
        self.ax_risk.set_xlabel("Process Name", fontsize=24, color="#2c3e50")
        self.ax_risk.set_ylabel("CPU Usage (%)", fontsize=24, color="#2c3e50")
        self.ax_risk.tick_params(axis='both', labelsize=20, colors="#2c3e50")
        self.ax_risk.grid(True, linestyle="--", alpha=0.7)

        # Rotate x-axis labels for better readability
        plt.setp(self.ax_risk.get_xticklabels(), rotation=45, ha="right")

        # Add value labels on top of bars
        for bar in bars:
            yval = bar.get_height()
            self.ax_risk.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval:.1f}%", ha="center", va="bottom", fontsize=16, color="#2c3e50")

        self.canvas_risk.draw()

    def update_deadlock_risk_time_chart(self):
        # Calculate the number of high-risk processes
        high_risk_count = sum(1 for proc in self.processes if proc['cpu_percent'] > 90 or proc['memory_percent'] > 90)

        # Update history
        current_time = time.time() - self.start_time
        self.risk_history.append(high_risk_count)
        self.time_history_risk.append(current_time)

        # Limit to last 60 seconds
        if len(self.time_history_risk) > 60:
            self.risk_history.pop(0)
            self.time_history_risk.pop(0)

        print(f"Risk Time Chart Data - Time: {self.time_history_risk}, Risk Count: {self.risk_history}")

        self.ax_risk_time.clear()
        self.ax_risk_time.plot(self.time_history_risk, self.risk_history, marker='o', markersize=8, linewidth=2, label="High-Risk Processes", color="#e74c3c")
        self.ax_risk_time.set_title("Deadlock Risk Over Time", fontsize=24, color="#2c3e50")
        self.ax_risk_time.set_xlabel("Time (s)", fontsize=20, color="#2c3e50")
        self.ax_risk_time.set_ylabel("Number of High-Risk Processes", fontsize=20, color="#2c3e50")
        self.ax_risk_time.set_ylim(0, 10)
        self.ax_risk_time.tick_params(axis='both', labelsize=16, colors="#2c3e50")
        self.ax_risk_time.grid(True, linestyle="--", alpha=0.7)
        self.ax_risk_time.legend(fontsize=16)
        self.canvas_risk_time.draw()

    def update_loop(self):
        self.start_time = time.time()
        while self.running:
            self.update_dashboard()
            time.sleep(1)  

    def quit(self):
        self.running = False
        self.update_thread.join(timeout=2)
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AIDeadlockDashboard(root)
    root.mainloop()
