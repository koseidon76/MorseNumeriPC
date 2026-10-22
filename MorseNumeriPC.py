import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np

try:
    import soundcard as sc
except ImportError:
    sc = None

DIGITS = {
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9"
}

class MorseNumbersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Morse Numeri PC")
        self.root.geometry("620x410")
        self.root.minsize(560, 360)
        self.running = False
        self.worker = None
        self.output = ""
        self.dot_unit = 0.12
        self.threshold = 0.015
        self.freq_low = 350
        self.freq_high = 1400
        self.last_state = False
        self.state_start = 0.0
        self.symbols = ""
        self.last_end = 0.0
        self.samplerate = 48000
        self.blocksize = 480

        frm = ttk.Frame(root, padding=14)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Cattura l'audio riprodotto dal PC e decodifica le cifre Morse.",
                  wraplength=570).pack(anchor="w", pady=(0, 10))

        row = ttk.Frame(frm)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="Sensibilità (soglia):").pack(side="left")
        self.threshold_var = tk.DoubleVar(value=self.threshold)
        ttk.Scale(row, from_=0.002, to=0.08, variable=self.threshold_var,
                  orient="horizontal").pack(side="left", fill="x", expand=True, padx=8)
        self.threshold_label = ttk.Label(row, text="0.015")
        self.threshold_label.pack(side="right")
        self.threshold_var.trace_add("write", self.update_threshold_label)

        row2 = ttk.Frame(frm)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Durata punto (secondi):").pack(side="left")
        self.unit_var = tk.DoubleVar(value=self.dot_unit)
        ttk.Spinbox(row2, from_=0.04, to=0.5, increment=0.01, textvariable=self.unit_var,
                    width=8).pack(side="left", padx=8)
        ttk.Label(row2, text="Esempio: 0,12").pack(side="left")

        self.status = tk.StringVar(value="Fermo")
        ttk.Label(frm, textvariable=self.status).pack(anchor="w", pady=(10, 4))
        ttk.Label(frm, text="Cifre decodificate:").pack(anchor="w")
        self.result = tk.Text(frm, height=5, font=("Consolas", 18), wrap="char")
        self.result.pack(fill="both", expand=True, pady=(3, 8))

        buttons = ttk.Frame(frm)
        buttons.pack(fill="x")
        self.start_btn = ttk.Button(buttons, text="Avvia ascolto", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(buttons, text="Ferma", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        ttk.Button(buttons, text="Copia cifre", command=self.copy).pack(side="left")
        ttk.Button(buttons, text="Cancella", command=self.clear).pack(side="left", padx=6)

        ttk.Label(frm, text="Nota: funziona meglio con toni Morse puliti e pause regolari. "
                  "Non invia audio a Internet.", wraplength=570).pack(anchor="w", pady=(9, 0))

    def update_threshold_label(self, *_):
        self.threshold_label.config(text=f"{self.threshold_var.get():.3f}")

    def start(self):
        if sc is None:
            messagebox.showerror("Libreria mancante",
                "Manca la libreria soundcard. Avvia INSTALLA.bat nella cartella del programma.")
            return
        try:
            self.dot_unit = float(self.unit_var.get())
            if not 0.04 <= self.dot_unit <= 0.5:
                raise ValueError
        except Exception:
            messagebox.showerror("Valore non valido", "La durata del punto deve essere tra 0,04 e 0,50 secondi.")
            return
        self.threshold = float(self.threshold_var.get())
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.set("Ascolto audio del PC…")
        self.worker = threading.Thread(target=self.listen_loop, daemon=True)
        self.worker.start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Fermo")

    def copy(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output)
        self.status.set("Cifre copiate negli appunti")

    def clear(self):
        self.output = ""
        self.result.delete("1.0", "end")
        self.symbols = ""
        self.last_end = 0.0

    def append_digit(self, digit):
        self.output += digit
        self.result.insert("end", digit)
        self.result.see("end")

    def listen_loop(self):
        try:
            speaker = sc.default_speaker()
            mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
            if mic is None:
                raise RuntimeError("Non è stato trovato l'ingresso audio loopback.")
            blocksize = 480
            self.last_state = False
            self.state_start = time.monotonic()
            self.last_end = time.monotonic()
            self.symbols = ""
            while self.running:
                audio = mic.record(samplerate=self.samplerate, numframes=blocksize)
                if audio.ndim > 1:
                    mono = np.mean(audio, axis=1)
                else:
                    mono = audio
                rms = float(np.sqrt(np.mean(np.square(mono)) + 1e-12))
                active = rms > float(self.threshold_var.get())
                now = time.monotonic()
                if active != self.last_state:
                    duration = now - self.state_start
                    if self.last_state:
                        # End of tone: classify as dot or dash.
                        unit = max(0.04, float(self.unit_var.get()))
                        symbol = "." if duration < unit * 2.0 else "-"
                        self.symbols += symbol
                        self.last_end = now
                    else:
                        # Start of tone after silence; a gap >= 3 units ends a digit.
                        gap = now - self.last_end
                        unit = max(0.04, float(self.unit_var.get()))
                        if self.symbols and gap >= unit * 2.5:
                            self.decode_current()
                    self.last_state = active
                    self.state_start = now
                elif not active and self.symbols and (now - self.last_end) >= max(0.18, float(self.unit_var.get()) * 3.2):
                    self.decode_current()
                time.sleep(0.003)
        except Exception as e:
            self.root.after(0, lambda msg=str(e): self.fail(msg))

    def decode_current(self):
        code = self.symbols
        self.symbols = ""
        if code in DIGITS:
            self.root.after(0, lambda d=DIGITS[code]: self.append_digit(d))

    def fail(self, message):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Errore audio")
        messagebox.showerror("Errore di acquisizione audio",
            message + "\n\nControlla che Windows abbia un dispositivo di uscita audio predefinito.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MorseNumbersApp(root)
    root.mainloop()
