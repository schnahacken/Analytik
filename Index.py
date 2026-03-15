import FID
import os
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    while True:
        clear_screen()
        FID.show_splash()
        
        print(f"\033[1m--- HAUPTMENÜ: MUELLER ANALYTIK ---\033[0m")
        print(f"  \033[34m1)\033[0m FID/TOC Analyse-Tool starten")
        print(f"  \033[34m2)\033[0m Info / Hilfe")
        print(f"  \033[34m3)\033[0m Programm beenden")
        
        wahl = input("\nWähle eine Option: ").strip()
        
        if wahl == "1":
            clear_screen()
            FID.main()
            input("\nDrücke Enter für das Hauptmenü...")
        elif wahl == "2":
            print("\nTool zur FID-Auswertung für Mueller Analytik (2026).")
            input("Drücke Enter...")
        elif wahl == "3":
            sys.exit()

if __name__ == "__main__":
    main_menu()
