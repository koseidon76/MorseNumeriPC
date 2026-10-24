import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue

try:
    import soundcard as sc
    import numpy as np
except Exception:
    sc = None
    np = None


class MorseNumeriPC:
    def __init__(self, root):
        self.root = root
        self.root.title("MorseNumeriPC")
        self.root.geometry("340x530")
        self.root.resizable(False, False)

        self.running = False
        self.session_id = 0
        self.worker = None
        self.symbols = ""
        self.last_tone_time = 0.0
        self.tone_start = None
        self.last_signal_time = 0.0
        self.output_queue = queue.Queue()

        self.threshold = tk.DoubleVar(value=0.06)
        self.dot_duration = tk.DoubleVar(value=0.25)
        self.status = tk.StringVar(value="Fermo")

        style = ttk.Style()
        style.configure("Play.TButton", font=("Segoe UI", 11, "bold"), padding=(6, 8))
        style.configure("Big.TButton", font=("Segoe UI", 11, "bold"), padding=(6, 12))

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="MorseNumeriPC", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Ascolta l'audio del PC e riconosce cifre Morse.").pack(anchor="w", pady=(2, 8))

        ttk.Label(frame, text="Sensibilità (predefinita: massima)").pack(anchor="w")
        self.threshold_scale = ttk.Scale(frame, from_=0.001, to=0.06, variable=self.threshold,
                                         orient="horizontal")
        self.threshold_scale.pack(fill="x", pady=(0, 3))
        self.threshold_label = ttk.Label(frame, text="0.060")
        self.threshold_label.pack(anchor="e")

        ttk.Label(frame, text="Durata punto (secondi)").pack(anchor="w", pady=(7, 0))
        ttk.Scale(frame, from_=0.08, to=0.5, variable=self.dot_duration,
                  orient="horizontal").pack(fill="x")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(8, 4))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(0, 7))
        ttk.Button(buttons, text="Avvia", command=self.start,
                   style="Play.TButton").pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(buttons, text="Ferma", command=self.stop,
                   style="Play.TButton").pack(side="left", expand=True, fill="x", padx=(3, 0))

        ttk.Label(frame, text="Numeri riconosciuti").pack(anchor="w")
        self.output = tk.Text(frame, height=9, wrap="word", font=("Consolas", 14))
        self.output.pack(fill="both", expand=True, pady=(3, 7))

        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions, text="Copia", command=self.copy,
                   style="Big.TButton").pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(actions, text="RESET MEMORIA", command=self.reset_memory,
                   style="Big.TButton").pack(side="left", expand=True, fill="x", padx=(3, 0))

        self.threshold.trace_add("write", self.update_threshold_label)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.poll_queue)

    def update_threshold_label(self, *_):
        self.threshold_label.config(text=f"{self.threshold.get():.3f}")

    def start(self):
        if sc is None or np is None:
            messagebox.showerror("Librerie mancanti", "Dipendenze audio mancanti. Ricrea l'EXE usando il workflow GitHub.")
            return
        if self.running:
            return
        self.session_id += 1
        sid = self.session_id
        self.running = True
        self.symbols = ""
        self.tone_start = None
        self.last_tone_time = time.time()
        self.last_signal_time = time.time()
        self.status.set("In ascolto…")
        self.worker = threading.Thread(target=self.listen, args=(sid,), daemon=True)
        self.worker.start()

    def stop(self):
        self.running = False
        self.status.set("Fermo")

    def reset_memory(self):
        self.session_id += 1
        self.running = False
        self.symbols = ""
        self.tone_start = None
        self.last_tone_time = 0.0
        self.last_signal_time = 0.0
        while True:
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break
        self.output.delete("1.0", "end")
        self.status.set("Memoria azzerata")

    def copy(self):
        text = self.output.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def listen(self, sid):
        try:
            speaker = sc.default_speaker()
            mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
            samplerate = 44100
            block_seconds = 0.04
            threshold = float(self.threshold.get())
            while self.running and sid == self.session_id:
                audio = mic.record(samplerate=samplerate, numframes=int(samplerate * block_seconds))
                if not self.running or sid != self.session_id:
                    break
                level = float(np.sqrt(np.mean(np.square(audio))))
                now = time.time()
                if level >= threshold:
                    if self.tone_start is None:
                        self.tone_start = now
                    self.last_signal_time = now
                else:
                    if self.tone_start is not None:
                        duration = now - self.tone_start
                        dot = max(0.08, float(self.dot_duration.get()))
                        symbol = "." if duration < dot * 2.0 else "-"
                        self.symbols += symbol
                        self.tone_start = None
                        self.last_tone_time = now
                    if self.symbols and (now - self.last_tone_time) > max(0.22, float(self.dot_duration.get()) * 2.2):
                        digit = self.decode_digit(self.symbols)
                        self.symbols = ""
                        if digit is not None:
                            self.output_queue.put((sid, digit))
                        self.last_tone_time = now
        except Exception as e:
            self.output_queue.put((sid, "__ERROR__" + str(e)))

    @staticmethod
    def decode_digit(code):
        table = {
            "-----": "0", ".----": "1", "..---": "2", "...--": "3",
            "....-": "4", ".....": "5", "-....": "6", "--...": "7",
            "---..": "8", "----.": "9",
        }
        return table.get(code)

    def poll_queue(self):
        try:
            while True:
                sid, value = self.output_queue.get_nowait()
                if sid != self.session_id:
                    continue
                if value.startswith("__ERROR__"):
                    self.status.set("Errore audio")
                    self.running = False
                    messagebox.showerror("Errore audio", value[len("__ERROR__"):])
                    continue
                # Numeri accodati in riga (nessun a capo)
                self.output.insert("end", value)
                self.output.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def close(self):
        self.session_id += 1
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MorseNumeriPC(root)
    root.mainloop()
