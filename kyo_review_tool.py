# kyo_review_tool.py
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from pathlib import Path
import re
import importlib

from config import BRAND_COLORS
import config as config_module 

def generate_regex_from_sample(sample: str) -> str:
    if not sample or not sample.strip(): return ""
    escaped = re.escape(sample.strip())
    return f"\\b{re.sub(r'\\d+', r'\\\\d+', escaped)}\\b"

class ReviewWindow(tk.Toplevel):
    def __init__(self, parent, pattern_name, label, file_info=None):
        super().__init__(parent)
        
        self.pattern_name, self.label, self.file_info = pattern_name, label, file_info
        self.custom_patterns_path = Path("custom_patterns.py")
        self.title(f"Manage Custom: {self.label}"); self.geometry("1000x700")

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED); paned.pack(fill=tk.BOTH, expand=True)
        mgr_frame = ttk.Frame(paned, padding=10); mgr_frame.columnconfigure(0, weight=1); mgr_frame.rowconfigure(1, weight=1); paned.add(mgr_frame, width=400)
        txt_frame = ttk.Frame(paned, padding=10); paned.add(txt_frame)
        
        ttk.Label(mgr_frame, text=self.label, font=("Segoe UI", 12, "bold")).grid(row=0, sticky="w")
        self.listbox = tk.Listbox(mgr_frame, font=("Consolas", 9)); self.listbox.grid(row=1, sticky="nsew", pady=5); self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        ttk.Label(mgr_frame, text="Test/Edit Pattern:", font=("Segoe UI", 10, "bold")).grid(row=2, sticky="w", pady=(5,0))
        self.entry = ttk.Entry(mgr_frame, font=("Consolas", 10)); self.entry.grid(row=3, sticky="ew")
        
        btn_frame = ttk.Frame(mgr_frame); btn_frame.grid(row=4, pady=5)
        self.suggest_btn = ttk.Button(btn_frame, text="💡 Suggest", command=self.suggest); self.suggest_btn.pack(side="left")
        self.test_btn = ttk.Button(btn_frame, text="🧪 Test", command=self.test); self.test_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="➕ Update List", command=self.update_list).pack(side="left")
        self.remove_btn = ttk.Button(btn_frame, text="➖ Remove", command=self.remove, state=tk.DISABLED); self.remove_btn.pack(side="left", padx=5)
        ttk.Button(mgr_frame, text="✔️ Save All and Close", style="Red.TButton", command=self.save).grid(row=5, pady=10, sticky="ew")

        self.pdf_text = tk.Text(txt_frame, wrap="word"); self.pdf_text.pack(fill="both", expand=True)
        self.pdf_text.tag_configure("highlight", background=BRAND_COLORS["warning_yellow"])

        if self.file_info: self.load_text()
        else:
            self.suggest_btn.config(state=tk.DISABLED); self.test_btn.config(state=tk.DISABLED)
            self.pdf_text.insert("1.0", "No file loaded."); self.pdf_text.config(state=tk.DISABLED)
        self.load_patterns()

    def load_patterns(self):
        self.listbox.delete(0, tk.END)
        try:
            mod = importlib.import_module("custom_patterns"); importlib.reload(mod)
            for p in getattr(mod, self.pattern_name, []): self.listbox.insert(tk.END, p)
        except (ImportError, SyntaxError): pass

    def save(self):
        patterns = self.listbox.get(0, tk.END)
        if not messagebox.askyesno("Confirm Save", f"Save {len(patterns)} patterns to custom_patterns.py?"): return
        
        try:
            all_lists = {self.pattern_name: list(patterns)}
            all_names = ["MODEL_PATTERNS", "QA_NUMBER_PATTERNS"]
            try:
                mod = importlib.import_module("custom_patterns"); importlib.reload(mod)
                for name in all_names:
                    if name != self.pattern_name: all_lists[name] = getattr(mod, name, [])
            except (ImportError, SyntaxError): pass

            content = "# custom_patterns.py\n# User-defined regex patterns.\n"
            for name, pats in all_lists.items():
                content += f"\n{name} = [\n"
                for p in pats: content += f"    r'{p.replace(chr(39), chr(92)+chr(39))}',\n"
                content += "]\n"
            
            self.custom_patterns_path.write_text(content, encoding='utf-8')
            messagebox.showinfo("Success", "Custom patterns saved!", parent=self)
            self.destroy()
        except Exception as e: messagebox.showerror("Save Failed", f"Could not save file:\n{e}", parent=self)

    def update_list(self):
        new_p = self.entry.get().strip()
        if not new_p: return
        sel = self.listbox.curselection()
        if not sel: self.listbox.insert(tk.END, new_p)
        else: self.listbox.delete(sel[0]); self.listbox.insert(sel[0], new_p)

    def on_select(self, e):
        sel = self.listbox.curselection()
        self.remove_btn.config(state=tk.NORMAL if sel else tk.DISABLED)
        if sel: self.entry.delete(0, tk.END); self.entry.insert(0, self.listbox.get(sel[0]))

    def remove(self):
        sel = self.listbox.curselection()
        if sel and messagebox.askyesno("Confirm Delete", "Remove selected pattern?"):
            self.listbox.delete(sel[0]); self.on_select(None)
            
    def test(self):
        self.pdf_text.tag_remove("highlight", "1.0", "end")
        p = self.entry.get(); txt = self.pdf_text.get("1.0", "end")
        if not p: return
        try:
            matches = list(re.finditer(p, txt, re.IGNORECASE))
            if not matches: messagebox.showinfo("No Matches", "Pattern found no matches.", parent=self); return
            for m in matches: self.pdf_text.tag_add("highlight", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            self.pdf_text.see(f"1.0+{matches[0].start()-100}c"); messagebox.showinfo("Success!", f"Found {len(matches)} matches.", parent=self)
        except re.error as e: messagebox.showerror("Invalid Pattern", f"Regex error:\n{e}", parent=self)
            
    def suggest(self):
        try:
            sel = self.pdf_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if not sel.strip(): messagebox.showwarning("No Selection", "Highlight text first.", parent=self); return
            self.entry.delete(0, tk.END); self.entry.insert(0, generate_regex_from_sample(sel))
        except tk.TclError: messagebox.showwarning("No Selection", "Highlight text first.", parent=self)
            
    def load_text(self):
        try:
            with open(self.file_info["txt_path"], 'r', encoding='utf-8') as f: self.pdf_text.insert("1.0", f.read())
        except Exception as e: messagebox.showerror("Error", f"Failed to load text:\n{e}", parent=self)