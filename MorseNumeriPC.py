import tkinter as tk
from tkinter import ttk, messagebox
import threading, time
import numpy as np
try:
    import soundcard as sc
except ImportError:
    sc = None

DIGITS = {"-----":"0",".----":"1","..---":"2","...--":"3","....-":"4",".....":"5","-....":"6","--...":"7","---..":"8","----.":"9"}

class App:
    def __init__(self, root):
        self.root=root; root.title("Morse Numeri PC"); root.geometry("310x430"); root.resizable(False,False)
        self.running=False; self.output=""; self.dot=tk.DoubleVar(value=0.25); self.threshold=tk.DoubleVar(value=0.015)
        self.status=tk.StringVar(value="Pronto"); self.symbols=""; self.last_tone_end=0.; self.last_state=False; self.state_start=0.
        f=ttk.Frame(root,padding=9); f.pack(fill="both",expand=True)
        ttk.Label(f,text="Decodifica i numeri Morse dall'audio del PC",wraplength=285).pack(anchor="w",pady=(0,7))
        ttk.Label(f,text="Sensibilità").pack(anchor="w")
        r=ttk.Frame(f); r.pack(fill="x")
        ttk.Scale(r,from_=0.003,to=0.06,variable=self.threshold,orient="horizontal").pack(side="left",fill="x",expand=True)
        self.th_label=ttk.Label(r,text="0.015",width=5); self.th_label.pack(side="right",padx=(5,0))
        self.threshold.trace_add("write",lambda *_:self.th_label.config(text=f"{self.threshold.get():.3f}"))
        ttk.Label(f,text="Durata punto (secondi)").pack(anchor="w",pady=(6,0))
        ttk.Spinbox(f,from_=0.10,to=0.40,increment=0.01,textvariable=self.dot,width=7).pack(anchor="w",pady=(2,7))
        ttk.Label(f,textvariable=self.status).pack(anchor="w",pady=(0,4))
        ttk.Label(f,text="Codici decodificati").pack(anchor="w")
        self.box=tk.Text(f,height=9,font=("Consolas",15),wrap="word"); self.box.pack(fill="both",expand=True,pady=(3,7))
        row=ttk.Frame(f); row.pack(fill="x")
        self.start_btn=ttk.Button(row,text="Avvia ascolto",command=self.start); self.start_btn.pack(side="left",fill="x",expand=True)
        self.stop_btn=ttk.Button(row,text="Ferma",command=self.stop,state="disabled"); self.stop_btn.pack(side="left",padx=(4,0),fill="x",expand=True)
        row2=ttk.Frame(f); row2.pack(fill="x",pady=(4,0))
        ttk.Button(row2,text="Copia cifre",command=self.copy).pack(side="left",fill="x",expand=True)
        ttk.Button(row2,text="Cancella",command=self.clear).pack(side="left",padx=(4,0),fill="x",expand=True)
        ttk.Label(f,text="L'audio resta sul PC; non viene inviato online.",foreground="#555",wraplength=285).pack(anchor="w",pady=(7,0))
    def start(self):
        if sc is None: messagebox.showerror("Errore","Dispositivo audio non disponibile."); return
        try:
            d=float(self.dot.get())
            if not 0.10<=d<=0.40: raise ValueError
            self.dot_value=d
        except Exception: messagebox.showerror("Valore non valido","Usa una durata tra 0,10 e 0,40."); return
        self.running=True; self.start_btn.config(state="disabled"); self.stop_btn.config(state="normal"); self.status.set("Ascolto audio del PC…")
        threading.Thread(target=self.listen,daemon=True).start()
    def stop(self):
        self.running=False; self.start_btn.config(state="normal"); self.stop_btn.config(state="disabled"); self.status.set("Fermo")
    def copy(self):
        if self.output: self.root.clipboard_clear(); self.root.clipboard_append(self.output); self.status.set("Codici copiati")
        else: self.status.set("Nessun codice ancora")
    def clear(self):
        self.output=""; self.box.delete("1.0","end"); self.symbols=""; self.last_tone_end=0.
        self.status.set("Pronto" if not self.running else "Ascolto audio del PC…")
    def add_digit(self,digit):
        compact=self.output.replace("\n","")+digit
        self.output="\n".join(compact[i:i+5] for i in range(0,len(compact),5))
        self.box.delete("1.0","end"); self.box.insert("end",self.output); self.box.see("end")
    def decode(self):
        seq=self.symbols; self.symbols=""
        if seq in DIGITS: self.root.after(0,lambda d=DIGITS[seq]:self.add_digit(d))
    def listen(self):
        try:
            speaker=sc.default_speaker(); mic=sc.get_microphone(id=str(speaker.name),include_loopback=True)
            now=time.monotonic(); self.last_state=False; self.state_start=now; self.last_tone_end=now
            while self.running:
                audio=mic.record(samplerate=48000,numframes=480)
                mono=np.mean(audio,axis=1) if audio.ndim>1 else audio
                rms=float(np.sqrt(np.mean(np.square(mono))+1e-12)); active=rms>float(self.threshold.get()); now=time.monotonic(); unit=self.dot_value
                if active!=self.last_state:
                    duration=now-self.state_start
                    if self.last_state:
                        if duration>=unit*0.45: self.symbols += "." if duration<unit*2.0 else "-"
                        self.last_tone_end=now
                    elif self.symbols and now-self.last_tone_end>=unit*2.5: self.decode()
                    self.last_state=active; self.state_start=now
                elif not active and self.symbols and now-self.last_tone_end>=unit*3.2: self.decode()
        except Exception as e: self.root.after(0,lambda msg=str(e):self.fail(msg))
    def fail(self,msg):
        self.running=False; self.start_btn.config(state="normal"); self.stop_btn.config(state="disabled"); self.status.set("Errore audio")
        messagebox.showerror("Errore audio",msg+"\nControlla l'uscita audio predefinita di Windows.")
if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
