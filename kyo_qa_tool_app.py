# Update this section in kyo_qa_tool_app.py

# Find this section in the __init__ method:
def __init__(self):
    super().__init__()
    
    # ...existing code...
    
    # Replace the icon loading section with this improved version:
    # --- Load icons with graceful fallback ---
    try:
        from icon_utils import load_icon, get_text_icon, create_default_icons
        
        # Check if icons exist, create defaults if needed
        icons_available = create_default_icons()
        
        # Load icons with fallback to text representations
        if icons_available:
            self.start_icon = load_icon("start.png")
            self.pause_icon = load_icon("pause.png")
            self.stop_icon = load_icon("stop.png")
            self.rerun_icon = load_icon("rerun.png")
            self.open_icon = load_icon("open.png")
            self.browse_icon = load_icon("browse.png")
            self.patterns_icon = load_icon("patterns.png")
            self.exit_icon = load_icon("exit.png")
            self.fullscreen_icon = load_icon("fullscreen.png")
        else:
            # Use text fallbacks
            self.start_icon = None
            self.pause_icon = None
            self.stop_icon = None
            self.rerun_icon = None
            self.open_icon = None
            self.browse_icon = None
            self.patterns_icon = None
            self.exit_icon = None
            self.fullscreen_icon = None
    except ImportError:
        # Fall back to no icons if icon_utils.py is missing
        self.start_icon = None
        self.pause_icon = None
        self.stop_icon = None
        self.rerun_icon = None
        self.open_icon = None
        self.browse_icon = None
        self.patterns_icon = None
        self.exit_icon = None
        self.fullscreen_icon = None
        
    # ...continue with existing code...
    
# Then update the create_process_controls method to handle missing icons:
def _create_process_controls(self, parent):
    ctrl = ttk.LabelFrame(parent, text="2. Process & Manage", padding=10)
    ctrl.grid(row=1, column=0, sticky="ew", pady=5)
    ctrl.columnconfigure((0, 1, 2, 3), weight=1)

    # Create buttons with text fallbacks if icons are missing
    from icon_utils import get_text_icon
    
    self.process_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('start') if not self.start_icon else ''} START", 
        image=self.start_icon, 
        compound="left" if self.start_icon else "none", 
        command=self.start_processing, 
        style="Red.TButton"
    )
    self.process_btn.grid(row=0, column=0, columnspan=4, sticky="ew", pady=2)

    self.pause_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('pause') if not self.pause_icon else ''} Pause", 
        image=self.pause_icon, 
        compound="left" if self.pause_icon else "none", 
        command=self.toggle_pause, 
        state=tk.DISABLED
    )
    self.pause_btn.grid(row=1, column=0, sticky="ew", pady=2)
    
    # Update all other buttons similarly
    self.stop_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('stop') if not self.stop_icon else ''} Stop", 
        image=self.stop_icon, 
        compound="left" if self.stop_icon else "none", 
        command=self.stop_processing, 
        state=tk.DISABLED
    )
    self.stop_btn.grid(row=1, column=1, sticky="ew", pady=2)
    
    self.rerun_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('rerun') if not self.rerun_icon else ''} Re-run Flagged", 
        image=self.rerun_icon, 
        compound="left" if self.rerun_icon else "none", 
        command=self.rerun_flagged_job, 
        state=tk.DISABLED
    )
    self.rerun_btn.grid(row=1, column=2, sticky="ew", pady=2)
    
    self.open_result_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('open') if not self.open_icon else ''} Open Result", 
        image=self.open_icon, 
        compound="left" if self.open_icon else "none", 
        command=self.open_result, 
        state=tk.DISABLED
    )
    self.open_result_btn.grid(row=1, column=3, sticky="ew", pady=2)
    
    self.review_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('patterns') if not self.patterns_icon else ''} Patterns", 
        image=self.patterns_icon, 
        compound="left" if self.patterns_icon else "none", 
        command=self.open_pattern_manager
    )
    self.review_btn.grid(row=2, column=0, sticky="ew", pady=2)
    
    self.fullscreen_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('fullscreen') if not self.fullscreen_icon else ''} Fullscreen", 
        image=self.fullscreen_icon, 
        compound="left" if self.fullscreen_icon else "none", 
        command=self.toggle_fullscreen
    )
    self.fullscreen_btn.grid(row=2, column=1, sticky="ew", pady=2)
    
    self.exit_btn = ttk.Button(
        ctrl, 
        text=f" {get_text_icon('exit') if not self.exit_icon else ''} Exit", 
        image=self.exit_icon, 
        compound="left" if self.exit_icon else "none", 
        command=self.on_closing
    )
    self.exit_btn.grid(row=2, column=3, sticky="ew", pady=2)
