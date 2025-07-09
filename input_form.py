import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import time

def parse_time_str(s):
    try:
        return time.fromisoformat(s)
    except ValueError:
        raise ValueError(f"Invalid time format: {s}. Use HH:MM")

def show_input_form():
    def submit():
        try:
            # Parse and validate parameters
            threshold_ticks = int(entry_threshold_ticks.get())
            retracement_ratio = float(entry_retrace_ratio.get()) / 100  # convert from % to ratio
            retracement_bars = int(entry_retrace_bars.get())
            market_open = parse_time_str(entry_market_open.get())
            retracement_start = parse_time_str(entry_retrace_start.get())
            entry_deadline = parse_time_str(entry_entry_deadline.get())
            market_close = parse_time_str(entry_market_close.get())
            validation_buffer_ticks = int(entry_validation_buffer_ticks.get())
            tp_multiplier = float(entry_tp_multiplier.get()) / 100  # convert from % to ratio
            sl_multiplier = float(entry_sl_multiplier.get()) / 100  # convert from % to ratio
            sl_point_limit = float(entry_sl_points.get())

            # Re-entry logic commented out for now
            # reentry_deadline = parse_time_str(entry_reentry_dealine.get())
            # reentry_tp_multiplier = float(entry_reentry_tp_multiplier.get()) / 100  # convert from % to ratio
            # reentry_sl_multiplier = float(entry_reentry_sl_multiplier.get()) / 100  # convert from % to ratio
            include_logs = include_logs_var.get()

            if not file_paths:
                raise ValueError("You must select at least one file.")

            # Additional time validation
            if retracement_start < market_open:
                raise ValueError("Retracement start time cannot be before market opens.")
            if entry_deadline > market_close:
                raise ValueError("Entry deadline cannot be after market closes.")
            if retracement_start >= entry_deadline:
                raise ValueError("Retracement start time must be earlier than entry deadline.")
            if market_close < market_open:
                raise ValueError("Market close time cannot be earlier than market open.")

            # Re-entry logic commented out for now
            # if reentry_deadline < market_open or reentry_deadline > market_close:
            #     raise ValueError("Reentry time limit must be in the market day.")

            # Store parameters
            params.update({
                "file_paths": file_paths,
                "threshold_ticks": threshold_ticks,
                "retracement_ratio": retracement_ratio,
                "retracement_bars": retracement_bars,
                "market_open": market_open,
                "retracement_start": retracement_start,
                "entry_deadline": entry_deadline,
                "market_close": market_close,
                "validation_buffer_ticks": validation_buffer_ticks,
                "tp_multiplier": tp_multiplier,
                "sl_multiplier": sl_multiplier,
                "sl_point_limit": sl_point_limit,
                # Re-entry logic commented out for now
                # "reentry_deadline": reentry_deadline,
                # "reentry_tp_multiplier": reentry_tp_multiplier,
                # "reentry_sl_multiplier": reentry_sl_multiplier,
                "include_logs": include_logs
            })

            root.destroy()
        except Exception as e:
            messagebox.showerror("Input Error", str(e))

    def choose_files():
        nonlocal file_paths
        file_paths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
        label_files.config(text=f"Selected: {len(file_paths)} files")

    file_paths = []
    params = {}

    root = tk.Tk()
    root.title("Strategy Parameter Input")

    tk.Button(root, text="Select Text Files", command=choose_files).grid(row=0, column=0, columnspan=2, pady=5)
    label_files = tk.Label(root, text="No files selected.")
    label_files.grid(row=1, column=0, columnspan=2, pady=2)

    tk.Label(root, text="Initial Minimum Ticks Required").grid(row=2, column=0, sticky="e")
    entry_threshold_ticks = tk.Entry(root)
    entry_threshold_ticks.insert(0, "16")
    entry_threshold_ticks.grid(row=2, column=1)

    tk.Label(root, text="Retracement Ratio (%)").grid(row=3, column=0, sticky="e")
    entry_retrace_ratio = tk.Entry(root)
    entry_retrace_ratio.insert(0, "100")
    entry_retrace_ratio.grid(row=3, column=1)

    tk.Label(root, text="Retracement Bar Minimum Count").grid(row=4, column=0, sticky="e")
    entry_retrace_bars = tk.Entry(root)
    entry_retrace_bars.insert(0, "3")
    entry_retrace_bars.grid(row=4, column=1)

    tk.Label(root, text="Market Open (HH:MM)").grid(row=5, column=0, sticky="e")
    entry_market_open = tk.Entry(root)
    entry_market_open.insert(0, "12:30")
    entry_market_open.grid(row=5, column=1)

    tk.Label(root, text="Retracement Start Time (HH:MM)").grid(row=6, column=0, sticky="e")
    entry_retrace_start = tk.Entry(root)
    entry_retrace_start.insert(0, "12:45")
    entry_retrace_start.grid(row=6, column=1)

    tk.Label(root, text="Entry Deadline (HH:MM)").grid(row=7, column=0, sticky="e")
    entry_entry_deadline = tk.Entry(root)
    entry_entry_deadline.insert(0, "14:00")
    entry_entry_deadline.grid(row=7, column=1)

    tk.Label(root, text="Market Close (HH:MM)").grid(row=8, column=0, sticky="e")
    entry_market_close = tk.Entry(root)
    entry_market_close.insert(0, "22:59")
    entry_market_close.grid(row=8, column=1)

    tk.Label(root, text="Validation Buffer Ticks (After 100% Retracement)").grid(row=9, column=0, sticky="e")
    entry_validation_buffer_ticks = tk.Entry(root)
    entry_validation_buffer_ticks.insert(0, "4")
    entry_validation_buffer_ticks.grid(row=9, column=1)

    tk.Label(root, text="TP Multiplier (%)").grid(row=10, column=0, sticky="e")
    entry_tp_multiplier = tk.Entry(root)
    entry_tp_multiplier.insert(0, "100")
    entry_tp_multiplier.grid(row=10, column=1)

    tk.Label(root, text="SL Multiplier (%)").grid(row=11, column=0, sticky="e")
    entry_sl_multiplier = tk.Entry(root)
    entry_sl_multiplier.insert(0, "40")
    entry_sl_multiplier.grid(row=11, column=1)

    tk.Label(root, text="SL Point Limit").grid(row=12, column=0, sticky="e")
    entry_sl_points = tk.Entry(root)
    entry_sl_points.insert(0, "6")
    entry_sl_points.grid(row=12, column=1)

    # Re-entry logic commented out for now
    # tk.Label(root, text="Re-entry Deadline (HH:MM)").grid(row=13, column=0, sticky="e")
    # entry_reentry_dealine = tk.Entry(root)
    # entry_reentry_dealine.insert(0, "13:30")
    # entry_reentry_dealine.grid(row=13, column=1)
    #
    # tk.Label(root, text="Re-entry TP Multiplier (%)").grid(row=14, column=0, sticky="e")
    # entry_reentry_tp_multiplier = tk.Entry(root)
    # entry_reentry_tp_multiplier.insert(0, "100")
    # entry_reentry_tp_multiplier.grid(row=14, column=1)
    #
    # tk.Label(root, text="Re-entry SL Multiplier (%)").grid(row=15, column=0, sticky="e")
    # entry_reentry_sl_multiplier = tk.Entry(root)
    # entry_reentry_sl_multiplier.insert(0, "60")
    # entry_reentry_sl_multiplier.grid(row=15, column=1)

    # Include Logs Checkbox
    include_logs_var = tk.BooleanVar(value=False)  # default: un-checked
    tk.Checkbutton(root, text="Include Logs in Output", variable=include_logs_var).grid(row=13, column=0, sticky="e")

    tk.Button(root, text="Run Analysis", command=submit).grid(row=14, column=0, columnspan=2, pady=10)

    root.mainloop()
    return params
