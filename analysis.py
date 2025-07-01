# --- Imports ---
import pandas as pd
from datetime import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
from datetime import datetime
from input_form import show_input_form
from consts import *

# --- Load Parameters ---
params = show_input_form()

THRESHOLD_VALUE = params['threshold_ticks'] * TICK_SIZE
MARKET_OPEN = params['market_open']
RETRACEMENT_START = params['retracement_start']
ENTRY_DEADLINE = params['entry_deadline']
MARKET_CLOSE = params['market_close']
RETRACE_RATIO_MINIMUM = params['retracement_ratio']
RETRACE_BAR_COUNT = params['retracement_bars']
VALIDATION_BUFFER = params['validation_buffer_ticks'] * TICK_SIZE
TP_MULTIPLIER = params['tp_multiplier']
SL_MULTIPLIER = params['sl_multiplier']
SL_POINT_LIMIT = params['sl_point_limit']
INCLUDE_LOGS = params['include_logs']

# --- Start GUI file picker ---
root = tk.Tk()
root.withdraw()
file_paths = params['file_paths']

if not file_paths or len(file_paths) == 0:
    messagebox.showerror("Error", "No file selected.")
    exit()

# --- Initialize log collection ---
log_output = ""
file_output = ""

excel_obj = {"Date": '',
                 "Long/Short": '',
                 "Entry Price": '',
                 "Spread": '',
                 "0L": '',
                 "EX": '',
                 "RT %": '',
                 "W/L": '',
                 "Balance": '',
                 "EX while active": '',
                 "En+Sp": '',
                 "EX before 0L": ''}
excel_logs = []

# --- Helper Functions ---
def load_and_split_files(file_paths):
    all_dfs = []

    for file_path in file_paths:
        with open(file_path, "r") as file:
            lines = file.readlines()

        data = []
        for line in lines:
            parts = line.strip().split(";")
            if len(parts) != 6:
                continue

            raw_datetime = parts[0]
            dt_obj = datetime.strptime(raw_datetime, "%Y%m%d %H%M%S")
            current_time = dt_obj.time()

            if not (MARKET_OPEN <= current_time <= MARKET_CLOSE):
                continue

            data.append({
                "Date": dt_obj.date(),
                "Time": current_time,
                "Open": float(parts[1]),
                "High": float(parts[2]),
                "Low": float(parts[3]),
                "Close": float(parts[4])
            })

        df = pd.DataFrame(data)
        for _, group in df.groupby("Date"):
            all_dfs.append(group.reset_index(drop=True))

    return all_dfs

def analyze_v_shape(df_day, day_index):
    global log_output

    zeroL = df_day.iloc[0]['Close']
    set_excel_property('0L', zeroL)

    current_date = df_day.loc[0, 'Date']
    mode = None
    extreme_price = None
    extreme_index = None
    max_spread = 0
    retrace_index = None

    found_extreme = False
    found_retrace = False
    found_validation = False
    entry_index = None
    retracement_locked = False
    retrace_ratio = None

    log(f"[Day {day_index + 1} - {current_date}] Zero Line: {zeroL}\n")
    for i in range(1, len(df_day)):
        if df_day.loc[i, 'Time'] > ENTRY_DEADLINE:
            break

        current_time = df_day.loc[i, 'Time']
        high = df_day.loc[i, 'High']
        low = df_day.loc[i, 'Low']

        # After 07:45, check for retracement FIRST
        if (
                current_time >= RETRACEMENT_START and
                found_extreme and
                not found_retrace and
                i > extreme_index
        ):
            retrace_price = df_day.loc[i, 'Low'] if mode == 'HH' else df_day.loc[i, 'High']
            retrace = abs(retrace_price - extreme_price)
            retrace_ratio = retrace / max_spread if max_spread else 0

            total_bars = i - extreme_index + 1
            if retrace_ratio >= RETRACE_RATIO_MINIMUM and total_bars >= RETRACE_BAR_COUNT:
                found_retrace = True
                retracement_locked = True
                retrace_index = i

        # If retracement found, check for validation
        if found_retrace and not found_validation:
            validation_idx = i
            if validation_idx < len(df_day):
                validation_row = df_day.loc[validation_idx]
                open_price = validation_row['Open']
                close_price = validation_row['Close']

                if retrace_ratio >= 1.0:
                    # If retracement is 100% or more, the validation candle must be in the opposite direction
                    # AND close ≥ 2 ticks beyond the zero line
                    if mode == 'HH' and close_price > open_price and close_price >= zeroL + VALIDATION_BUFFER:
                        found_validation = True
                        entry_index = validation_idx + 1
                    elif mode == 'LL' and close_price < open_price and close_price <= zeroL - VALIDATION_BUFFER:
                        found_validation = True
                        entry_index = validation_idx + 1
                else:
                    if mode == 'HH' and close_price > open_price:
                        found_validation = True
                        entry_index = validation_idx + 1
                    elif mode == 'LL' and close_price < open_price:
                        found_validation = True
                        entry_index = validation_idx + 1

            if found_validation:
                break

        # Only update HH/LL if no retracement is found yet
        if not retracement_locked:
            is_HH = high >= zeroL + THRESHOLD_VALUE
            is_LL = low <= zeroL - THRESHOLD_VALUE

            if is_HH:
                move = high - zeroL
                if move > max_spread:
                    mode = 'HH'
                    extreme_price = high
                    extreme_index = i
                    max_spread = move
                    found_extreme = True
            elif is_LL:
                move = zeroL - low
                if move > max_spread:
                    mode = 'LL'
                    extreme_price = low
                    extreme_index = i
                    max_spread = move
                    found_extreme = True

    if found_extreme:
        log(f"[Day {day_index + 1} - {current_date}] Found {mode} at {df_day.loc[extreme_index, 'Time']} (price: {extreme_price}, spread: {max_spread})\n")
    if found_retrace:
        log(
            f"[Day {day_index + 1} - {current_date}] Retrace found at {df_day.loc[retrace_index, 'Time']} (percent: {retrace_ratio * 100}%)\n")
    if not found_validation:
        log(f"[Day {day_index + 1} - {current_date}] No valid trade setup found.\n")
    else:
        log(f"[Day {day_index + 1} - {current_date}] Entered {'long' if mode == 'HH' else 'short'} at {df_day.loc[entry_index, 'Time']}\n")

    set_excel_property("EX", extreme_price)
    set_excel_property("RT %", f"{retrace_ratio * 100:.2f}%" if retrace_ratio is not None else "")
    set_excel_property("Spread", max_spread)

    return {
        "extreme_found": mode if found_extreme else None,
        "retrace_found": found_retrace,
        "validation_found": found_validation,
        "entry_index": entry_index,
        "direction": 'long' if mode == 'HH' else 'short' if mode == 'LL' else None,
        "extreme_price": extreme_price
    }

