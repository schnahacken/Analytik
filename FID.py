#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FID/TOC CLI-Tool (komplette Version)
------------------------------------
Funktionen:
- TA-Luft Grenzwert (Default 50 mgC/m³; editierbar)
- mg/m³ <-> ppmv (ideales Gas, T/p frei wählbar)
- mgC/m³, mgC/L (Stripper-Bilanz mit Qg, QL, η)
- CSV-/Excel-Export (Excel via openpyxl, keine Pandas nötig)
- Stoffdatenbank ODER freie Summenformel (inkl. Klammern & Hydrate)
- Nummerierte, farbige Menüs; farbige Ergebnisse (Zahlen rot, Einheiten grün)
- Farbbalken für TA-Luft-Auslastung
"""

import re
import time
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional

# ----------------- ANSI-Farben -----------------
RED   = "\033[31m"
GREEN = "\033[32m"
YEL   = "\033[33m"
BLUE  = "\033[34m"
CYAN  = "\033[36m"
WHITE = "\033[37m"
BOLD  = "\033[1m"
END   = "\033[0m"

# ----------------- Startanzeige (Splash) -----------------

def show_splash():
    # Wir nutzen hier ''' statt """ am Anfang und Ende, 
    # damit die """ innerhalb deines Logos keine Fehler verursachen.
    logo = f'''
{CYAN}{BOLD}
M"""""`'"""`YM                         dP dP                       
M  mm.  mm.  M                         88 88                       
M  MMM  MMM  M dP    dP .d8888b.       88 88    .d8888b. 88d888b.  
M  MMM  MMM  M 88    88 88ooood8       88 88    88ooood8 88'  `88  
M  MMM  MMM  M 88.  .88 88.  ...       88 88    88.  ... 88        
M  MMM  MMM  M `88888P' `88888P'       dP dP    `88888P' dP        
MMMMMMMMMMMMMM                                                     
                                                                   
MMP"""""""MM                       dP             dP   oo dP       
M' .mmmm  MM                       88             88      88       
M         `M    88d888b. .d8888b. 88 dP    dP d8888P dP 88  .dP   
M  MMMMM  MM    88'  `88 88'  `88 88 88    88   88   88 88888"    
M  MMMMM  MM    88    88 88.  .88 88 88.  .88   88   88 88  `8b.  
M  MMMMM  MM    dP    dP `88888P8 dP `8888P88   dP   dP dP   `YP  
MMMMMMMMMMMM                          .88                          
                                  d8888P                           
{END}{YEL}
           >>> FID/TOC CLI-Analysis System <<<
               Standard: TA-Luft 2026
{END}
'''
    print(logo)
    import time
    time.sleep(2.0)

# ----------------- Stammdaten -----------------
ATOMGEWICHTE: Dict[str, float] = {
    "H": 1.00794, "C": 12.011, "N": 14.0067, "O": 15.999, "S": 32.065,
    "Cl": 35.453, "F": 18.998403163, "Br": 79.904,
    "Si": 28.085, "P": 30.974, "Al": 26.982, "K": 39.098,
    "Na": 22.990, "Ca": 40.078, "Mg": 24.305
}

STOFF_DB: Dict[str, str] = {
    "Butadien": "C4H6",
    "Toluol": "C7H8",
    "Propan": "C3H8",
    "Benzol": "C6H6",
    "Styrol": "C8H8",
    "Ethylen": "C2H4",
    "Propylen": "C3H6",
    "Methan": "CH4",
}

R = 8.314462618  # J/(mol*K), ideale Gaskonstante

# ----------------- Menüsystem -----------------

def nummeriertes_menue(titel: str, optionen: list) -> int:
    print(f"\n{CYAN}{BOLD}{titel}:{END}")
    for i, opt in enumerate(optionen, 1):
        print(f"  {BLUE}{i}{END}) {WHITE}{opt}{END}")
    while True:
        eingabe = input(f"{YEL}Bitte Nummer eingeben:{END} ").strip()
        if eingabe.isdigit():
            idx = int(eingabe)
            if 1 <= idx <= len(optionen):
                return idx
        print(f"{RED}Ungültige Auswahl – bitte erneut eine Nummer eingeben.{END}")

# ----------------- Chemische Hilfsfunktionen -----------------

def parse_formula(formula: str) -> Dict[str, int]:
    parts = re.split(r"[·\.]", formula.replace(" ", ""))
    total: Dict[str, int] = {}
    for part in parts:
        comp = _parse_formula_core(part)
        for el, n in comp.items():
            total[el] = total.get(el, 0) + n
    return total

