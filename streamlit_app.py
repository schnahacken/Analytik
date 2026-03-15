import streamlit as st
import FID  # Importiert deine Logik aus FID.py
import pandas as pd

st.set_page_config(page_title="Mueller Analytik Web", layout="centered")

# Korrektur: Wir nutzen einfache Hochkommas ''' für den gesamten Block
st.code(r'''
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
''')

st.title("FID/TOC Analyse-Tool")

# Sidebar für die Stoffauswahl
with st.sidebar:
    st.header("Stoffdaten")
    stoff_liste = list(FID.STOFF_DB.keys()) + ["Eigene Summenformel"]
    auswahl = st.selectbox("Stoff auswählen", stoff_liste)
    
    if auswahl == "Eigene Summenformel":
        formula = st.text_input("Formel eingeben", value="C6H6")
        name = "Benutzerdefiniert"
    else:
        name = auswahl
        formula = FID.STOFF_DB[auswahl]

# Parameter Eingabe
col1, col2 = st.columns(2)
with col1:
    ta_limit = st.number_input("TA-Luft Grenzwert (mgC/m³)", value=50.0)
    temp = st.number_input("Temperatur (°C)", value=25.0)
with col2:
    druck = st.number_input("Druck (hPa)", value=1013.25)
    mode = st.radio("Modus", ["ppmv", "mg/m³"])

messwert = st.number_input(f"Messwert ({mode})", value=1.0, format="%.4f")

# Berechnung auslösen
if st.button("BERECHNEN", type="primary"):
    try:
        # Nutzung deiner Datenklasse aus FID.py
        inp = FID.Inputs(
            name=name, 
            formula=formula, 
            TA_mgC_m3=ta_limit,
            T_C=temp, 
            P_hPa=druck, 
            meas_mode=("ppmv" if mode == "ppmv" else "mgm3"),
            meas_value=messwert, 
            Qg_Nm3_h=1.0, 
            QL_L_h=1.0, 
            eta=1.0
        )
        
        res = FID.compute(inp) # Rechenlogik aus FID.py
        
        st.subheader("Ergebnis")
        st.metric("Kohlenstoff-Konzentration", f"{res.mgC_m3:.4f} mgC/m³")
        
        if res.TA_exceeded:
            st.error("⚠️ GRENZWERT ÜBERSCHRITTEN!")
        else:
            st.success("✅ Grenzwert eingehalten.")
            
    except Exception as e:
        st.error(f"Fehler bei der Berechnung: {e}")