def evaluate_trade(df_day, entry_index, direction, extreme_price, day_index):
    global log_output
    zeroL = df_day.iloc[0]['Close']
    current_date = df_day.loc[0, 'Date']

    if entry_index is None or entry_index >= len(df_day):
        return None

    entry_price = df_day.loc[entry_index, 'Open']
    entry_time = df_day.loc[entry_index, 'Time']
    spread = abs(extreme_price - zeroL)

    tp_price = entry_price + (spread * TP_MULTIPLIER) if direction == 'long' else entry_price - (spread * TP_MULTIPLIER)

    # Take the spread multiplier from the entry or the point limit from the entry - whichever one is a smaller stop loss
    sl_spread = entry_price - (spread * SL_MULTIPLIER) if direction == 'long' else entry_price + (spread * SL_MULTIPLIER)
    sl_point = entry_price - SL_POINT_LIMIT if direction == 'long' else entry_price + SL_POINT_LIMIT
    sl_price = max(sl_spread, sl_point) if direction == 'long' else min(sl_spread, sl_point)

    log(f"[Day {day_index + 1} - {current_date}] Take Profit: {tp_price}, Stop Loss: {sl_price}\n")

    result = None
    active_hh = df_day.loc[entry_index, 'High']
    active_ll = df_day.loc[entry_index, 'Low']
    extended_hh = active_hh
    extended_ll = active_ll
    exited = False
    exit_price = None
    exit_time = None
    trigger = "EOD"

    for j in range(entry_index + 1, len(df_day)):
        row = df_day.loc[j]
        high, low, time_j, close = row['High'], row['Low'], row['Time'], row['Close']

        if not exited:
            active_hh = max(active_hh, high)
            active_ll = min(active_ll, low)

            if direction == 'long':
                if high >= tp_price:
                    result = "win"
                    trigger = "TP"
                    exit_price = tp_price
                    exit_time = time_j
                    exited = True
                elif low <= sl_price:
                    result = "loss"
                    trigger = "SL"
                    exit_price = sl_price
                    exit_time = time_j
                    exited = True
            else:
                if low <= tp_price:
                    result = "win"
                    trigger = "TP"
                    exit_price = tp_price
                    exit_time = time_j
                    exited = True
                elif high >= sl_price:
                    result = "loss"
                    trigger = "SL"
                    exit_price = sl_price
                    exit_time = time_j
                    exited = True
            if exited:
                extended_hh = active_hh
                extended_ll = active_ll

        if exited:
            # Still track extended movement *after* exit, until return to zero line
            if direction == 'long':
                extended_hh = max(extended_hh, high)
                if low <= zeroL:
                    break
            else:
                extended_ll = min(extended_ll, low)
                if high >= zeroL:
                    break

        if time_j >= MARKET_CLOSE:
            if not exited:
                exit_price = close
                exit_time = time_j
                result = "win" if (direction == 'long' and close >= tp_price) or \
                                 (direction == 'short' and close <= tp_price) else "loss"
                trigger = "EOD"
            break

    if not exited and exit_price is None:
        # Fallback (didn’t hit SL/TP/EOD in loop)
        final_row = df_day.iloc[-1]
        exit_price = final_row['Close']
        exit_time = final_row['Time']
        result = "win" if (direction == 'long' and exit_price >= tp_price) or \
                         (direction == 'short' and exit_price <= tp_price) else "loss"
        trigger = "EOD"

    p_or_l = abs(exit_price - entry_price)
    revenue = p_or_l if result == 'win' else -p_or_l

    log(f"[Day {day_index + 1} - {current_date}] {result.upper()}: Entry at {entry_price} ({entry_time}), "
        f"{trigger} hit at {exit_time}, Exit at {exit_price}, Revenue: {revenue}\n")

    if direction == 'long':
        log(f"[Day {day_index + 1} - {current_date}] Highest while active: {active_hh}, "
            f"Highest before return to 0L: {extended_hh}\n")
    else:
        log(f"[Day {day_index + 1} - {current_date}] Lowest while active: {active_ll}, "
            f"Lowest before return to 0L: {extended_ll}\n")

    set_excel_property("Entry Price", entry_price)
    set_excel_property("Long/Short", 'Long' if direction == 'long' else 'Short')
    set_excel_property("W/L", "W" if result == 'win' else "L")
    set_excel_property("Balance", revenue)
    set_excel_property("EX while active", active_hh if direction == 'long' else active_ll)
    set_excel_property("En+Sp", tp_price)
    set_excel_property("EX before 0L", extended_hh if direction == 'long' else extended_ll)

    return result, p_or_l

