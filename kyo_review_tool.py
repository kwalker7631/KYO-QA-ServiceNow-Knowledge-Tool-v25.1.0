# kyo_review_tool.py
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from pathlib import Path
import re
import importlib

from config import BRAND_COLORS
import config as config_module 

#==============================================================
# --- MODIFICATION: Rewritten to avoid f-string syntax error ---
#==============================================================
def generate_regex_from_sample(sample: str) -> str:
    """
    Analyzes a sample string and generates a precise regex pattern by keeping
    all letters and symbols literal and only generalizing the numbers.
    """
    if not sample or not sample.strip():
        return ""

    # Step 1: Escape any special regex characters in the user's sample text.
    escaped_sample = re.escape(sample.strip())

    # Step 2: In the escaped string, find all digit sequences and replace them
    # with the regex token for one or more digits, `\d+`.
    pattern_with_digit_wildcard = re.sub(r'\d+', r'\\d+', escaped_sample)
    
    # Step 3: Construct the final pattern. This is now safe.
    return f"\\b{pattern_with_digit_wildcard}\\b"
#==============================================================
# --- END OF MODIFICATION ---
#==============================================================


class ReviewWindow(tk.Toplevel):
    """A generic regex pattern management tool that safely edits a separate custom_patterns.py file."""
    def __init__(self, parent, pattern_name: str, pattern_label: str, file_info: dict = None):
        super().__init__(parent)
        
        self.pattern_name = pattern_name
        self.pattern_label = pattern_label
        self.file_info = file_info
        self.custom_patterns_path = Path("custom_patterns.py")
        
        self.title(f"Manage Custom: {self.pattern_label}")
        self.geometry("1000x700")
        self.configure(bg=BRAND_COLORS["background"])

        paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned_window.pack(fill=tk.BOTH, expand=True)

        manager_frame = ttk.Frame(paned_window, padding=10)
        manager_frame.columnconfigure(0, weight=1)
        manager_frame.rowconfigure(1, weight=1)
        paned_window.add(manager_frame, width=400)

        text_frame = ttk.Frame(paned_window, padding=10)
        paned_window.add(text_frame)
        
        ttk.Label(manager_frame, text=self.pattern_label, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        
        self.pattern_listbox = tk.Listbox(manager_frame, font=("Consolas", 9), height=15)
        self.pattern_listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        self.pattern_listbox.bind("<<ListboxSelect>>", self.on_pattern_select)
        pattern_scrollbar = ttk.Scrollbar(manager_frame, orient="vertical", command=self.pattern_listbox.yview)
        pattern_scrollbar.grid(row=1, column=2, sticky="ns", pady=5)
        self.pattern_listbox.config(yscrollcommand=pattern_scrollbar.set)
        
        btn_frame = ttk.Frame(manager_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Add as New", command=self.add_pattern).pack(side="left", padx=5)
        self.remove_btn = ttk.Button(btn_frame, text="Remove Selected", command=self.remove_pattern, state=tk.DISABLED)
        self.remove_btn.pack(side="left", padx=5)
        
        ttk.Label(manager_frame, text="Test / Edit Pattern:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10,0))
        self.pattern_entry = ttk.Entry(manager_frame, font=("Consolas", 10))
        self.pattern_entry.grid(row=4, column=0, columnspan=2, sticky="ew")
        
        test_save_frame = ttk.Frame(manager_frame)
        test_save_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.suggest_btn = ttk.Button(test_save_frame, text="Suggest from Highlight", command=self.on_suggest_pattern)
        self.suggest_btn.pack(side="left", padx=5)
        self.test_btn = ttk.Button(test_save_frame, text="Test Pattern", command=self.test_pattern)
        self.test_btn.pack(side="left", padx=5)
        ttk.Button(test_save_frame, text="Update List", command=self.update_pattern_in_list).pack(side="left", padx=5)
        
        ttk.Button(manager_frame, text="Save All Patterns", style="Red.TButton", command=self.save_patterns_to_config).grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

        self.pdf_text = tk.Text(text_frame, wrap="word", font=("Consolas", 9), relief="solid", borderwidth=1)
        self.pdf_text.pack(fill="both", expand=True, side="left")
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.pdf_text.yview)
        text_scrollbar.pack(fill="y", side="right")
        self.pdf_text.config(yscrollcommand=text_scrollbar.set)
        self.pdf_text.tag_configure("highlight", background="yellow", foreground="black")

        if self.file_info:
            self.load_text_file()
        else:
            self.suggest_btn.config(state=tk.DISABLED)
            self.test_btn.config(state=tk.DISABLED)
            self.pdf_text.insert("1.0", "No file selected.\n\nManage patterns on the left without testing.")
            self.pdf_text.config(state=tk.DISABLED)
            
        self.load_patterns_from_config()

    def load_patterns_from_config(self):
        """Dynamically loads the specified pattern list from the custom_patterns.py file."""
        self.pattern_listbox.delete(0, tk.END)
        patterns_to_load = []
        try:
            import custom_patterns as custom_module
            importlib.reload(custom_module)
            patterns_to_load = getattr(custom_module, self.pattern_name, [])
        except (ImportError, SyntaxError):
            pass 
        for pattern in patterns_to_load:
            self.pattern_listbox.insert(tk.END, pattern)
    
    def save_patterns_to_config(self):
        """Re-writes all pattern lists into the custom_patterns.py file correctly."""
        all_patterns_in_listbox = self.pattern_listbox.get(0, tk.END)
        msg = f"This will save {len(all_patterns_in_listbox)} patterns to the {self.pattern_name} list in custom_patterns.py.\n\nAre you sure?"
        if not messagebox.askyesno("Confirm Save", msg, parent=self):
            return

        try:
            all_lists_to_save = {self.pattern_name: list(all_patterns_in_listbox)}
            all_possible_pattern_names = ["MODEL_PATTERNS", "QA_NUMBER_PATTERNS"]
            
            try:
                import custom_patterns as custom_module
                importlib.reload(custom_module)
                for name in all_possible_pattern_names:
                    if name != self.pattern_name:
                        if name not in all_lists_to_save:
                            all_lists_to_save[name] = getattr(custom_module, name, [])
            except (ImportError, SyntaxError):
                pass

            file_content = "# custom_patterns.py\n# This file stores user-defined regex patterns.\n"
            
            for name, patterns in all_lists_to_save.items():
                file_content += f"\n{name} = [\n"
                for pattern in patterns:
                    safe_pattern = pattern.replace("'", "\\'")
                    file_content += f"    r'{safe_pattern}',\n"
                file_content += "]\n"
            
            self.custom_patterns_path.write_text(file_content, encoding='utf-8')
            messagebox.showinfo("Success", "Custom patterns saved successfully!\nChanges will apply on the next run.", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save patterns to file:\n{e}", parent=self)

    def update_pattern_in_list(self):
        new_pattern = self.pattern_entry.get().strip()
        if not new_pattern:
            messagebox.showwarning("Input Error", "Test/Edit Pattern box is empty.", parent=self)
            return
            
        selection_indices = self.pattern_listbox.curselection()
        if not selection_indices:
            self.pattern_listbox.insert(tk.END, new_pattern)
        else:
            idx = selection_indices[0]
            self.pattern_listbox.delete(idx)
            self.pattern_listbox.insert(idx, new_pattern)

    def on_pattern_select(self, event):
        selection_indices = self.pattern_listbox.curselection()
        if not selection_indices:
            self.remove_btn.config(state=tk.DISABLED)
            self.pattern_entry.delete(0, tk.END)
            return
        selected_pattern = self.pattern_listbox.get(selection_indices[0])
        self.pattern_entry.delete(0, tk.END)
        self.pattern_entry.insert(0, selected_pattern)
        self.remove_btn.config(state=tk.NORMAL)

    def add_pattern(self):
        new_pattern = self.pattern_entry.get().strip()
        if new_pattern:
            self.pattern_listbox.insert(tk.END, new_pattern)
            self.pattern_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "Test/Edit Pattern box is empty. Cannot add.", parent=self)

    def remove_pattern(self):
        selection_indices = self.pattern_listbox.curselection()
        if not selection_indices: return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to remove the selected pattern?"):
            self.pattern_listbox.delete(selection_indices[0])
            self.on_pattern_select(None)

    def test_pattern(self):
        self.pdf_text.tag_remove("highlight", "1.0", "end")
        pattern_str = self.pattern_entry.get()
        if not pattern_str:
            messagebox.showwarning("Warning", "Test Pattern box cannot be empty.", parent=self)
            return
        try:
            content = self.pdf_text.get("1.0", "end")
            matches = list(re.finditer(pattern_str, content, re.IGNORECASE))
            if not matches:
                messagebox.showinfo("No Matches", "The pattern did not find any matches in the text.", parent=self)
                return
            for match in matches:
                start, end = match.span()
                self.pdf_text.tag_add("highlight", f"1.0+{start}c", f"1.0+{end}c")
            self.pdf_text.see(f"1.0+{matches[0].start()-100}c")
            messagebox.showinfo("Success!", f"Found {len(matches)} match(es).", parent=self)
        except re.error as e:
            messagebox.showerror("Invalid Pattern", f"The regular expression is invalid:\n{e}", parent=self)
            
    def on_suggest_pattern(self):
        try:
            selected_text = self.pdf_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if not selected_text or not selected_text.strip():
                messagebox.showwarning("No Selection", "Please highlight text to generate a pattern.", parent=self)
                return
            suggested_pattern = generate_regex_from_sample(selected_text)
            self.pattern_entry.delete(0, tk.END)
            self.pattern_entry.insert(0, suggested_pattern)
            messagebox.showinfo("Pattern Suggested", "A pattern has been generated in the 'Test / Edit' box.", parent=self)
        except tk.TclError:
            messagebox.showwarning("No Selection", "Please highlight text to generate a pattern.", parent=self)
            
    def load_text_file(self):
        try:
            if self.file_info and "txt_path" in self.file_info:
                txt_path = self.file_info["txt_path"]
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.pdf_text.insert("1.0", content)
            else:
                raise ValueError("No file information was provided to load.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load text file:\n{e}", parent=self)
            self.pdf_text.insert("1.0", "Error: Could not load text file for review.")
            self.pdf_text.config(state=tk.DISABLED)