import pyautogui
import keyboard
import time
import pygetwindow as gw
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from PIL import Image, ImageTk, ImageDraw
import json
import os
import threading
import pyperclip
import ctypes
import webbrowser
import sys

taille_fenetre = "845x900+100+100"

# Configuration pour éviter les problèmes de layout clavier AZERTY
pyautogui.KEYBOARD_KEYS = {
    'a': 'q', 'q': 'a', 'w': 'z', 'z': 'w',
    'A': 'Q', 'Q': 'A', 'W': 'Z', 'Z': 'W',
    'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right'
}

class MouseBlocker:
    def __init__(self):
        self.blocked = False
        self.original_pos = None
        self.block_thread = None
        
    def block_mouse(self):
        """Bloque complètement les mouvements de souris"""
        if not self.blocked:
            self.original_pos = pyautogui.position()
            self.blocked = True
            # Démarrer le thread de blocage
            self.block_thread = threading.Thread(target=self._mouse_block_loop, daemon=True)
            self.block_thread.start()
            
    def _mouse_block_loop(self):
        """Boucle qui force la souris à rester en place"""
        while self.blocked:
            if self.original_pos:
                current_pos = pyautogui.position()
                if current_pos != self.original_pos:
                    pyautogui.moveTo(self.original_pos[0], self.original_pos[1], duration=0)
            time.sleep(0.001)  # Vérification très fréquente
            
    def unblock_mouse(self):
        """Débloque les mouvements de souris"""
        if self.blocked:
            self.blocked = False
            if self.block_thread:
                self.block_thread.join(timeout=0.1)

class MacroCalibration:
    def __init__(self, app_instance=None):
        self.config_file = "calibration_config.json"
        self.coordinates = {}
        self.app_instance = app_instance
        self.load_config()

    def load_config(self):
        """Charge la configuration sauvegardée"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.coordinates = json.load(f)
            except:
                self.coordinates = {}
        else:
            self.coordinates = {}

    def save_config(self):
        """Sauvegarde la configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.coordinates, f, indent=2)