# --- Log Functions ---
def generate_log_filename() -> str:
    # Get the filename without folders
    base_name = "Analysis_From"

    # Remove the extension
    name_without_ext = os.path.splitext(base_name)[0]

    # Get current date and time (to the minute)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Create new filename
    new_filename = f"{name_without_ext}_{timestamp}.txt"

    return new_filename

def log(text):
    global file_output
    print(text)
    file_output += text

def log_popup(text):
    global log_output
    log(text)
    log_output += text

def save_log():
    global file_output
    if not file_output:
        return

    output_filename = generate_log_filename()
    with open(output_filename, "w") as file:
        file.write(file_output)

def set_excel_property(key, value):
    global excel_obj
    excel_obj[key] = value

def reset_excel_obj(date):
    global excel_obj
    excel_obj = {"Date": date,
                 "Long/Short": '',
                 "Entry Price": '',
                 "Spread": '',
                 "0L": '',
                 "EX": '',
                 "RT %": '',
                 "W/L": '',
                 "Balance": '',
                 "EX while active": '',
                 "En+Sp": '',
                 "EX before 0L": ''}

def log_excel_entry():
    global excel_obj
    global excel_logs
    excel_logs.append(excel_obj)

def save_excel_log():
    global excel_logs
    if not excel_logs:
        return

    df = pd.DataFrame(excel_logs)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"Excel_From_{timestamp}.xlsx"
    df.to_excel(filename, index=False)

# --- Main ---
def main():
    global log_output
    global file_output

    daily_dfs = load_and_split_files(file_paths)

    total_days = 0
    extreme_count = 0
    retrace_count = 0
    validation_count = 0
    trade_win = 0
    trade_loss = 0
    total_profit = 0
    total_loss = 0

    for day_index, df_day in enumerate(daily_dfs):
        date = df_day.loc[0, "Date"]
        if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            continue

        reset_excel_obj(date)
        total_days += 1
        result = analyze_v_shape(df_day, day_index)
        entry_idx = result['entry_index']
        direction = result['direction']

        if result['extreme_found']:
            extreme_count += 1
        if result['retrace_found']:
            retrace_count += 1
        if result['validation_found']:
            validation_count += 1

        if result['validation_found']:
            trade_outcome, p_or_l = evaluate_trade(df_day, entry_idx, direction, result["extreme_price"], day_index)
            if trade_outcome == "win":
                trade_win += 1
                total_profit += p_or_l
            elif trade_outcome == "loss":
                trade_loss += 1
                total_loss += p_or_l

        log_excel_entry()

    log_popup("\n--- Summary ---\n")
    log_popup(f"Total Days: {total_days}\n")
    log_popup(f"Extreme Found: {extreme_count} ({extreme_count / total_days * 100:.1f}%)\n")
    log_popup(f"Retrace Found: {retrace_count} ({retrace_count / total_days * 100:.1f}%)\n")
    log_popup(f"Validation Found: {validation_count} ({validation_count / total_days * 100:.1f}%)\n")
    if validation_count > 0:
        log_popup(f"Trades Won: {trade_win} ({trade_win / validation_count * 100:.1f}%)\n")
        log_popup(f"Trades Lost: {trade_loss} ({trade_loss / validation_count * 100:.1f}%)\n")
        log_popup(f"Total Profit: {total_profit}\n")
        log_popup(f"Total Loss: {total_loss}\n")
        log_popup(f"Total Revenue: {total_profit - total_loss}\n")
    else:
        log_popup("No valid trades found.\n")

    if INCLUDE_LOGS:
        save_log()
        save_excel_log()

    messagebox.showinfo("V-Shape Trade Analysis", log_output)

# --- Run ---
if __name__ == "__main__":
    main()