def _parse_formula_core(s: str, i: int = 0) -> Dict[str, int]:
    stack = [{}]
    i = 0
    L = len(s)
    while i < L:
        ch = s[i]
        if ch == '(':
            stack.append({})
            i += 1
        elif ch == ')':
            i += 1
            m, i = _read_number(s, i)
            m = m if m is not None else 1
            group = stack.pop()
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * m
        else:
            if not ch.isalpha() or not ch.isupper():
                raise ValueError(f"Unerwartetes Zeichen '{ch}' an Pos {i} in '{s}'")
            sym = ch
            i += 1
            if i < L and s[i].islower():
                sym += s[i]
                i += 1
            m, i = _read_number(s, i)
            count = m if m is not None else 1
            stack[-1][sym] = stack[-1].get(sym, 0) + count
    if len(stack) != 1:
        raise ValueError(f"Unausgeglichene Klammern in '{s}'")
    return stack[0]

def _read_number(s: str, i: int) -> Tuple[Optional[int], int]:
    j = i
    while j < len(s) and s[j].isdigit():
        j += 1
    if j == i:
        return None, i
    return int(s[i:j]), j

def molmasse(zus: Dict[str, int]) -> float:
    mm = 0.0
    for el, n in zus.items():
        if el not in ATOMGEWICHTE:
            raise ValueError(f"Unbekanntes Element: {el}")
        mm += ATOMGEWICHTE[el] * n
    return mm

def c_mass_fraction(zus: Dict[str, int], mm: float) -> float:
    nC = zus.get("C", 0)
    return (nC * ATOMGEWICHTE["C"]) / mm if mm > 0 else 0.0

# ----------------- Physikalische Umrechnungen -----------------

def ppmv_to_mgm3(ppmv: float, M_g_mol: float, T_C: float, P_hPa: float) -> float:
    T_K = T_C + 273.15
    P_Pa = P_hPa * 100.0
    return ppmv * 1e-6 * (P_Pa / (R * T_K)) * M_g_mol * 1e3

def mgm3_to_ppmv(mgm3: float, M_g_mol: float, T_C: float, P_hPa: float) -> float:
    T_K = T_C + 273.15
    P_Pa = P_hPa * 100.0
    return mgm3 * 1e-3 * (R * T_K / P_Pa) / M_g_mol * 1e6

def mgC_per_L_from_gas(mgC_per_m3: float, Qg_Nm3_h: float, QL_L_h: float, eta: float) -> float:
    if eta <= 0 or QL_L_h <= 0:
        return float("nan")
    return mgC_per_m3 * (Qg_Nm3_h / (eta * QL_L_h))

# ----------------- Interaktive Eingabe/Workflow -----------------