class MacroApp:
    def __init__(self):
        self.calibration = MacroCalibration(self)
        self.mouse_blocker = MouseBlocker()
        self.calibrating = False
        self.calibration_index = 0
        self.macro_running = False
        self.loop_counter_label = None
        self.warning_delay = 2.0  # Délai par défaut
        self.delay_enabled = True  # Délai activé par défaut
        self.load_settings()
        self.setup_gui()
    
    def show_topmost_messagebox(self, msg_type, title, message):
        """Affiche une messagebox toujours au premier plan"""
        # Créer une fenêtre temporaire invisible pour servir de parent
        temp_window = tk.Toplevel(self.root)
        temp_window.withdraw()  # Rendre invisible
        temp_window.attributes('-topmost', True)
        temp_window.lift()
        temp_window.focus_force()
        
        # S'assurer que la fenêtre principale reste au premier plan
        self.root.attributes('-topmost', True)
        
        try:
            # Afficher la messagebox avec la fenêtre temporaire comme parent
            if msg_type == "info":
                result = messagebox.showinfo(title, message, parent=temp_window)
            elif msg_type == "warning":
                result = messagebox.showwarning(title, message, parent=temp_window)
            elif msg_type == "error":
                result = messagebox.showerror(title, message, parent=temp_window)
            elif msg_type == "yesno":
                result = messagebox.askyesno(title, message, parent=temp_window)
            else:
                result = messagebox.showinfo(title, message, parent=temp_window)
        finally:
            # Détruire la fenêtre temporaire et restaurer le focus
            temp_window.destroy()
            self.root.lift()
            self.root.focus_force()
            
        return result

    def check_stop_key(self):
        """Vérifie si Ctrl est pressé pour arrêter complètement le script"""
        try:
            if keyboard.is_pressed('ctrl'):
                self.mouse_blocker.unblock_mouse()  # TODO : Modifier la fonction pour surveiller le CTRL (ne fonctionne pas dans l'état)
                sys.exit(0)
        except:
            pass

    def open_link(self):
        webbrowser.open_new("https://litedragondev.youtrack.cloud/newIssue")

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("MissionFlash")
        self.root.geometry(taille_fenetre)

        try:
            self.root.iconbitmap("../images/mission-flash.ico")
        except:
            pass

        # Garder la fenêtre toujours en premier plan
        self.root.attributes('-topmost', True)

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        macro_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Instructions", menu=macro_menu)
        macro_menu.add_command(label="Instructions", command=self.show_instructions)

        info_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Infos", menu=info_menu)
        info_menu.add_command(label="Infos", command=self.show_infos)

        # Logo frame
        logo_frame = tk.Frame(self.root, bg="#f0f0f0")
        logo_frame.pack(fill='x', padx=5, pady=2)
        try:
            logo_image = Image.open("../images/mission.png")
            logo_image = logo_image.resize((508, 66), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            tk.Label(logo_frame, image=self.logo_photo, bg="#f0f0f0").pack()
        except Exception as e:
            print(f"Erreur logo: {e}")
            tk.Label(logo_frame, text="Mission Flash", bg="#f0f0f0", fg="#333", font=("Arial Bold", 14)).pack()

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.setup_nouveau_tab(notebook)
        self.setup_macros_tab(notebook)
        self.setup_settings_tab(notebook)

        # Instructions label at bottom
        self.instructions_label = tk.Label(self.root, text="Pour accéder aux Instructions : Haut de l'application -> Instructions -> Instructions",
                                         bg="#e6f3ff", fg="#0066cc", font=("Arial", 11), wraplength=580, justify='left')
        self.instructions_label.pack(fill='x', side='bottom', padx=5, pady=2)

        label = tk.Label(self.root, text="Signaler un bug", fg="red", cursor="hand2", font=("Arial", 13))
        label.bind("<Button-1>", lambda e: self.open_link())
        label.pack()

        # Version label at bottom
        version_frame = tk.Frame(self.root, bg="#f0f0f0")
        version_frame.pack(fill='x', side='bottom', padx=5, pady=2)
        tk.Label(version_frame, text="v10.4.0 𝘗𝘳𝘦𝘷𝘦𝘳𝘴𝘪𝘰𝘯", bg="#f0f0f0", fg="#666", font=("Arial Bold", 8)).pack(side='right')

        # S'assurer que la souris est débloquée à la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def fix_window_position(self):
        """Fixe la position de la fenêtre"""
        self.root.update_idletasks()
        
    def close_warning_dialog(self):
        """Ferme la fenêtre d'avertissement si elle existe"""
        if hasattr(self, 'warning_dialog') and self.warning_dialog.winfo_exists():
            self.warning_dialog.destroy()
    
    def update_loop_counter(self, remaining_loops):
        """Met à jour le compteur de boucles restantes dans la fenêtre d'avertissement"""
        if hasattr(self, 'loop_counter_label') and self.loop_counter_label and hasattr(self, 'warning_dialog') and self.warning_dialog.winfo_exists():
            if remaining_loops > 0:
                self.loop_counter_label.config(text=f"Boucles restantes : {remaining_loops}")
            else:
                self.loop_counter_label.config(text="")
    
    def load_settings(self):
        """Charge les paramètres depuis le fichier de configuration"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", 'r') as f:
                    settings = json.load(f)
                    self.warning_delay = settings.get("warning_delay", 2.0)
                    self.delay_enabled = settings.get("delay_enabled", True)
        except:
            self.warning_delay = 2.0
            self.delay_enabled = True
    
    def show_loop_confirmation(self):
        """Affiche une boîte de dialogue de confirmation pour continuer la boucle"""
        result = [False]
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirmation de boucle")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.configure(bg="#f0f0f0")
        dialog.transient(self.root)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        
        dialog.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 200,
            self.root.winfo_rooty() + 200
        ))
        
        tk.Label(dialog, text="Voulez-vous relancer la boucle ?", 
                bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=30)
        
        def on_yes():
            result[0] = True
            dialog.destroy()
        
        def on_no():
            result[0] = False
            dialog.destroy()
        
        button_frame = tk.Frame(dialog, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Oui", command=on_yes,
                 bg="green", fg="white", font=("Arial", 10, "bold"), width=10).pack(side=tk.LEFT, padx=20)
        tk.Button(button_frame, text="Non", command=on_no,
                 bg="red", fg="white", font=("Arial", 10, "bold"), width=10).pack(side=tk.LEFT, padx=20)
        
        dialog.bind('<Return>', lambda e: on_yes())
        dialog.bind('<Escape>', lambda e: on_no())
        
        dialog.wait_window()
        return result[0]

    def save_settings(self):
        """Sauvegarde les paramètres dans le fichier de configuration"""
        settings = {"warning_delay": self.warning_delay, "delay_enabled": self.delay_enabled}
        with open("settings.json", 'w') as f:
            json.dump(settings, f, indent=2)
    
    def on_closing(self):
        """Gestion de la fermeture de l'application"""
        self.mouse_blocker.unblock_mouse()
        self.close_warning_dialog()
        self.root.quit()
        self.root.destroy()
        
    def show_instructions(self):
        """Affiche les instructions"""
        self.show_topmost_messagebox("info", "Instructions", "Instructions d'utilisation de l'application")

    def show_infos(self):
        """Affiche une fenêtre d'informations personnalisable"""
        info_window = tk.Toplevel(self.root)
        info_window.title("Informations")
        info_window.geometry(taille_fenetre)
        info_window.attributes('-topmost', True)

        # Logo litedragondev en rond
        try:
            logo_img = Image.open("../images/litedragondev.png")
            logo_img = logo_img.resize((160, 160), Image.Resampling.LANCZOS)

            # Créer un masque circulaire
            mask = Image.new('L', (160, 160), 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 160, 160), fill=255)

            # Appliquer le masque
            logo_img.putalpha(mask)

            self.logo_dev_photo = ImageTk.PhotoImage(logo_img)
            tk.Label(info_window, image=self.logo_dev_photo).pack(pady=10)
        except:
            pass

        # -------- ASCII ART --------
        ascii_art = r"""
        
██╗     ██╗████████╗███████╗██████╗ ██████╗  █████╗  ██████╗  ██████╗ ███╗   ██╗██████╗ ███████╗██╗   ██╗
██║     ██║╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝ ██╔═══██╗████╗  ██║██╔══██╗██╔════╝██║   ██║
██║     ██║   ██║   █████╗  ██║  ██║██████╔╝███████║██║  ███╗██║   ██║██╔██╗ ██║██║  ██║█████╗  ██║   ██║
██║     ██║   ██║   ██╔══╝  ██║  ██║██╔══██╗██╔══██║██║   ██║██║   ██║██║╚██╗██║██║  ██║██╔══╝  ╚██╗ ██╔╝
███████╗██║   ██║   ███████╗██████╔╝██║  ██║██║  ██║╚██████╔╝╚██████╔╝██║ ╚████║██████╔╝███████╗ ╚████╔╝ 
╚══════╝╚═╝   ╚═╝   ╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝  ╚═══╝  
                                                                                                         

        """

        tk.Label(info_window, text=ascii_art, font=("Courier New", 5), justify=tk.LEFT).pack(pady=5)

        tk.Label(info_window, text="Mission Flash 10.0.0 𝘗𝘳𝘦𝘷𝘦𝘳𝘴𝘪𝘰𝘯", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(info_window, text="Application d'automatisation pour Mission").pack(pady=5)

        info_text = """Mission Flash est un outil d'automatisation conçu pour aider à la saisie sur la GMAO Mission.
    Réservé pour une utilisation professionnelle chez Fauché Maintenance Ouest Occitanie. 
    Apache 2.0 - litedragondev - Tous droits réservés.
    """
        tk.Label(info_window, text=info_text, font=("Arial", 10, "italic"),
                 fg="#000", justify=tk.CENTER, wraplength=350).pack(pady=5, expand=True)

    def toggle_calibration(self):
        """Bascule l'affichage de la calibration"""
        if self.calibration_visible:
            self.calibration_frame.pack_forget()
            self.calibration_visible = False
        else:
            self.calibration_frame.pack(fill='both', expand=True)
            self.calibration_visible = True
            
    def start_calibration(self):
        """Démarre la calibration"""
        self.calibrating = True
        self.calibration_status.config(text="Calibration en cours...")
        
    def reset_calibration(self):
        """Remet à zéro la calibration"""
        self.calibration.coordinates = {}
        self.calibration.save_config()
        self.update_coord_list()
        
    def delete_selected_coord(self):
        """Supprime la coordonnée sélectionnée"""
        selection = self.coord_listbox.curselection()
        if selection:
            # Logique de suppression
            pass
            
    def quick_test(self):
        """Test rapide"""
        self.show_topmost_messagebox("info", "Test", "Test effectué")
        
    def update_coord_list(self):
        """Met à jour la liste des coordonnées"""
        self.coord_listbox.delete(0, tk.END)
        for key, value in self.calibration.coordinates.items():
            self.coord_listbox.insert(tk.END, f"{key}: {value}")
            
    def setup_nouveau_tab(self, notebook):
        """Configure l'onglet Nouveau"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Nouveau")
        tk.Label(frame, text="Onglet Nouveau").pack(pady=20)
        
    def setup_macros_tab(self, notebook):
        """Configure l'onglet Macros"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Macros")
        tk.Label(frame, text="Onglet Macros").pack(pady=20)


    def validate_input(self, char):
        return char == '' or char in '0123456789-/'

    def validate_num(self, char):
        return char == '' or char in '0123456789-/azertyuiopqsdfghjklmwxcvbnAZERTYUIOPQSDFGHJKLMWXCVBN'

    def validate_montant(self, char):
        return char == '' or char in '0123456789-/,'

    # def setup_devis_tab(self, notebook):  # Onglet désactivé temporairement
        self.devis_frame = ttk.Frame(notebook)
        notebook.add(self.devis_frame, text="Devis")

        vcmd_num = (self.root.register(self.validate_num), '%S')
        vcmd = (self.root.register(self.validate_input), '%S')
        vcmd_montant = (self.root.register(self.validate_montant), '%S')

        windowName = tk.StringVar(value="Alteva.MissionOne")

        # Calibration button
        self.calibrer_button = tk.Button(self.devis_frame, text="Calibrer", command=self.toggle_calibration,
                 bg="orange", fg="white", font=("Arial", 10, "bold"))
        self.calibrer_button.pack(pady=5)

        # Calibration section (initially hidden)
        self.calibration_frame = tk.Frame(self.devis_frame)
        self.calibration_visible = False

        # instructions = tk.Text(self.calibration_frame, height=9, width=70, wrap=tk.WORD)
        # instructions.pack(padx=10, pady=5)
        # instructions.insert(tk.END, """PRERQUIS: Pack Linguistique Anglais (Paramètres -> Heure Et Langue -> Langue -> Ajouter une Langue -> Anglais (United States) -> Installer)
# CALIBRATION: Ouvrez Mission One dans l'onglet Devis, cliquez 'Démarrer la calibration', positionnez le curseur sur chaque élément et appuyez CTRL.
# UTILISATION : Desactivez Maj. Lock de votre clavier, cliquez sur "Lancer la Macro".""")

        tk.Button(self.calibration_frame, text="Démarrer la calibration",
                 command=self.start_calibration, bg="red", fg="white").pack(pady=5)

        self.calibration_status = tk.Label(self.calibration_frame, text="", fg="red")
        self.calibration_status.pack(pady=2)

        self.coord_listbox = tk.Listbox(self.calibration_frame, height=8, width=70)
        self.coord_listbox.pack(padx=10, pady=5)

        button_frame = tk.Frame(self.calibration_frame)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Reset", command=self.reset_calibration).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Supprimer", command=self.delete_selected_coord).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Test", command=self.quick_test).pack(side=tk.LEFT, padx=2)

        self.update_coord_list()

        # Main form (in a separate frame for easy hide/show)
        self.main_form_frame = tk.Frame(self.devis_frame)
        self.main_form_frame.pack(fill='both', expand=True)

        ttk.Separator(self.main_form_frame, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(self.main_form_frame, text="Nom de la fenêtre :").pack(pady=2)
        self.entry_fenetre = tk.Entry(self.main_form_frame, textvariable=windowName, width=50)
        self.entry_fenetre.pack(padx=10, pady=5)

        tk.Label(self.main_form_frame, text="Numéro de commande :").pack(pady=2)
        self.entry_num_commande = tk.Entry(self.main_form_frame, width=50, validate='key', validatecommand=vcmd_num)
        self.entry_num_commande.pack(padx=10, pady=5)


        self.tab_entree_var = tk.BooleanVar(value=False)
        chk_tab = tk.Checkbutton(self.main_form_frame, text="Le numéro de Commande existe-il déjà ?",
                                variable=self.tab_entree_var)
        chk_tab.pack(pady=5)

        tk.Label(self.main_form_frame, text="Date (Format JJ/MM/AAAA) :").pack(pady=2)
        self.entry_date = tk.Entry(self.main_form_frame, width=50, validate='key', validatecommand=vcmd_montant)
        self.entry_date.pack(padx=10, pady=5)


        tk.Label(self.main_form_frame, text="Remarque (multi-ligne) :").pack(pady=2)
        self.text_remarque = tk.Text(self.main_form_frame, height=5, width=50)
        self.text_remarque.pack(padx=10, pady=5)

        self.cocher_case_var = tk.BooleanVar()
        chk1 = tk.Checkbutton(self.main_form_frame, text="Est ce la dernière commande du Devis ?",
                             variable=self.cocher_case_var)
        chk1.pack(pady=5)

        self.montant_var = tk.BooleanVar()
        chk2 = tk.Checkbutton(self.main_form_frame, text="Remplir le champ Montant de la commande",
                             variable=self.montant_var, command=self.toggle_montant_field)
        chk2.pack(pady=5)

        self.entry_montant = tk.Entry(self.main_form_frame, width=50, validate='key', validatecommand=vcmd_montant)

        self.launch_button = tk.Button(self.main_form_frame, text="Lancer la macro", command=self.lancement_macro,
                 bg="green", fg="white", font=("Arial", 12, "bold"))
        self.launch_button.pack(pady=15)
        


        self.caps_warning_label = tk.Label(self.main_form_frame, text="Verr. Maj. Activé ! Désactivez pour continuer",
                                          fg="red", font=("Arial", 10, "bold"))

        self.status_label = tk.Label(self.main_form_frame, text="", fg="blue")
        self.status_label.pack(pady=5)

        self.check_caps_lock()

    def setup_nouveau_tab(self, notebook):
        self.nouveau_frame = ttk.Frame(notebook)
        notebook.add(self.nouveau_frame, text="Macro Personnalisée")
        
        # Variables pour les macros
        self.macros = {}
        self.macro_steps = []
        self.step_widgets = []
        self.load_macros()
        
        # Titre
        tk.Label(self.nouveau_frame, text="Créateur de Macros", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Frame pour les contrôles principaux
        control_frame = tk.Frame(self.nouveau_frame)
        control_frame.pack(pady=5)
        
        # Nom de la macro et délai global
        name_frame = tk.Frame(control_frame)
        name_frame.pack(pady=5)
        
        tk.Label(name_frame, text="Nom:").pack(side=tk.LEFT)
        self.macro_name_entry = tk.Entry(name_frame, width=20)
        self.macro_name_entry.pack(side=tk.LEFT, padx=5)

        
        tk.Label(name_frame, text="Délai entre étapes (s):").pack(side=tk.LEFT, padx=(20,0))
        self.global_delay_entry = tk.Entry(name_frame, width=5, validate='key', validatecommand=(self.root.register(lambda x: x == '' or x.replace('.','').isdigit()), '%P'))
        self.global_delay_entry.insert(0, "0.5")
        self.global_delay_entry.pack(side=tk.LEFT, padx=5)
        
        # Champ description
        desc_frame = tk.Frame(control_frame)
        desc_frame.pack(pady=5)
        
        tk.Label(desc_frame, text="Description:").pack(side=tk.LEFT)
        self.macro_desc_entry = tk.Entry(desc_frame, width=50)
        self.macro_desc_entry.pack(side=tk.LEFT, padx=5)
        
        # Boutons principaux
        button_frame = tk.Frame(control_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Ajouter une étape", command=self.add_step,
                 bg="blue", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Sauvegarder", command=self.save_macro,
                 bg="green", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Exécuter", command=self.execute_current_macro,
                 bg="darkgreen", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Effacer tout", command=self.clear_steps,
                 bg="orange", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Frame scrollable pour les étapes
        steps_container = tk.Frame(self.nouveau_frame)
        steps_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.steps_canvas = tk.Canvas(steps_container, height=300)
        self.steps_scrollbar = ttk.Scrollbar(steps_container, orient="vertical", command=self.steps_canvas.yview)
        self.steps_frame = tk.Frame(self.steps_canvas)
        
        self.steps_canvas.configure(yscrollcommand=self.steps_scrollbar.set)
        self.steps_canvas.pack(side="left", fill="both", expand=True)
        self.steps_scrollbar.pack(side="right", fill="y")
        
        self.steps_canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")
        self.steps_frame.bind("<Configure>", lambda e: self.steps_canvas.configure(scrollregion=self.steps_canvas.bbox("all")))
        
        # Liaison pour le scroll avec la molette de souris
        def on_mousewheel(event):
            self.steps_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.steps_canvas.bind("<MouseWheel>", on_mousewheel)
        self.steps_frame.bind("<MouseWheel>", on_mousewheel)
        

        
    def load_macros(self):
        try:
            if os.path.exists("macros.json"):
                with open("macros.json", 'r') as f:
                    self.macros = json.load(f)
        except:
            self.macros = {}
            
    def save_macros(self):
        with open("macros.json", 'w') as f:
            json.dump(self.macros, f, indent=2)
            
    def add_step(self):
            
        step_frame = tk.Frame(self.steps_frame, relief=tk.RAISED, bd=1)
        step_frame.pack(fill='x', pady=5, padx=5)
        
        # Header avec numéro, case à cocher et bouton supprimer
        header = tk.Frame(step_frame)
        header.pack(fill='x', padx=5, pady=2)
        
        tk.Label(header, text=f"Étape {len(self.macro_steps)+1}:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # Case à cocher pour activer/désactiver l'étape
        step_data = {"frame": step_frame, "enabled": tk.BooleanVar(value=True)}
        enabled_checkbox = tk.Checkbutton(header, text="Activée", variable=step_data["enabled"], 
                                         font=("Arial", 9))
        enabled_checkbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # Boutons de déplacement et suppression
        button_container = tk.Frame(header)
        button_container.pack(side=tk.RIGHT)
        
        tk.Button(button_container, text="↑", command=lambda: self.move_step_up_individual(step_data), 
                 bg="gray", fg="white", font=("Arial", 8, "bold"), width=2).pack(side=tk.LEFT, padx=1)
        tk.Button(button_container, text="↓", command=lambda: self.move_step_down_individual(step_data), 
                 bg="gray", fg="white", font=("Arial", 8, "bold"), width=2).pack(side=tk.LEFT, padx=1)
        tk.Button(button_container, text="X", command=lambda: self.remove_step(step_frame), 
                 bg="red", fg="white", width=2).pack(side=tk.LEFT, padx=1)
        
        # Zone de texte pour le label de l'étape
        label_frame = tk.Frame(step_frame)
        label_frame.pack(fill='x', pady=2, padx=5)
        
        tk.Label(label_frame, text="Label:").pack(side=tk.LEFT)
        step_data["label_entry"] = tk.Entry(label_frame, width=30)
        step_data["label_entry"].pack(side=tk.LEFT, padx=5)
        
        # Champ délai individuel
        tk.Label(label_frame, text="Délai (s):").pack(side=tk.LEFT, padx=(20,0))
        step_data["step_delay_entry"] = tk.Entry(label_frame, width=5, validate='key', validatecommand=(self.root.register(lambda x: x == '' or x.replace('.','').isdigit()), '%P'))
        step_data["step_delay_entry"].pack(side=tk.LEFT, padx=5)
        
        # Sélecteur de type d'action
        type_frame = tk.Frame(step_frame)
        type_frame.pack(fill='x', pady=5, padx=5)
        
        tk.Label(type_frame, text="Action:").pack(side=tk.LEFT)
        action_var = tk.StringVar(value="Cliquer")
        action_combo = ttk.Combobox(type_frame, textvariable=action_var, values=["Cliquer", "Saisir", "Touches spécifiques", "Attendre", "Confirmer ?", "Saisir valeur", "Utiliser variable", "Début de boucle", "Boucle"], state="readonly", width=15)
        action_combo.pack(side=tk.LEFT, padx=5)
        
        # Frame pour les options spécifiques
        options_frame = tk.Frame(step_frame)
        options_frame.pack(fill='x', pady=5, padx=5)
        
        step_data.update({"action_var": action_var, "options_frame": options_frame, "coords": None, "calibrating": False})
        self.macro_steps.append(step_data)
        
        action_combo.bind("<<ComboboxSelected>>", lambda e: self.update_step_options(step_data))
        self.update_step_options(step_data)
        

        

        
    def update_step_options(self, step_data):
        # Nettoyer les options précédentes
        for widget in step_data["options_frame"].winfo_children():
            widget.destroy()
            
        action = step_data["action_var"].get()
        
        if action == "Cliquer":
            tk.Button(step_data["options_frame"], text="Calibrer coordonnées", command=lambda: self.calibrate_click(step_data), bg="orange", fg="white").pack(side=tk.LEFT, padx=(10,0))
            step_data["coord_label"] = tk.Label(step_data["options_frame"], text="Non calibré", fg="red")
            step_data["coord_label"].pack(side=tk.LEFT, padx=10)
            
            tk.Button(step_data["options_frame"], text="Test", command=lambda: self.test_click(step_data), bg="blue", fg="white").pack(side=tk.LEFT, padx=5)

            tk.Label(step_data["options_frame"], text="Type:").pack(side=tk.LEFT, padx=(20,0))
            step_data["click_type"] = tk.StringVar(value="Gauche")
            click_combo = ttk.Combobox(step_data["options_frame"], textvariable=step_data["click_type"], values=["Gauche", "Droit"], state="readonly", width=8)
            click_combo.pack(side=tk.LEFT, padx=5)

        elif action == "Saisir":
            tk.Label(step_data["options_frame"], text="Texte:").pack(side=tk.LEFT, padx=(10,0))
            step_data["text_entry"] = tk.Entry(step_data["options_frame"], width=30)
            step_data["text_entry"].pack(side=tk.LEFT, padx=5)


        elif action == "Touches spécifiques":
            keys_frame = tk.Frame(step_data["options_frame"])
            keys_frame.pack(side=tk.LEFT, padx=(10,0))

            step_data["keys"] = {}
            for key in ["Ctrl", "Alt", "Shift", "Tab", "Entrée", "Échap", "↑", "↓", "←", "→"]:
                var = tk.BooleanVar()
                tk.Checkbutton(keys_frame, text=key, variable=var).pack(side=tk.LEFT)
                step_data["keys"][key] = var

            tk.Label(step_data["options_frame"], text="Autre:").pack(side=tk.LEFT, padx=(10,0))
            step_data["custom_key"] = tk.Entry(step_data["options_frame"], width=10)
            step_data["custom_key"].pack(side=tk.LEFT, padx=5)

        elif action == "Attendre":
            tk.Label(step_data["options_frame"], text="Délai (s):").pack(side=tk.LEFT, padx=(10,0))
            step_data["delay_entry"] = tk.Entry(step_data["options_frame"], width=10, validate='key', validatecommand=(self.root.register(lambda x: x == '' or x.replace('.','').isdigit()), '%P'))
            step_data["delay_entry"].pack(side=tk.LEFT, padx=5)

        elif action == "Confirmer ?":
            tk.Label(step_data["options_frame"], text="Message:").pack(side=tk.LEFT, padx=(10,0))
            step_data["confirm_message"] = tk.Text(step_data["options_frame"], width=30, height=3, wrap=tk.WORD)
            step_data["confirm_message"].insert("1.0", "Confirmer ?")
            step_data["confirm_message"].pack(side=tk.LEFT, padx=5)

        elif action == "Saisir valeur":
            tk.Label(step_data["options_frame"], text="Message:").pack(side=tk.LEFT, padx=(10,0))
            step_data["input_message"] = tk.Entry(step_data["options_frame"], width=30)
            step_data["input_message"].insert(0, "Saisissez la valeur souhaitée :")
            step_data["input_message"].pack(side=tk.LEFT, padx=5)
            tk.Label(step_data["options_frame"], text="Variable*:").pack(side=tk.LEFT, padx=(10,0))
            step_data["variable_name"] = tk.Entry(step_data["options_frame"], width=15)
            step_data["variable_name"].pack(side=tk.LEFT, padx=5)
            step_data["variable_name"].bind('<KeyRelease>', lambda e: self.validate_step_variable_fields(step_data))
            
            # Option pour choisir le type de saisie
            tk.Label(step_data["options_frame"], text="Type:").pack(side=tk.LEFT, padx=(10,0))
            step_data["input_type"] = tk.StringVar(value="Court")
            input_type_combo = ttk.Combobox(step_data["options_frame"], textvariable=step_data["input_type"], 
                                          values=["Court", "Long"], state="readonly", width=8)
            input_type_combo.pack(side=tk.LEFT, padx=5)

        elif action == "Utiliser variable":
            tk.Label(step_data["options_frame"], text="Variable:").pack(side=tk.LEFT, padx=(10,0))
            step_data["use_variable"] = ttk.Combobox(step_data["options_frame"], width=15, state="readonly")
            step_data["use_variable"].pack(side=tk.LEFT, padx=5)
            self.update_variable_list(step_data)

        elif action == "Début de boucle":
            tk.Label(step_data["options_frame"], text="Point de départ de la boucle", fg="blue", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10,0))
            
        elif action == "Boucle":
            tk.Label(step_data["options_frame"], text="Répétitions:").pack(side=tk.LEFT, padx=(10,0))
            step_data["loop_count"] = tk.Entry(step_data["options_frame"], width=10, validate='key', validatecommand=(self.root.register(lambda x: x == '' or (x.isdigit() and int(x) > 0)), '%P'))
            step_data["loop_count"].insert(0, "0")
            step_data["loop_count"].bind('<FocusIn>', lambda e: e.widget.after(1, lambda: e.widget.select_range(0, tk.END)))
            step_data["loop_count"].bind('<Button-1>', lambda e: e.widget.after(1, lambda: e.widget.select_range(0, tk.END)))
            step_data["loop_count"].pack(side=tk.LEFT, padx=5)

            # Mode de boucle
            tk.Label(step_data["options_frame"], text="Mode:").pack(side=tk.LEFT, padx=(20,0))
            step_data["loop_mode"] = tk.StringVar(value="Fixe")
            loop_mode_combo = ttk.Combobox(step_data["options_frame"], textvariable=step_data["loop_mode"], values=["Fixe", "Avec confirmation"], state="readonly", width=15)
            loop_mode_combo.pack(side=tk.LEFT, padx=5)





    def move_step_up_individual(self, step_data):
        """Déplace une étape spécifique vers le haut"""
        try:
            current_index = self.macro_steps.index(step_data)
            if current_index > 0:
                self.macro_steps[current_index], self.macro_steps[current_index - 1] = \
                    self.macro_steps[current_index - 1], self.macro_steps[current_index]
                self.refresh_steps_display()
        except ValueError:
            pass
    
    def move_step_down_individual(self, step_data):
        """Déplace une étape spécifique vers le bas"""
        try:
            current_index = self.macro_steps.index(step_data)
            if current_index < len(self.macro_steps) - 1:
                self.macro_steps[current_index], self.macro_steps[current_index + 1] = \
                    self.macro_steps[current_index + 1], self.macro_steps[current_index]
                self.refresh_steps_display()
        except ValueError:
            pass
    
    def refresh_steps_display(self):
        """Rafraîchit l'affichage des étapes dans l'ordre correct"""
        # Supprimer tous les frames de l'affichage
        for step in self.macro_steps:
            step["frame"].pack_forget()
        
        # Les remettre dans le bon ordre
        for step in self.macro_steps:
            step["frame"].pack(fill='x', pady=5, padx=5)
        
        # Renuméroter
        self.renumber_steps()

    def validate_step_variable_fields(self, step_data):
        """Valide que le champ Variable est rempli pour l'action Saisir valeur"""
        if "variable_name" in step_data:
            variable_name = step_data["variable_name"].get().strip()
            if variable_name:
                step_data["variable_name"].config(bg="white")
            else:
                step_data["variable_name"].config(bg="#ffcccc")

    def update_variable_list(self, step_data):
        """Met à jour la liste des variables disponibles"""
        variables = []
        for step in self.macro_steps:
            if (step["action_var"].get() == "Saisir valeur" and
                "variable_name" in step and
                step["variable_name"].get().strip()):
                variables.append(step["variable_name"].get().strip())

        if "use_variable" in step_data:
            step_data["use_variable"]["values"] = variables
            if variables and not step_data["use_variable"].get():
                step_data["use_variable"].set(variables[0])

    def calibrate_click(self, step_data):
        if step_data["calibrating"]:
            return

        step_data["calibrating"] = True
        step_data["coord_label"].config(text="Positionnez la souris et appuyez CTRL", fg="orange")

        def calibrate_thread():
            try:
                keyboard.wait('ctrl')
                x, y = pyautogui.position()
                step_data["coords"] = (x, y)
                step_data["coord_label"].config(text=f"Calibré: ({x}, {y})", fg="green")
            except:
                step_data["coord_label"].config(text="Erreur de calibration", fg="red")
            finally:
                step_data["calibrating"] = False

        threading.Thread(target=calibrate_thread, daemon=True).start()
    
    def test_click(self, step_data):
        """Teste les coordonnées calibrées en effectuant un clic"""
        if not step_data.get("coords"):
            self.show_topmost_messagebox("warning", "Test", "Aucune coordonnée calibrée")
            return
        
        x, y = step_data["coords"]
        click_type = step_data["click_type"].get()
        
        try:
            if click_type == "Droit":
                pyautogui.rightClick(x, y)
            else:
                pyautogui.click(x, y)
            self.show_topmost_messagebox("info", "Test", f"Clic {click_type.lower()} effectué à ({x}, {y})")
        except Exception as e:
            self.show_topmost_messagebox("error", "Erreur", f"Erreur lors du test: {str(e)}")

    def remove_step(self, step_frame):
        # Trouver et supprimer l'étape
        removed_step = None
        for i, step in enumerate(self.macro_steps):
            if step["frame"] == step_frame:
                removed_step = step
                del self.macro_steps[i]
                break
        step_frame.destroy()
        self.renumber_steps()


            


    def renumber_steps(self):
        for i, step in enumerate(self.macro_steps):
            header = step["frame"].winfo_children()[0]
            header.winfo_children()[0].config(text=f"Étape {i+1}:")

    def clear_steps(self):
        for step in self.macro_steps:
            step["frame"].destroy()
        self.macro_steps = []

        


    def save_macro(self):
        name = self.macro_name_entry.get().strip()
        if not name:
            self.show_topmost_messagebox("warning", "Attention", "Nom requis")
            return
        if not self.macro_steps:
            self.show_topmost_messagebox("warning", "Attention", "Aucune étape")
            return
        
        # Vérifier que tous les champs Variable obligatoires sont remplis
        for step in self.macro_steps:
            if (step["action_var"].get() == "Saisir valeur" and 
                "variable_name" in step and 
                not step["variable_name"].get().strip()):
                self.show_topmost_messagebox("warning", "Attention", "Le champ Variable est obligatoire pour l'action 'Saisir valeur'")
                return

        macro_data = {"steps": [], "global_delay": float(self.global_delay_entry.get() or 0.5), "description": self.macro_desc_entry.get().strip()}

        for step in self.macro_steps:
            action = step["action_var"].get()
            step_info = {"action": action}

            # Ajouter le label s'il existe
            if "label_entry" in step:
                step_info["label"] = step["label_entry"].get()

            # Ajouter l'état activé/désactivé
            step_info["enabled"] = step["enabled"].get()

            # Ajouter le délai individuel (utilise le délai global si vide)
            step_delay = step["step_delay_entry"].get().strip()
            if step_delay:
                step_info["step_delay"] = float(step_delay)

            if action == "Cliquer" and step["coords"]:
                step_info["coords"] = step["coords"]
                step_info["click_type"] = step["click_type"].get()
            elif action == "Saisir":
                step_info["text"] = step["text_entry"].get()
            elif action == "Touches spécifiques":
                keys = [k for k, v in step["keys"].items() if v.get()]
                custom = step["custom_key"].get().strip()
                if custom: keys.append(custom)
                step_info["keys"] = keys
            elif action == "Attendre":
                step_info["delay"] = float(step["delay_entry"].get() or 1)
            elif action == "Confirmer ?":
                step_info["confirm_message"] = step["confirm_message"].get("1.0", tk.END).strip()
            elif action == "Saisir valeur":
                step_info["input_message"] = step["input_message"].get()
                step_info["variable_name"] = step["variable_name"].get()
                step_info["input_type"] = step["input_type"].get()
            elif action == "Utiliser variable":
                step_info["use_variable"] = step["use_variable"].get()
            elif action == "Début de boucle":
                # Pas de paramètres spécifiques pour le début de boucle
                pass
            elif action == "Boucle":
                step_info["loop_count"] = int(step["loop_count"].get() or 1)
                step_info["loop_mode"] = step["loop_mode"].get()

            macro_data["steps"].append(step_info)

        self.macros[name] = macro_data
        self.save_macros()
        self.update_saved_macros_list()
        self.update_macros_list()
        self.show_topmost_messagebox("info", "Succès", f"Macro '{name}' sauvegardée")

    def setup_macros_tab(self, notebook):
        self.macros_tab_frame = ttk.Frame(notebook)
        notebook.add(self.macros_tab_frame, text="Macros Sauvegardées")

        # Titre
        tk.Label(self.macros_tab_frame, text="Macros Sauvegardées", font=("Arial", 16, "bold")).pack(pady=10)

        # Liste des macros
        list_frame = tk.Frame(self.macros_tab_frame)
        list_frame.pack(fill='both', padx=20, pady=10)

        tk.Label(list_frame, text="Sélectionnez une macro:", font=("Arial", 12)).pack(pady=(0,10))

        self.macros_listbox = tk.Listbox(list_frame, height=15, font=("Arial", 11))
        self.macros_listbox.pack(fill='both', pady=(0,20))

        # Boutons d'action
        buttons_frame = tk.Frame(self.macros_tab_frame)
        buttons_frame.pack(pady=20)

        tk.Button(buttons_frame, text="Exécuter", command=self.execute_macro_from_tab,
                 bg="darkgreen", fg="white", font=("Arial", 12, "bold"), width=12, height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="Modifier", command=self.edit_macro_from_tab,
                 bg="orange", fg="white", font=("Arial", 12, "bold"), width=12, height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="Supprimer", command=self.delete_macro_from_tab,
                 bg="red", fg="white", font=("Arial", 12, "bold"), width=12, height=2).pack(side=tk.LEFT, padx=10)

        self.update_macros_list()
    
    def setup_settings_tab(self, notebook):
        """Configure l'onglet Paramètres"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Paramètres")
        
        # Titre
        tk.Label(settings_frame, text="Paramètres", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Section délai d'attente
        delay_frame = tk.Frame(settings_frame)
        delay_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(delay_frame, text="Délai d'attente avant démarrage de la macro:", 
                font=("Arial", 12)).pack(anchor='w', pady=(0,10))
        
        # Case à cocher pour activer/désactiver le délai
        self.delay_enabled_var = tk.BooleanVar(value=self.delay_enabled)
        delay_checkbox = tk.Checkbutton(delay_frame, text="Activer le délai d'attente", 
                                       variable=self.delay_enabled_var, font=("Arial", 11),
                                       command=self.toggle_delay_controls)
        delay_checkbox.pack(anchor='w', pady=(0,10))
        
        delay_input_frame = tk.Frame(delay_frame)
        delay_input_frame.pack(anchor='w')
        
        self.delay_entry = tk.Entry(delay_input_frame, width=10, font=("Arial", 11),
                                   validate='key', validatecommand=(self.root.register(
                                   lambda x: x == '' or (x.replace('.','').isdigit() and float(x) >= 0.5)), '%P'))
        self.delay_entry.pack(side=tk.LEFT)
        self.delay_entry.insert(0, str(self.warning_delay))
        
        tk.Label(delay_input_frame, text="secondes", font=("Arial", 11)).pack(side=tk.LEFT, padx=(5,0))
        
        self.toggle_delay_controls()
        
        # Description
        desc_text = ("Ce délai correspond au temps d'attente entre le moment où vous appuyez sur OK "
                    "dans l'écran d'avertissement et le démarrage effectif de la première étape de la macro.")
        tk.Label(delay_frame, text=desc_text, font=("Arial", 10), fg="#666",
                wraplength=400, justify='left').pack(anchor='w', pady=(10,0))
        
        # Bouton de sauvegarde
        save_button = tk.Button(delay_frame, text="Sauvegarder", command=self.save_delay_setting,
                               bg="green", fg="white", font=("Arial", 11, "bold"))
        save_button.pack(anchor='w', pady=20)
        
        # Statut de sauvegarde
        self.save_status_label = tk.Label(delay_frame, text="", font=("Arial", 10))
        self.save_status_label.pack(anchor='w')
    
    def toggle_delay_controls(self):
        """Active ou désactive les contrôles de délai selon la case à cocher"""
        enabled = self.delay_enabled_var.get()
        state = "normal" if enabled else "disabled"
        self.delay_entry.config(state=state)
    
    def save_delay_setting(self):
        """Sauvegarde le paramètre de délai"""
        try:
            self.delay_enabled = self.delay_enabled_var.get()
            
            if self.delay_enabled:
                new_delay = float(self.delay_entry.get())
                if new_delay < 0.5:
                    self.save_status_label.config(text="Le délai minimum est de 0.5 seconde", fg="red")
                    return
                self.warning_delay = new_delay
            
            self.save_settings()
            self.save_status_label.config(text="Paramètres sauvegardés avec succès", fg="green")
            
            # Effacer le message après 3 secondes
            self.root.after(3000, lambda: self.save_status_label.config(text=""))
        except ValueError:
            self.save_status_label.config(text="Veuillez entrer une valeur numérique valide", fg="red")

    def update_macros_list(self):
        self.macros_listbox.delete(0, tk.END)
        for name, data in self.macros.items():
            desc = data.get("description", "")
            display_text = f"{name} - {desc}" if desc else name
            self.macros_listbox.insert(tk.END, display_text)

    def execute_single_step(self, step_info):
        """Exécute une seule étape de macro"""
        action = step_info["action"]

        if action == "Cliquer" and "coords" in step_info:
            x, y = step_info["coords"]
            click_type = step_info.get("click_type", "Gauche")
            if click_type == "Droit":
                pyautogui.rightClick(x, y)
            else:
                pyautogui.click(x, y)
        elif action == "Saisir" and "text" in step_info:
            pyautogui.write(step_info["text"])
        elif action == "Touches spécifiques" and "keys" in step_info:
            keys = step_info["keys"]
            key_map = {"Ctrl": "ctrl", "Alt": "alt", "Shift": "shift", "Tab": "tab", "Entrée": "enter", "Échap": "esc", "↑": "up", "↓": "down", "←": "left", "→": "right"}
            mapped_keys = [key_map.get(key, key.lower()) for key in keys]
            if len(mapped_keys) > 1:
                pyautogui.hotkey(*mapped_keys)
            elif len(mapped_keys) == 1:
                pyautogui.press(mapped_keys[0])
        elif action == "Attendre" and "delay" in step_info:
            self.show_wait_dialog(step_info["delay"])
        elif action == "Saisir valeur":
            # Désactiver VERR MAJ si activé
            caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
            if caps_on:
                ctypes.windll.user32.keybd_event(0x14, 0x45, 0, 0)
                ctypes.windll.user32.keybd_event(0x14, 0x45, 2, 0)
                time.sleep(0.1)
            
            message = step_info.get("input_message", "Saisissez la valeur souhaitée :")
            input_type = step_info.get("input_type", "Court")
            
            if input_type == "Long":
                user_input = self.show_long_text_dialog(message)
            else:
                user_input = self.show_input_dialog(message)
                
            if user_input is None:
                return False
            if "variable_name" in step_info and step_info["variable_name"]:
                setattr(self, f"macro_var_{step_info['variable_name']}", user_input)
        elif action == "Utiliser variable":
            var_name = step_info.get("use_variable")
            if var_name and hasattr(self, f"macro_var_{var_name}"):
                var_value = getattr(self, f"macro_var_{var_name}")
                pyautogui.write(var_value)
        return True

    def execute_single_step_with_confirm(self, step_info):
        """Exécute une seule étape de macro avec gestion des confirmations"""
        action = step_info["action"]

        if action == "Confirmer ?":
            message = step_info.get("confirm_message", "Confirmer ?")
            if not messagebox.askyesno("Confirmation", message):
                return False
        else:
            return self.execute_single_step(step_info)
        return True

    def execute_macro_from_tab(self):
        selection = self.macros_listbox.curselection()
        if not selection:
            self.show_topmost_messagebox("warning", "Attention", "Sélectionnez une macro")
            return

        display_text = self.macros_listbox.get(selection[0])
        # Extraire le nom réel de la macro (avant le " - ")
        name = display_text.split(" - ")[0] if " - " in display_text else display_text

        if name not in self.macros:
            self.show_topmost_messagebox("error", "Erreur", "Macro introuvable")
            return

        macro_data = self.macros[name]

        result = self.show_warning_dialog()
        if not result:
            return

        def execute_thread():
            try:
                if self.delay_enabled:
                    time.sleep(self.warning_delay)
                global_delay = macro_data.get("global_delay", 0.5)

                self.macro_running = True
                
                # Trouver l'index du début de boucle s'il existe
                loop_start_index = 0
                for i, step_info in enumerate(macro_data["steps"]):
                    if step_info["action"] == "Début de boucle":
                        loop_start_index = i
                        break
                
                for step_info in macro_data["steps"]:
                    self.check_stop_key()

                    # Ignorer les étapes désactivées
                    if not step_info.get("enabled", True):
                        continue

                    action = step_info["action"]

                    if action == "Début de boucle":
                        # Ne rien faire, c'est juste un marqueur
                        pass
                    elif action == "Boucle":
                        loop_count = step_info.get("loop_count", 1)
                        loop_mode = step_info.get("loop_mode", "Fixe")
                        
                        if loop_mode == "Avec confirmation":
                            # Mode boucle infinie avec confirmation
                            while True:
                                # Demander à l'utilisateur s'il veut lancer/relancer la boucle
                                if not self.show_loop_confirmation():
                                    break
                                    
                                # Exécuter les étapes de la boucle
                                for prev_step in macro_data["steps"][loop_start_index:-1]:
                                    if prev_step["action"] == "Début de boucle" or not prev_step.get("enabled", True):
                                        continue
                                    self.check_stop_key()
                                    if not self.execute_single_step_with_confirm(prev_step):
                                        return
                                    prev_step_delay = prev_step.get("step_delay", global_delay)
                                    if prev_step["action"] == "Attendre":
                                        pass
                                    elif prev_step_delay > 2:
                                        self.show_wait_dialog(prev_step_delay)
                                    else:
                                        time.sleep(prev_step_delay)
                        else:
                            # Mode boucle fixe
                            for loop_iteration in range(loop_count - 1):
                                remaining_loops = loop_count - 1 - loop_iteration
                                self.update_loop_counter(remaining_loops)
                                for prev_step in macro_data["steps"][loop_start_index:-1]:
                                    if prev_step["action"] == "Début de boucle" or not prev_step.get("enabled", True):
                                        continue
                                    self.check_stop_key()
                                    if not self.execute_single_step_with_confirm(prev_step):
                                        return
                                    prev_step_delay = prev_step.get("step_delay", global_delay)
                                    if prev_step["action"] == "Attendre":
                                        pass
                                    elif prev_step_delay > 2:
                                        self.show_wait_dialog(prev_step_delay)
                                    else:
                                        time.sleep(prev_step_delay)
                            self.update_loop_counter(0)
                    else:
                        if not self.execute_single_step_with_confirm(step_info):
                            break

                    # Utiliser le délai individuel ou le délai global
                    step_delay = step_info.get("step_delay", global_delay)
                    if action == "Attendre":
                        # Pour les blocs Attendre, le délai est déjà géré dans execute_single_step
                        pass
                    elif step_delay > 2:
                        self.show_wait_dialog(step_delay)
                    else:
                        time.sleep(step_delay)

                self.show_topmost_messagebox("info", "Succès", "Macro exécutée")
            except Exception as e:
                if "arrêtée par l'utilisateur" in str(e):
                    self.show_topmost_messagebox("info", "Arrêt", "Macro arrêtée par l'utilisateur")
                else:
                    self.show_topmost_messagebox("error", "Erreur", f"Erreur: {str(e)}")
            finally:
                self.macro_running = False
                self.close_warning_dialog()

        threading.Thread(target=execute_thread, daemon=True).start()

    def edit_macro_from_tab(self):
        selection = self.macros_listbox.curselection()
        if not selection:
            self.show_topmost_messagebox("warning", "Attention", "Sélectionnez une macro")
            return

        display_text = self.macros_listbox.get(selection[0])
        name = display_text.split(" - ")[0] if " - " in display_text else display_text

        if name not in self.macros:
            self.show_topmost_messagebox("error", "Erreur", "Macro introuvable")
            return

        # Basculer vers l'onglet "Macro Personnalisée" (index 0)
        notebook = self.root.winfo_children()[2]
        notebook.select(0)

        # Charger la macro sélectionnée
        self.load_macro_for_editing(name)

    def load_macro_for_editing(self, name):
        """Charge une macro dans l'éditeur pour modification"""
        if name not in self.macros:
            return
            
        macro_data = self.macros[name]
        
        # Effacer l'éditeur actuel
        self.clear_steps()
        
        # Charger les informations de base
        self.macro_name_entry.delete(0, tk.END)
        self.macro_name_entry.insert(0, name)
        self.macro_desc_entry.delete(0, tk.END)
        self.macro_desc_entry.insert(0, macro_data.get("description", ""))
        self.global_delay_entry.config(validate='none')
        self.global_delay_entry.delete(0, tk.END)
        self.global_delay_entry.insert(0, str(macro_data.get("global_delay", 0.5)))
        self.global_delay_entry.config(validate='key')
        
        # Recréer toutes les étapes
        for step_info in macro_data["steps"]:
            self.add_step()
            step_data = self.macro_steps[-1]
            action = step_info["action"]
            
            step_data["action_var"].set(action)
            self.update_step_options(step_data)
            
            if "label" in step_info and "label_entry" in step_data:
                step_data["label_entry"].insert(0, step_info["label"])
            
            if "enabled" in step_info:
                step_data["enabled"].set(step_info["enabled"])
            
            if "step_delay" in step_info:
                step_data["step_delay_entry"].insert(0, str(step_info["step_delay"]))
            
            if action == "Cliquer" and "coords" in step_info:
                step_data["coords"] = step_info["coords"]
                x, y = step_info["coords"]
                step_data["coord_label"].config(text=f"Calibré: ({x}, {y})", fg="green")
                if "click_type" in step_info:
                    step_data["click_type"].set(step_info["click_type"])
            elif action == "Saisir" and "text" in step_info:
                step_data["text_entry"].insert(0, step_info["text"])
            elif action == "Touches spécifiques" and "keys" in step_info:
                for key in step_info["keys"]:
                    if key in step_data["keys"]:
                        step_data["keys"][key].set(True)
                    else:
                        step_data["custom_key"].insert(0, key)
            elif action == "Attendre" and "delay" in step_info:
                step_data["delay_entry"].insert(0, str(step_info["delay"]))
            elif action == "Confirmer ?" and "confirm_message" in step_info:
                step_data["confirm_message"].insert("1.0", step_info["confirm_message"])
            elif action == "Saisir valeur":
                if "input_message" in step_info:
                    step_data["input_message"].insert(0, step_info["input_message"])
                if "variable_name" in step_info:
                    step_data["variable_name"].insert(0, step_info["variable_name"])
                if "input_type" in step_info:
                    step_data["input_type"].set(step_info["input_type"])
            elif action == "Utiliser variable":
                if "use_variable" in step_info:
                    step_data["use_variable"].set(step_info["use_variable"])
            elif action == "Boucle":
                if "loop_count" in step_info:
                    step_data["loop_count"].delete(0, tk.END)
                    step_data["loop_count"].insert(0, str(step_info["loop_count"]))
                if "loop_mode" in step_info:
                    step_data["loop_mode"].set(step_info["loop_mode"])
                if "loop_mode" in step_info:
                    step_data["loop_mode"].set(step_info["loop_mode"])

    def delete_macro_from_tab(self):
        selection = self.macros_listbox.curselection()
        if not selection:
            self.show_topmost_messagebox("warning", "Attention", "Sélectionnez une macro à supprimer")
            return

        display_text = self.macros_listbox.get(selection[0])
        # Extraire le nom réel de la macro (avant le " - ")
        name = display_text.split(" - ")[0] if " - " in display_text else display_text

        if self.show_topmost_messagebox("yesno", "Confirmation", f"Supprimer la macro '{name}' ?"):
            if name in self.macros:
                del self.macros[name]
                self.save_macros()
                self.update_macros_list()
                self.show_topmost_messagebox("info", "Succès", f"Macro '{name}' supprimée")
            else:
                self.show_topmost_messagebox("error", "Erreur", "Macro introuvable")

    def update_saved_macros_list(self):
        # Mise à jour pour les deux listes
        if hasattr(self, 'saved_macros_listbox'):
            self.saved_macros_listbox.delete(0, tk.END)
            for name, data in self.macros.items():
                desc = data.get("description", "")
                display_text = f"{name} - {desc}" if desc else name
                self.saved_macros_listbox.insert(tk.END, display_text)
        if hasattr(self, 'macros_listbox'):
            self.update_macros_list()

    def load_macro(self):
        selection = self.saved_macros_listbox.curselection()
        if not selection:
            return

        name = self.saved_macros_listbox.get(selection[0])
        macro_data = self.macros[name]

        self.clear_steps()
        self.macro_name_entry.delete(0, tk.END)
        self.macro_name_entry.insert(0, name)
        self.macro_desc_entry.delete(0, tk.END)
        self.macro_desc_entry.insert(0, macro_data.get("description", ""))
        # Forcer la réinitialisation du champ délai
        self.global_delay_entry.config(validate='none')
        self.global_delay_entry.delete(0, tk.END)
        self.global_delay_entry.insert(0, str(macro_data.get("global_delay", 0.5)))
        self.global_delay_entry.config(validate='key')

        # Recréer les étapes avec leurs paramètres
        for step_info in macro_data["steps"]:
            self.add_step()
            step_data = self.macro_steps[-1]
            action = step_info["action"]

            # Définir le type d'action
            step_data["action_var"].set(action)
            self.update_step_options(step_data)

            # Restaurer le label s'il existe
            if "label" in step_info and "label_entry" in step_data:
                step_data["label_entry"].insert(0, step_info["label"])

            # Restaurer l'état activé/désactivé
            if "enabled" in step_info:
                step_data["enabled"].set(step_info["enabled"])

            # Restaurer le délai individuel
            if "step_delay" in step_info:
                step_data["step_delay_entry"].insert(0, str(step_info["step_delay"]))

            # Restaurer les paramètres selon le type
            if action == "Cliquer" and "coords" in step_info:
                step_data["coords"] = step_info["coords"]
                x, y = step_info["coords"]
                step_data["coord_label"].config(text=f"Calibré: ({x}, {y})", fg="green")
                if "click_type" in step_info:
                    step_data["click_type"].set(step_info["click_type"])
            elif action == "Saisir" and "text" in step_info:
                step_data["text_entry"].insert(0, step_info["text"])
            elif action == "Touches spécifiques" and "keys" in step_info:
                for key in step_info["keys"]:
                    if key in step_data["keys"]:
                        step_data["keys"][key].set(True)
                    else:
                        step_data["custom_key"].insert(0, key)
            elif action == "Attendre" and "delay" in step_info:
                step_data["delay_entry"].insert(0, str(step_info["delay"]))
            elif action == "Confirmer ?" and "confirm_message" in step_info:
                step_data["confirm_message"].insert("1.0", step_info["confirm_message"])
            elif action == "Saisir valeur":
                if "input_message" in step_info:
                    step_data["input_message"].insert(0, step_info["input_message"])
                if "variable_name" in step_info:
                    step_data["variable_name"].insert(0, step_info["variable_name"])
                if "input_type" in step_info:
                    step_data["input_type"].set(step_info["input_type"])
            elif action == "Utiliser variable":
                if "use_variable" in step_info:
                    step_data["use_variable"].set(step_info["use_variable"])
            
    def delete_macro(self):
        selection = self.saved_macros_listbox.curselection()
        if selection:
            name = self.saved_macros_listbox.get(selection[0])
            if self.show_topmost_messagebox("yesno", "Confirmation", f"Supprimer '{name}' ?"):
                del self.macros[name]
                self.save_macros()
                self.update_saved_macros_list()
                self.update_macros_list()
                
    def execute_current_macro(self):
        if not self.macro_steps:
            self.show_topmost_messagebox("warning", "Attention", "Aucune étape définie")
            return
        
        # Vérifier que tous les champs Variable obligatoires sont remplis
        for step in self.macro_steps:
            if (step["action_var"].get() == "Saisir valeur" and 
                "variable_name" in step and 
                not step["variable_name"].get().strip()):
                self.show_topmost_messagebox("warning", "Attention", "Le champ Variable est obligatoire pour l'action 'Saisir valeur'")
                return
            
        # Créer temporairement les données de la macro
        macro_data = {"steps": [], "global_delay": float(self.global_delay_entry.get() or 0.5), "description": self.macro_desc_entry.get().strip()}
        
        for step in self.macro_steps:
            action = step["action_var"].get()
            step_info = {"action": action}
            
            if "label_entry" in step:
                step_info["label"] = step["label_entry"].get()
            
            # Ajouter l'état activé/désactivé
            step_info["enabled"] = step["enabled"].get()
            
            # Ajouter le délai individuel
            step_delay = step["step_delay_entry"].get().strip()
            if step_delay:
                step_info["step_delay"] = float(step_delay)
            
            if action == "Cliquer" and step["coords"]:
                step_info["coords"] = step["coords"]
                step_info["click_type"] = step["click_type"].get()
            elif action == "Saisir":
                step_info["text"] = step["text_entry"].get()
            elif action == "Touches spécifiques":
                keys = [k for k, v in step["keys"].items() if v.get()]
                custom = step["custom_key"].get().strip()
                if custom: keys.append(custom)
                step_info["keys"] = keys
            elif action == "Attendre":
                step_info["delay"] = float(step["delay_entry"].get() or 1)
            elif action == "Confirmer ?":
                step_info["confirm_message"] = step["confirm_message"].get("1.0", tk.END).strip()
            elif action == "Saisir valeur":
                variable_name = step["variable_name"].get().strip()
                if not variable_name:
                    self.show_topmost_messagebox("warning", "Attention", "Le champ Variable est obligatoire pour l'action 'Saisir valeur'")
                    return
                step_info["input_message"] = step["input_message"].get()
                step_info["variable_name"] = variable_name
                step_info["input_type"] = step["input_type"].get()
            elif action == "Utiliser variable":
                step_info["use_variable"] = step["use_variable"].get()
            elif action == "Début de boucle":
                # Pas de paramètres spécifiques pour le début de boucle
                pass
            elif action == "Boucle":
                step_info["loop_count"] = int(step["loop_count"].get() or 1)
                step_info["loop_mode"] = step["loop_mode"].get()
                
            macro_data["steps"].append(step_info)

        result = self.show_warning_dialog()
        if not result:
            return
            
        def execute_thread():
            try:
                if self.delay_enabled:
                    time.sleep(self.warning_delay)
                global_delay = macro_data.get("global_delay", 0.5)
                
                self.macro_running = True
                
                # Trouver l'index du début de boucle s'il existe
                loop_start_index = 0
                for i, step_info in enumerate(macro_data["steps"]):
                    if step_info["action"] == "Début de boucle":
                        loop_start_index = i
                        break
                
                for step_info in macro_data["steps"]:
                    self.check_stop_key()
                    
                    # Ignorer les étapes désactivées
                    if not step_info.get("enabled", True):
                        continue
                        
                    action = step_info["action"]
                    
                    if action == "Début de boucle":
                        # Ne rien faire, c'est juste un marqueur
                        pass
                    elif action == "Boucle":
                        loop_count = step_info.get("loop_count", 1)
                        loop_mode = step_info.get("loop_mode", "Fixe")
                        
                        if loop_mode == "Avec confirmation":
                            # Mode boucle infinie avec confirmation
                            while True:
                                # Demander à l'utilisateur s'il veut lancer/relancer la boucle
                                if not self.show_loop_confirmation():
                                    break
                                    
                                # Exécuter les étapes de la boucle
                                for prev_step in macro_data["steps"][loop_start_index:-1]:
                                    if prev_step["action"] == "Début de boucle" or not prev_step.get("enabled", True):
                                        continue
                                    self.check_stop_key()
                                    if not self.execute_single_step_with_confirm(prev_step):
                                        return
                                    prev_step_delay = prev_step.get("step_delay", global_delay)
                                    if prev_step["action"] == "Attendre":
                                        pass
                                    elif prev_step_delay > 2:
                                        self.show_wait_dialog(prev_step_delay)
                                    else:
                                        time.sleep(prev_step_delay)
                        else:
                            # Mode boucle fixe
                            for loop_iteration in range(loop_count - 1):
                                remaining_loops = loop_count - 1 - loop_iteration
                                self.update_loop_counter(remaining_loops)
                                for prev_step in macro_data["steps"][loop_start_index:-1]:
                                    if prev_step["action"] == "Début de boucle" or not prev_step.get("enabled", True):
                                        continue
                                    self.check_stop_key()
                                    if not self.execute_single_step_with_confirm(prev_step):
                                        return
                                    prev_step_delay = prev_step.get("step_delay", global_delay)
                                    if prev_step["action"] == "Attendre":
                                        pass
                                    elif prev_step_delay > 2:
                                        self.show_wait_dialog(prev_step_delay)
                                    else:
                                        time.sleep(prev_step_delay)
                            self.update_loop_counter(0)
                    else:
                        if not self.execute_single_step_with_confirm(step_info):
                            break
                        
                    # Utiliser le délai individuel ou le délai global
                    step_delay = step_info.get("step_delay", global_delay)
                    if action == "Attendre":
                        # Pour les blocs Attendre, le délai est déjà géré dans execute_single_step_with_confirm
                        pass
                    elif step_delay > 2:
                        self.show_wait_dialog(step_delay)
                    else:
                        time.sleep(step_delay)
                    
                self.show_topmost_messagebox("info", "Succès", "Macro exécutée")
            except Exception as e:
                if "arrêtée par l'utilisateur" in str(e):
                    self.show_topmost_messagebox("info", "Arrêt", "Macro arrêtée par l'utilisateur")
                else:
                    self.show_topmost_messagebox("error", "Erreur", f"Erreur: {str(e)}")
            finally:
                self.macro_running = False
                self.close_warning_dialog()
                
        threading.Thread(target=execute_thread, daemon=True).start()

    def execute_macro(self):
        selection = self.saved_macros_listbox.curselection()
        if not selection:
            self.show_topmost_messagebox("warning", "Attention", "Sélectionnez une macro")
            return
            
        name = self.saved_macros_listbox.get(selection[0])
        macro_data = self.macros[name]

        result = self.show_warning_dialog()
        if not result:
            return
            
        def execute_thread():
            try:
                if self.delay_enabled:
                    time.sleep(self.warning_delay)
                global_delay = macro_data.get("global_delay", 0.5)
                
                self.macro_running = True
                for step_info in macro_data["steps"]:
                    self.check_stop_key()
                        
                    action = step_info["action"]
                    
                    if action == "Cliquer" and "coords" in step_info:
                        x, y = step_info["coords"]
                        click_type = step_info.get("click_type", "Gauche")
                        if click_type == "Droit":
                            pyautogui.rightClick(x, y)
                        else:
                            pyautogui.click(x, y)
                    elif action == "Saisir" and "text" in step_info:
                        pyautogui.write(step_info["text"])
                    elif action == "Touches spécifiques" and "keys" in step_info:
                        keys = step_info["keys"]
                        key_map = {"Ctrl": "ctrl", "Alt": "alt", "Shift": "shift", "Tab": "tab", "Entrée": "enter", "Échap": "esc", "↑": "up", "↓": "down", "←": "left", "→": "right"}
                        mapped_keys = [key_map.get(key, key.lower()) for key in keys]
                        if len(mapped_keys) > 1:
                            pyautogui.hotkey(*mapped_keys)
                        elif len(mapped_keys) == 1:
                            pyautogui.press(mapped_keys[0])
                    elif action == "Attendre" and "delay" in step_info:
                        self.show_wait_dialog(step_info["delay"])
                    elif action == "Confirmer ?":
                        message = step_info.get("confirm_message", "Confirmer ?")
                        if not self.show_topmost_messagebox("yesno", "Confirmation", message):
                            break
                    elif action == "Saisir valeur":
                        message = step_info.get("input_message", "Saisissez la valeur souhaitée :")
                        user_input = self.show_input_dialog(message)
                        if user_input is None:
                            break
                        if "variable_name" in step_info and step_info["variable_name"]:
                            setattr(self, f"macro_var_{step_info['variable_name']}", user_input)
                    elif action == "Utiliser variable":
                        var_name = step_info.get("use_variable")
                        if var_name and hasattr(self, f"macro_var_{var_name}"):
                            var_value = getattr(self, f"macro_var_{var_name}")
                            pyautogui.write(var_value)
                        
                    # Utiliser le délai individuel ou le délai global
                    step_delay = step_info.get("step_delay", global_delay)
                    if action == "Attendre":
                        # Pour les blocs Attendre, le délai est déjà géré ci-dessus
                        pass
                    elif step_delay > 2:
                        self.show_wait_dialog(step_delay)
                    else:
                        time.sleep(step_delay)
                    
                self.show_topmost_messagebox("info", "Succès", "Macro exécutée")
            except Exception as e:
                if "arrêtée par l'utilisateur" in str(e):
                    self.show_topmost_messagebox("info", "Arrêt", "Macro arrêtée par l'utilisateur")
                else:
                    self.show_topmost_messagebox("error", "Erreur", f"Erreur: {str(e)}")
            finally:
                self.macro_running = False
                self.close_warning_dialog()
                
        threading.Thread(target=execute_thread, daemon=True).start()

    def fix_window_position(self):
        """Fixe la fenêtre à une position précise et empêche son déplacement"""
        # Position fixe (coin supérieur gauche)
        x, y = 100, 100
        self.root.geometry(f"600x800+{x}+{y}")
        
        # Empêcher le redimensionnement et le déplacement
        self.root.resizable(True, True)
        
        # Désactiver les événements de déplacement
        def disable_event():
            return "break"
        
        self.root.bind("<Button-1>", lambda e: self.check_title_bar(e))
        self.root.bind("<B1-Motion>", disable_event)
        
    def check_title_bar(self, event):
        """Vérifie si le clic est sur la barre de titre et l'empêche"""
        if event.y < 30:  # Zone approximative de la barre de titre
            return "break"
        
    def on_closing(self):
        """Nettoie les ressources avant fermeture"""
        self.mouse_blocker.unblock_mouse()
        self.root.destroy()

    def show_instructions(self):
        """Affiche une fenêtre avec les instructions complètes"""
        instructions_window = tk.Toplevel(self.root)
        instructions_window.title("Instructions d'utilisation")
        instructions_window.geometry("500x300")
        instructions_window.resizable(False, False)

        text_widget = tk.Text(instructions_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)

        instructions_text = """PRÉREQUIS:
Pack Linguistique Anglais (Paramètres → Heure Et Langue → Langue → Ajouter une Langue → Anglais (United States) → Installer)

CALIBRATION:
1. Ouvrez Mission One dans l'onglet Devis
2. Cliquez 'Calibrer' puis 'Démarrer la calibration'
3. Positionnez le curseur sur chaque élément demandé
4. Appuyez sur CTRL pour enregistrer la position

UTILISATION:
1. Désactivez Maj. Lock de votre clavier
2. Remplissez les champs du formulaire
3. Cliquez sur "Lancer la Macro"""

        text_widget.insert('1.0', instructions_text)
        text_widget.config(state='disabled')

    def check_caps_lock(self):
        """Vérifie l'état de Verr Maj et affiche un avertissement"""
        caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)

        if caps_on:
            self.caps_warning_label.pack(pady=5, before=self.status_label)
        else:
            self.caps_warning_label.pack_forget()

        self.root.after(500, self.check_caps_lock)

    def toggle_montant_field(self):
        if self.montant_var.get():
            self.entry_montant.pack(padx=10, pady=5, before=self.launch_button)
        else:
            self.entry_montant.pack_forget()

    def toggle_calibration(self):
        if self.calibrating:
            self.calibrating = False
            self.calibration_status.config(text="Calibration annulée", fg="red")
            self.calibrer_button.config(text="Retour", state="normal")
            return

        if self.calibration_visible:
            self.calibration_frame.pack_forget()
            self.main_form_frame.pack(fill='both', expand=True)
            self.calibrer_button.config(text="Calibrer")
            self.calibration_visible = False
        else:
            self.main_form_frame.pack_forget()
            self.calibration_frame.pack(fill='x', padx=10, pady=5, after=self.devis_frame.winfo_children()[0])
            self.calibrer_button.config(text="Retour")
            self.calibration_visible = True

    def start_calibration(self):
        def calibration_thread():
            elements_to_calibrate = [
                ("commandes_recues", "Bouton 'Commandes reçues'"),
                ("nouvelle_commande", "Bouton 'Ajouter nouvelle commande'"),
                ("num_commande", "Champ 'Numéro de commande'"),
                ("date", "Champ 'Date'"),
                ("case_a_cocher", "Case à cocher (optionnelle)"),
                ("montant", "Champ 'Montant' (optionnel)"),
                ("remarque", "Champ 'Remarque'"),
                ("validation", "Bouton 'Validation'")
            ]

            self.calibrating = True
            self.calibrer_button.config(text="Annuler", state="normal")

            for i in range(self.calibration_index, len(elements_to_calibrate)):
                if not self.calibrating:
                    break
                name, description = elements_to_calibrate[i]
                try:
                    self.calibration_status.config(text=f"Calibration en cours... Positionnez sur {description} puis pressez CTRL", fg="red")
                    self.root.update()

                    keyboard.wait('ctrl')
                    x, y = pyautogui.position()
                    self.calibration.coordinates[name] = {"x": x, "y": y, "description": description}
                    self.calibration_index = i + 1
                    self.update_coord_list()
                    self.calibration.save_config()

                except Exception as e:
                    self.calibration_status.config(text=f"Erreur: {str(e)}", fg="red")
                    break

            if self.calibrating:
                self.calibration_status.config(text="Calibration terminée!", fg="green")
                self.calibration_index = 0

            self.calibrating = False
            self.calibrer_button.config(text="Retour", state="normal")

        threading.Thread(target=calibration_thread, daemon=True).start()

    def reset_calibration(self):
        self.calibration.coordinates = {}
        self.calibration.save_config()
        self.update_coord_list()
        self.calibration_index = 0
        self.show_topmost_messagebox("info", "Reset", "Calibration réinitialisée")

    def delete_selected_coord(self):
        selection = self.coord_listbox.curselection()
        if selection:
            index = selection[0]
            keys = list(self.calibration.coordinates.keys())
            if index < len(keys):
                key_to_delete = keys[index]
                del self.calibration.coordinates[key_to_delete]
                self.calibration.save_config()
                self.update_coord_list()

    def quick_test(self):
        if not self.calibration.coordinates:
            self.show_topmost_messagebox("warning", "Test", "Aucune coordonnée calibrée")
            return

        for name, coord in self.calibration.coordinates.items():
            pyautogui.click(coord['x'], coord['y'])
            time.sleep(0.5)

    def update_coord_list(self):
        self.coord_listbox.delete(0, tk.END)
        for name, coord in self.calibration.coordinates.items():
            self.coord_listbox.insert(tk.END, f"{name}: ({coord['x']}, {coord['y']}) - {coord['description']}")

    def toggle_montant_field(self):
        if self.montant_var.get():
            self.montant_label = tk.Label(self.main_form_frame, text="Montant de la commande :")
            self.montant_label.pack(pady=2, before=self.launch_button)
            self.entry_montant.pack(padx=10, pady=5, before=self.launch_button)
        else:
            if hasattr(self, 'montant_label'):
                self.montant_label.destroy()
            self.entry_montant.pack_forget()

    def safe_click(self, x, y):
        """Clique de manière sécurisée avec blocage temporaire"""
        try:
            # Débloquer temporairement pour le clic
            self.mouse_blocker.unblock_mouse()
            pyautogui.click(x, y)
            time.sleep(0.1)
            # Rebloquer immédiatement
            self.mouse_blocker.block_mouse()
            return True
        except Exception:
            self.mouse_blocker.block_mouse()
            return False

    def clear_clipboard(self):
        """Purge le presse-papiers"""
        pyperclip.copy("")

    def copy_from_field_and_paste(self, field_widget, target_coords):
        """Double-clique sur le champ, copie avec Ctrl+C et colle aux coordonnées cibles"""
        try:
            # Obtenir les coordonnées du champ dans l'interface
            field_x = field_widget.winfo_rootx() + field_widget.winfo_width() // 2
            field_y = field_widget.winfo_rooty() + field_widget.winfo_height() // 2
            
            # Débloquer temporairement la souris
            self.mouse_blocker.unblock_mouse()
            
            # Double-cliquer sur le champ pour sélectionner tout
            pyautogui.doubleClick(field_x, field_y)
            time.sleep(0.2)
            
            # Copier avec Ctrl+C
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.2)
            
            # Rebloquer la souris
            self.mouse_blocker.block_mouse()
            
            # Cliquer sur la cible et coller
            if not self.safe_click(target_coords['x'], target_coords['y']):
                return False
            time.sleep(0.3)
            
            # Sélectionner tout le contenu existant avant de coller
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            return True
        except Exception:
            self.mouse_blocker.block_mouse()
            return False
    
    def copy_from_text_field_and_paste(self, field_widget, target_coords):
        """Spécial pour champ Text: clique, Ctrl+A, copie et colle"""
        try:
            # Obtenir les coordonnées du champ dans l'interface
            field_x = field_widget.winfo_rootx() + field_widget.winfo_width() // 2
            field_y = field_widget.winfo_rooty() + field_widget.winfo_height() // 2
            
            # Débloquer temporairement la souris
            self.mouse_blocker.unblock_mouse()
            
            # Cliquer sur le champ
            pyautogui.click(field_x, field_y)
            time.sleep(0.2)
            
            # Sélectionner tout avec Ctrl+A
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            
            # Copier avec Ctrl+C
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.2)
            
            # Rebloquer la souris
            self.mouse_blocker.block_mouse()
            
            # Cliquer sur la cible et coller
            if not self.safe_click(target_coords['x'], target_coords['y']):
                return False
            time.sleep(0.3)
            
            # Sélectionner tout le contenu existant avant de coller
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            return True
        except Exception:
            self.mouse_blocker.block_mouse()
            return False

    def lancement_macro(self):
        try:
            # Désactiver VERR MAJ si activé
            caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
            if caps_on:
                ctypes.windll.user32.keybd_event(0x14, 0x45, 0, 0)
                ctypes.windll.user32.keybd_event(0x14, 0x45, 2, 0)
                time.sleep(0.2)

            window_name = self.entry_fenetre.get()
            num_commande = self.entry_num_commande.get()
            date = self.entry_date.get()
            remarque = self.text_remarque.get("1.0", tk.END).strip()

            if not all([window_name, num_commande, date]):
                self.show_topmost_messagebox("error", "Erreur", "Veuillez remplir tous les champs obligatoires")
                return

            required_coords = ["commandes_recues", "nouvelle_commande", "num_commande", "date", "remarque", "validation"]
            missing_coords = [coord for coord in required_coords if coord not in self.calibration.coordinates]

            if missing_coords:
                self.show_topmost_messagebox("error", "Calibration incomplète", f"Coordonnées manquantes: {', '.join(missing_coords)}")
                return

            # Avertissement avant exécution
            result = self.show_warning_dialog()

            if not result:
                return

            if self.delay_enabled:
                delay_seconds = int(self.warning_delay)
                self.status_label.config(text=f"Démarrage dans {delay_seconds} secondes... NE BOUGEZ PAS LA SOURIS!", fg="red")
                self.root.update()

                for i in range(delay_seconds, 0, -1):
                    self.status_label.config(text=f"Démarrage dans {i} seconde(s)...", fg="red")
                    self.root.update()
                    time.sleep(1)
            else:
                self.status_label.config(text="Démarrage immédiat... NE BOUGEZ PAS LA SOURIS!", fg="red")
                self.root.update()

            self.status_label.config(text="Préparation du blocage de souris...", fg="orange")
            self.root.update()

            def macro_thread():
                try:
                    self.macro_running = True
                    windows = gw.getWindowsWithTitle(window_name)
                    if not windows:
                        raise Exception(f"Fenêtre '{window_name}' non trouvée")

                    window = windows[0]
                    window.activate()
                    time.sleep(1)

                    # Bloquer la souris
                    self.mouse_blocker.block_mouse()
                    self.status_label.config(text="Souris bloquée - Exécution en cours...", fg="orange")
                    self.root.update()

                    # Commandes reçues
                    self.check_stop_key()
                    coord = self.calibration.coordinates["commandes_recues"]
                    if not self.safe_click(coord['x'], coord['y']):
                        raise Exception("Échec du clic sur 'Commandes reçues'")
                    time.sleep(0.5)

                    # Nouvelle commande
                    self.check_stop_key()
                    coord = self.calibration.coordinates["nouvelle_commande"]
                    if not self.safe_click(coord['x'], coord['y']):
                        raise Exception("Échec du clic sur 'Nouvelle commande'")
                    time.sleep(0.5)

                    # Numéro de commande - copie depuis le champ
                    self.check_stop_key()
                    coord = self.calibration.coordinates["num_commande"]
                    if not self.copy_from_field_and_paste(self.entry_num_commande, coord):
                        raise Exception("Échec de la saisie du numéro de commande")
                    time.sleep(0.25)

                    # Date - copie depuis le champ
                    self.check_stop_key()
                    coord = self.calibration.coordinates["date"]
                    
                    # Tab + Entrée si la case est cochée
                    if self.tab_entree_var.get():
                        if not self.safe_click(coord['x'], coord['y']):
                            raise Exception("Échec du clic sur le champ 'Date'")
                        time.sleep(0.3)
                        pyautogui.press('tab')
                        time.sleep(0.2)
                        pyautogui.press('enter')
                        time.sleep(0.25)
                        self.tab_entree_var.set(True)
                    
                    if not self.copy_from_field_and_paste(self.entry_date, coord):
                        raise Exception("Échec de la saisie de la date")

                    # Case à cocher optionnelle
                    self.check_stop_key()
                    if self.cocher_case_var.get() and "case_a_cocher" in self.calibration.coordinates:
                        coord = self.calibration.coordinates["case_a_cocher"]
                        if not self.safe_click(coord['x'], coord['y']):
                            raise Exception("Échec du clic sur la case à cocher")
                        time.sleep(0.25)
                        pyautogui.press('enter')

                    # Montant optionnel - copie depuis le champ
                    self.check_stop_key()
                    if self.montant_var.get() and "montant" in self.calibration.coordinates:
                        coord = self.calibration.coordinates["montant"]
                        if not self.copy_from_field_and_paste(self.entry_montant, coord):
                            raise Exception("Échec de la saisie du montant")

                    # Remarque - copie depuis le champ avec Ctrl+A
                    self.check_stop_key()
                    coord = self.calibration.coordinates["remarque"]
                    if not self.copy_from_text_field_and_paste(self.text_remarque, coord):
                        raise Exception("Échec de la saisie de la remarque")

                    # Validation
                    self.check_stop_key()
                    coord = self.calibration.coordinates["validation"]
                    if not self.safe_click(coord['x'], coord['y']):
                        raise Exception("Échec du clic sur 'Validation'")

                    self.status_label.config(text="Macro exécutée avec succès!", fg="green")

                except Exception as e:
                    if "arrêtée par l'utilisateur" in str(e):
                        self.status_label.config(text="Macro arrêtée par l'utilisateur", fg="orange")
                    else:
                        self.status_label.config(text=f"Erreur: {str(e)}", fg="red")
                finally:
                    # Débloquer la souris dans tous les cas
                    self.macro_running = False
                    self.mouse_blocker.unblock_mouse()
                    self.close_warning_dialog()

            threading.Thread(target=macro_thread, daemon=True).start()

        except Exception as e:
            self.show_topmost_messagebox("error", "Erreur", str(e))

    def show_wait_dialog(self, delay_seconds):
        """Affiche une boîte de dialogue d'attente avec compte à rebours sans bloquer l'exécution"""
        def create_dialog():
            dialog = tk.Toplevel(self.root)
            dialog.title("Macro en cours")
            dialog.geometry("350x150")
            dialog.resizable(False, False)
            dialog.configure(bg="#f0f0f0")
            dialog.transient(self.root)
            dialog.attributes('-topmost', True)
            dialog.lift()
            dialog.focus_force()
            
            # Centrer la fenêtre
            dialog.geometry("+{}+{}".format(
                self.root.winfo_rootx() + 150,
                self.root.winfo_rooty() + 250
            ))
            
            # Message principal
            message_label = tk.Label(dialog, text="Macro en cours d'exécution", 
                                    font=("Arial", 12, "bold"), 
                                    bg="#f0f0f0")
            message_label.pack(pady=15)
            
            # Compte à rebours
            countdown_label = tk.Label(dialog, text=f"Prochaine étape dans {int(delay_seconds)}s", 
                                      font=("Arial", 10), 
                                      fg="#d32f2f", bg="#f0f0f0")
            countdown_label.pack(pady=10)
            
            # Fonction pour mettre à jour le compte à rebours
            remaining = [delay_seconds]
            
            def update_countdown():
                if remaining[0] > 0:
                    countdown_label.config(text=f"Prochaine étape dans {int(remaining[0])}s")
                    remaining[0] -= 1
                    dialog.after(1000, update_countdown)
                else:
                    dialog.destroy()
            
            # Démarrer le compte à rebours
            update_countdown()
        
        # Créer la dialog dans le thread principal et continuer l'exécution
        self.root.after(0, create_dialog)
        time.sleep(delay_seconds)

    def show_input_dialog(self, message):
        """Affiche une boîte de dialogue de saisie simple et sécurisée"""
        result = [None]
        dialog = tk.Toplevel(self.root)
        dialog.title("Saisie")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.configure(bg="#f0f0f0")
        dialog.transient(self.root)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        
        # Centrer la fenêtre
        dialog.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 200,
            self.root.winfo_rooty() + 200
        ))
        
        tk.Label(dialog, text=message, bg="#f0f0f0", font=("Arial", 10)).pack(pady=15)
        
        entry = tk.Entry(dialog, width=30, font=("Arial", 10))
        entry.pack(pady=10)
        entry.focus_set()
        
        def validate_input():
            text = entry.get().strip()
            if text:
                ok_button.config(state="normal", bg="green")
                entry.config(bg="white")
            else:
                ok_button.config(state="disabled", bg="#cccccc")
                entry.config(bg="#ffcccc")

        def ok_clicked():
            result[0] = entry.get().strip() if entry.get().strip() else None
            dialog.destroy()
            # Désactiver VERR MAJ après validation
            caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
            if caps_on:
                ctypes.windll.user32.keybd_event(0x14, 0x45, 0, 0)
                ctypes.windll.user32.keybd_event(0x14, 0x45, 2, 0)
        
        def cancel_clicked():
            result[0] = None
            dialog.destroy()
        
        button_frame = tk.Frame(dialog, bg="#f0f0f0")
        button_frame.pack(pady=15)
        
        ok_button = tk.Button(button_frame, text="OK", command=ok_clicked,
                 bg="green", fg="white", font=("Arial", 9, "bold"), width=8)
        ok_button.pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Annuler", command=cancel_clicked,
                 bg="gray", fg="white", font=("Arial", 9, "bold"), width=8).pack(side=tk.LEFT, padx=10)
        
        entry.bind('<KeyRelease>', lambda e: validate_input())
        validate_input()  # Validation initiale
        
        entry.bind('<Return>', lambda e: ok_clicked())
        entry.bind('<Escape>', lambda e: cancel_clicked())
        
        # Attendre la fermeture de la fenêtre
        dialog.wait_window()
        return result[0]

    def show_long_text_dialog(self, message):
        """Affiche une boîte de dialogue spécialement conçue pour les longs commentaires ou textes"""
        result = [None]
        dialog = tk.Toplevel(self.root)
        dialog.title("Saisie de texte long")
        dialog.geometry("600x600")
        dialog.resizable(True, True)
        dialog.configure(bg="#f0f0f0")
        dialog.transient(self.root)
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        
        # Centrer la fenêtre
        dialog.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 150,
            self.root.winfo_rooty() + 150
        ))
        
        # Message d'instruction
        tk.Label(dialog, text=message, bg="#f0f0f0", font=("Arial", 11, "bold")).pack(pady=15)
        
        # Frame pour le texte avec scrollbar
        text_frame = tk.Frame(dialog, bg="#f0f0f0")
        text_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Zone de texte avec scrollbar
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), height=15, width=60)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text_widget.focus_set()
        
        # Compteur de caractères
        char_count_label = tk.Label(dialog, text="Caractères: 0", bg="#f0f0f0", font=("Arial", 9), fg="#666")
        char_count_label.pack(pady=5)
        
        def update_char_count(event=None):
            content = text_widget.get("1.0", tk.END).strip()
            char_count_label.config(text=f"Caractères: {len(content)}")
            validate_text()
        
        def validate_text():
            content = text_widget.get("1.0", tk.END).strip()
            if content:
                ok_button.config(state="normal", bg="green")
                text_widget.config(bg="white")
            else:
                ok_button.config(state="disabled", bg="#cccccc")
                text_widget.config(bg="#ffcccc")

        text_widget.bind('<KeyRelease>', update_char_count)
        text_widget.bind('<Button-1>', update_char_count)
        
        def ok_clicked():
            content = text_widget.get("1.0", tk.END).strip()
            result[0] = content if content else None
            dialog.destroy()
            # Désactiver VERR MAJ après validation
            caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
            if caps_on:
                ctypes.windll.user32.keybd_event(0x14, 0x45, 0, 0)
                ctypes.windll.user32.keybd_event(0x14, 0x45, 2, 0)
        
        def cancel_clicked():
            result[0] = None
            dialog.destroy()
        
        # Boutons
        button_frame = tk.Frame(dialog, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        ok_button = tk.Button(button_frame, text="OK", command=ok_clicked,
                 bg="green", fg="white", font=("Arial", 10, "bold"), width=12, height=2)
        ok_button.pack(side=tk.LEFT, padx=15)
        tk.Button(button_frame, text="Annuler", command=cancel_clicked,
                 bg="gray", fg="white", font=("Arial", 10, "bold"), width=12, height=2).pack(side=tk.LEFT, padx=15)
        
        validate_text()  # Validation initiale
        
        # Raccourcis clavier
        dialog.bind('<Control-Return>', lambda e: ok_clicked())
        dialog.bind('<Escape>', lambda e: cancel_clicked())
        
        # Attendre la fermeture de la fenêtre
        dialog.wait_window()
        return result[0]

    def show_warning_dialog(self):
        """Affiche une boîte de dialogue d'avertissement personnalisée"""
        self.warning_dialog = tk.Toplevel(self.root)
        self.warning_dialog.title("ATTENTION")
        self.warning_dialog.geometry("500x700")
        self.warning_dialog.resizable(False, False)
        self.warning_dialog.configure(bg="#f0f0f0")
        self.warning_dialog.transient(self.root)
        self.warning_dialog.attributes('-topmost', True)
        self.warning_dialog.grab_set()
        self.warning_dialog.lift()
        self.warning_dialog.focus_force()
        
        # Centrer la fenêtre
        self.warning_dialog.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 100
        ))
        
        # Titre en gras et rouge
        title_label = tk.Label(self.warning_dialog, text="ATTENTION", 
                              font=("Arial", 16, "bold"), 
                              fg="red", bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Message principal
        message = ("Le script que vous êtes sur le point de lancer peut supprimer "
                  "des éléments de manière involontaire et incontrôlable.\n\n"
                  "Pour éviter que cela se produise, NE TOUCHEZ EN AUCUN CAS "
                  "LA SOURIS OU LE CLAVIER.\n\n"
                  "IMPORTANT: Il est conseillé de désactiver Verr. Maj. Avant l'exécution.\n\n"
                  "Appuyez sur Ok ou Entrée pour démarrer ou Annuler pour annuler le lancement.")
        
        message_label = tk.Label(self.warning_dialog, text=message, 
                                font=("Arial", 11),
                                wraplength=450, justify="center",
                                bg="#f0f0f0")
        message_label.pack(pady=10, padx=20)
        
        # Compteur de boucles restantes
        self.loop_counter_label = tk.Label(self.warning_dialog, text="", 
                                          font=("Arial", 12, "bold"), 
                                          fg="#0066cc", bg="#f0f0f0")
        self.loop_counter_label.pack(pady=10)
        
        # Label d'avertissement Verr Maj
        caps_warning = tk.Label(self.warning_dialog, text="",
                               fg="red", font=("Arial", 12, "bold"), bg="#f0f0f0")
        
        # Variable pour stocker le résultat
        result = [False]
        
        def on_ok():
            # Désactiver automatiquement le verr maj si activé
            caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
            if caps_on:
                ctypes.windll.user32.keybd_event(0x14, 0x45, 0, 0)
                ctypes.windll.user32.keybd_event(0x14, 0x45, 2, 0)
                time.sleep(0.2)
            result[0] = True
            # Ne pas fermer la dialog, juste changer les boutons
            ok_button.config(state="disabled", bg="#cccccc")
            cancel_button.config(text="Arrêter", command=on_stop, bg="#d32f2f")
            
        def on_cancel():
            result[0] = False
            self.warning_dialog.destroy()
            
        def on_stop():
            self.mouse_blocker.unblock_mouse()
            self.warning_dialog.destroy()
            sys.exit(0)
        
        # Boutons
        button_frame = tk.Frame(self.warning_dialog, bg="#f0f0f0")
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        ok_button = tk.Button(button_frame, text="OK", command=on_ok,
                             bg="#d32f2f", fg="white", font=("Arial", 10, "bold"),
                             width=10, height=2)
        ok_button.pack(side=tk.LEFT, padx=20)
        
        cancel_button = tk.Button(button_frame, text="Annuler", command=on_cancel,
                                 bg="#757575", fg="white", font=("Arial", 10, "bold"),
                                 width=10, height=2)
        cancel_button.pack(side=tk.LEFT, padx=20)
        
        # Raccourci clavier pour Entrée
        self.warning_dialog.bind('<Return>', lambda e: on_ok())
        self.warning_dialog.focus_set()
        
        # Fonction pour vérifier l'état de Verr Maj
        def check_caps_lock_state():
            caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
            if caps_on:
                caps_warning.pack(pady=10, before=button_frame)
            else:
                caps_warning.pack_forget()
            if hasattr(self, 'warning_dialog') and self.warning_dialog.winfo_exists():
                self.warning_dialog.after(200, check_caps_lock_state)
        
        # Démarrer la vérification
        check_caps_lock_state()
        
        # Attendre que l'utilisateur clique OK
        while not result[0] and hasattr(self, 'warning_dialog') and self.warning_dialog.winfo_exists():
            self.warning_dialog.update()
            time.sleep(0.1)
        
        return result[0]

if __name__ == "__main__":
    app = MacroApp()
    app.root.mainloop()