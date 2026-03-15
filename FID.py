#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    # Verwendung von ''' verhindert Fehler mit den Anführungszeichen im Logo
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
    time.sleep(2.0)

# ----------------- Stammdaten & Logik -----------------
ATOMGEWICHTE: Dict[str, float] = {
    "H": 1.00794, "C": 12.011, "N": 14.0067, "O": 15.999, "S": 32.065,
    "Cl": 35.453, "F": 18.998403163, "Br": 79.904,
    "Si": 28.085, "P": 30.974, "Al": 26.982, "K": 39.098,
    "Na": 22.990, "Ca": 40.078, "Mg": 24.305
}

STOFF_DB: Dict[str, str] = {
    "Butadien": "C4H6", "Toluol": "C7H8", "Propan": "C3H8",
    "Benzol": "C6H6", "Styrol": "C8H8", "Ethylen": "C2H4",
    "Propylen": "C3H6", "Methan": "CH4",
}

R = 8.314462618

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

def parse_formula(formula: str) -> Dict[str, int]:
    parts = re.split(r"[·\.]", formula.replace(" ", ""))
    total: Dict[str, int] = {}
    for part in parts:
        comp = _parse_formula_core(part)
        for el, n in comp.items():
            total[el] = total.get(el, 0) + n
    return total

def _parse_formula_core(s: str) -> Dict[str, int]:
    stack = [{}]; i = 0; L = len(s)
    while i < L:
        ch = s[i]
        if ch == '(':
            stack.append({}); i += 1
        elif ch == ')':
            i += 1
            j = i
            while i < L and s[i].isdigit(): i += 1
            m = int(s[j:i]) if j < i else 1
            group = stack.pop()
            for el, n in group.items():
                stack[-1][el] = stack[-1].get(el, 0) + n * m
        else:
            sym = ch; i += 1
            if i < L and s[i].islower(): sym += s[i]; i += 1
            j = i
            while i < L and s[i].isdigit(): i += 1
            count = int(s[j:i]) if j < i else 1
            stack[-1][sym] = stack[-1].get(sym, 0) + count
    return stack[0]

def compute(inputs: Inputs) -> Results:
    zus = parse_formula(inputs.formula)
    mm = sum(ATOMGEWICHTE[el] * n for el, n in zus.items())
    wC = (zus.get("C", 0) * ATOMGEWICHTE["C"]) / mm if mm > 0 else 0.0
    
    T_K, P_Pa = inputs.T_C + 273.15, inputs.P_hPa * 100.0
    if inputs.meas_mode.lower() == "ppmv":
        mg_m3 = inputs.meas_value * 1e-6 * (P_Pa / (R * T_K)) * mm * 1e3
        ppmv = inputs.meas_value
    else:
        mg_m3 = inputs.meas_value
        ppmv = (mg_m3 * 1e-3 * R * T_K / P_Pa) / mm * 1e6
        
    mgC_m3 = mg_m3 * wC
    mgC_L = mgC_m3 * (inputs.Qg_Nm3_h / (inputs.eta * inputs.QL_L_h)) if inputs.eta > 0 and inputs.QL_L_h > 0 else 0.0
    ta_mg_stoff = inputs.TA_mgC_m3 / wC if wC > 0 else float('inf')
    
    return Results(zus, mm, wC, mg_m3, ppmv, mgC_m3, mgC_L, ta_mg_stoff, 0.0, mg_m3 > ta_mg_stoff)

def main():
    show_splash()
    print(f"{BOLD}=== FID/TOC CLI-Tool gestartet ==={END}")
    # Hier folgen deine restlichen Input-Logiken aus dem Original...
