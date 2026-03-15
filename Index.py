import FID  # Importiert dein FID-Skript
import os
import sys

# Farben für den Index
BLUE  = "\033[34m"
CYAN  = "\033[36m"
GREEN = "\033[32m"
BOLD  = "\033[1m"
END   = "\033[0m"

def clear_screen():
    # Löscht den Terminalinhalt für eine saubere Optik
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    while True:
        clear_screen()
        # Wir können die Splash-Funktion direkt aus der FID.py nutzen!
        FID.show_splash()
        
        print(f"{BOLD}--- HAUPTMENÜ: MUELLER ANALYTIK ---{END}")
        print(f"  {BLUE}1){END} FID/TOC Analyse-Tool starten")
        print(f"  {BLUE}2){END} Info / Hilfe")
        print(f"  {BLUE}3){END} Programm beenden")
        
        wahl = input(f"\n{BOLD}Wähle eine Option:{END} ").strip()
        
        if wahl == "1":
            clear_screen()
            # Ruft die main() Funktion in deiner FID.py auf
            FID.main()
            input(f"\n{GREEN}Programm beendet. Drücke Enter für das Hauptmenü...{END}")
        
        elif wahl == "2":
            print(f"\n{CYAN}Dieses Tool dient der Auswertung von FID-Messungen.")
            print(f"Erstellt für Mueller Analytik (2026).{END}")
            input("\nDrücke Enter zum Zurückkehren...")
            
        elif wahl == "3":
            print(f"{GREEN}Auf Wiedersehen!{END}")
            sys.exit()
        
        else:
            print(f"\033[31mUngültige Wahl, bitte versuche es erneut.{END}")
            import time
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