def ask_float(prompt: str, default: Optional[float] = None) -> float:
    while True:
        s = input(f"{prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not s and default is not None:
            return float(default)
        try:
            return float(s.replace(",", "."))
        except ValueError:
            print(f"{RED}Bitte Zahl eingeben (Dezimaltrenner . oder ,).{END}")

def select_substance() -> Tuple[str, str]:
    namen = list(STOFF_DB.keys())
    optionen = [f"{n} ({STOFF_DB[n]})" for n in namen] + ["Eigene Summenformel eingeben"]
    auswahl = nummeriertes_menue("Stoff auswählen", optionen)
    if auswahl <= len(namen):
        stoff = namen[auswahl - 1]
        return stoff, STOFF_DB[stoff]
    formel = input(f"{YEL}Summenformel eingeben (z.B. C6H4(CH3)2):{END} ").strip()
    return "Benutzerdefiniert", formel

# ----------------- Datenklassen & Kern -----------------

@dataclass
class Inputs:
    name: str
    formula: str
    TA_mgC_m3: float
    T_C: float
    P_hPa: float
    meas_mode: str
    meas_value: float
    Qg_Nm3_h: float
    QL_L_h: float
    eta: float

@dataclass
class Results:
    composition: Dict[str, int]
    M_g_mol: float
    wC: float
    mg_m3: float
    ppmv: float
    mgC_m3: float
    mgC_L: float
    TA_mg_m3_stoff: float
    TA_ppmv_stoff: float
    TA_exceeded: bool

def compute(inputs: Inputs) -> Results:
    zus = parse_formula(inputs.formula)
    M = molmasse(zus)
    wC = c_mass_fraction(zus, M)
    if inputs.meas_mode.lower() == "ppmv":
        mg_m3 = ppmv_to_mgm3(inputs.meas_value, M, inputs.T_C, inputs.P_hPa)
        ppmv = inputs.meas_value
    else:
        mg_m3 = inputs.meas_value
        ppmv = mgm3_to_ppmv(inputs.meas_value, M, inputs.T_C, inputs.P_hPa)
    mgC_m3 = mg_m3 * wC
    mgC_L  = mgC_per_L_from_gas(mgC_m3, inputs.Qg_Nm3_h, inputs.QL_L_h, inputs.eta)
    TA_mg_m3_stoff = inputs.TA_mgC_m3 / wC if wC > 0 else float("inf")
    TA_ppmv_stoff  = mgm3_to_ppmv(TA_mg_m3_stoff, M, inputs.T_C, inputs.P_hPa)
    TA_exceeded    = mg_m3 > TA_mg_m3_stoff
    return Results(zus, M, wC, mg_m3, ppmv, mgC_m3, mgC_L, TA_mg_m3_stoff, TA_ppmv_stoff, TA_exceeded)

# ----------------- Export & Ausgabe -----------------

def export_results(inputs: Inputs, results: Results, fmt: str, filename: str) -> None:
    rec = {**asdict(inputs), **asdict(results)}
    if fmt.lower() == "csv":
        import csv, json
        with open(filename, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            for k, v in rec.items():
                w.writerow([k, json.dumps(v) if isinstance(v, dict) else v])
    elif fmt.lower() == "xlsx":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["key", "value"])
        for k, v in rec.items():
            ws.append([k, str(v)])
        wb.save(filename)

def ta_balken(value: float, limit: float) -> str:
    if limit <= 0: return f"{RED}Limit ungültig{END}"
    ratio = value / limit
    pct = ratio * 100
    total_len = 20
    filled = int(min(max(ratio, 0.0), 1.0) * total_len)
    bar = "█" * filled + "-" * (total_len - filled)
    color = GREEN if pct < 50 else (YEL if pct < 100 else RED)
    return f"TA-Luft-Auslastung: {color}|{bar}| {pct:5.1f}%{END}"

def pretty_print(inputs: Inputs, r: Results) -> None:
    zr = lambda x: f"{RED}{x}{END}"
    ue = lambda x: f"{GREEN}{x}{END}"
    print("\n— Ergebnis —")
    print(f"Stoff: {inputs.name} ({inputs.formula})")
    print(f"Molmasse:          {zr(f'{r.M_g_mol:.5f}')} {ue('g/mol')}")
    print(f"C‑Massenanteil wC: {zr(f'{r.wC:.6f}')} ({zr(f'{r.wC*100:.2f} %')})")
    print(f"→ mg/m³ (Stoff):   {zr(f'{r.mg_m3:.6g}')} {ue('mg/m³')}")
    print(f"→ mgC/m³:          {zr(f'{r.mgC_m3:.6g}')} {ue('mgC/m³')}")
    print(f"→ mgC/L (Flüssig): {zr(f'{r.mgC_L:.6g}')} {ue('mgC/L')}")
    print(ta_balken(r.mg_m3, r.TA_mg_m3_stoff))
    print(f"Überschreitung?:   {BOLD}{(RED if r.TA_exceeded else GREEN)}{'JA' if r.TA_exceeded else 'NEIN'}{END}")

# ----------------- Hauptablauf -----------------

def main():
    show_splash()
    print(f"{BOLD}=== FID/TOC CLI‑Tool gestartet ==={END}")
    
    name, formula = select_substance()
    TA_mgC_m3 = ask_float("TA‑Luft Grenzwert als mgC/m³ (Default 50)", 50.0)

    print("\nBetriebsbedingungen:")
    T_C  = ask_float("Temperatur T in °C", 25.0)
    P_hPa = ask_float("Druck p in hPa", 1013.25)

    mode_idx = nummeriertes_menue("Messmodus wählen", ["ppmv", "mg/m³"])
    mode = "ppmv" if mode_idx == 1 else "mgm3"
    value = ask_float(f"Wert ({mode})")

    print("\nStripper-Parameter:")
    Qg  = ask_float("N2-Durchfluss Q_g in Nm³/h", 1.0)
    QL  = ask_float("Kondensatdurchfluss Q_L in L/h", 1.0)
    eta = ask_float("Stripper‑Effizienz η (0..1)", 1.0)

    inp = Inputs(name, formula, TA_mgC_m3, T_C, P_hPa, mode, value, Qg, QL, eta)
    
    try:
        res = compute(inp)
        pretty_print(inp, res)
        
        exp_idx = nummeriertes_menue("Exportformat wählen", ["CSV", "Excel", "Kein Export"])
        if exp_idx in (1, 2):
            fmt = "csv" if exp_idx == 1 else "xlsx"
            fn = input("Dateiname: ").strip() or "ergebnis"
            export_results(inp, res, fmt, f"{fn}.{fmt}")
            print(f"→ Datei gespeichert: {fn}.{fmt}")
    except Exception as ex:
        print(f"\n{RED}FEHLER:{END} {ex}")

if __name__ == "__main__":
    main()
