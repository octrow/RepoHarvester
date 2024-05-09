import customtkinter as ctk
from tkinter import filedialog  # For file dialog
import threading

from repoharvester import RepoHarvester


class RepoHarvesterGUI:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.geometry("700x500")
        self.app.title("RepoHarvester")

        # Configure theme and appearance (optional)
        ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

        self.create_widgets()
        self.app.mainloop()

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(master=self.app, corner_radius=10)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Section frames
        input_frame = ctk.CTkFrame(master=main_frame)
        options_frame = ctk.CTkFrame(master=main_frame)
        output_frame = ctk.CTkFrame(master=main_frame)
        action_frame = ctk.CTkFrame(master=main_frame)
        status_frame = ctk.CTkFrame(master=main_frame)

        input_frame.pack(pady=10, padx=10, fill="x")
        options_frame.pack(pady=10, padx=10, fill="x")
        output_frame.pack(pady=10, padx=10, fill="x")
        action_frame.pack(pady=10, padx=10, fill="x")
        status_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Input Section ---
        repo_url_label = ctk.CTkLabel(master=input_frame, text="Repository URL (SSH):")
        repo_url_label.pack(side="left", padx=5)
        self.repo_url_entry = ctk.CTkEntry(master=input_frame, width=400)
        self.repo_url_entry.pack(side="left", padx=5)

        # --- Options Section ---
        # Remove comments checkbox
        self.remove_comments_var = ctk.BooleanVar(value=False)
        remove_comments_checkbox = ctk.CTkCheckBox(master=options_frame, text="Remove Comments",
                                                   variable=self.remove_comments_var)
        remove_comments_checkbox.pack(side="left", padx=5)

        # Placeholder for file type inclusion/exclusion options
        file_type_label = ctk.CTkLabel(master=options_frame, text="File Types:")
        file_type_label.pack(side="left", padx=5)

        # Max file size input
        max_size_label = ctk.CTkLabel(master=options_frame, text="Max File Size (KB):")
        max_size_label.pack(side="left", padx=5)
        self.max_size_entry = ctk.CTkEntry(master=options_frame, width=100)
        self.max_size_entry.pack(side="left", padx=5)

        # Exclude folders input
        exclude_folders_label = ctk.CTkLabel(master=options_frame, text="Exclude Folders:")
        exclude_folders_label.pack(side="left", padx=5)
        self.exclude_folders_entry = ctk.CTkEntry(master=options_frame, width=200)
        self.exclude_folders_entry.pack(side="left", padx=5)

        # File type inclusion/exclusion
        file_type_frame = ctk.CTkFrame(master=options_frame)
        file_type_frame.pack(side="left", padx=5)

        self.file_type_vars = {}  # Dictionary to store checkbox variables
        for group_name, extensions in EXTENSION_GROUPS.items():
            var = ctk.BooleanVar(value=True)  # Default: include all groups
            self.file_type_vars[group_name] = var
            checkbox = ctk.CTkCheckBox(master=file_type_frame, text=group_name.title(),
                                       variable=var, onvalue=True, offvalue=False)
            checkbox.pack(side="top", anchor="w")

        # Optional: Input field for custom extensions
        custom_ext_label = ctk.CTkLabel(master=options_frame, text="Custom Extensions (comma-separated):")
        custom_ext_label.pack(side="left", padx=5)
        self.custom_ext_entry = ctk.CTkEntry(master=options_frame, width=200)
        self.custom_ext_entry.pack(side="left", padx=5)

        # --- Output Section ---
        log_file_label = ctk.CTkLabel(master=output_frame, text="Log File Path:")
        log_file_label.pack(side="left", padx=5)
        self.log_file_entry = ctk.CTkEntry(master=output_frame, width=350)
        self.log_file_entry.pack(side="left", padx=5)
        log_file_button = ctk.CTkButton(master=output_frame, text="Browse", command=self.browse_log_file)
        log_file_button.pack(side="left", padx=5)

        # --- Action Buttons ---
        self.start_button = ctk.CTkButton(master=action_frame, text="Start", command=self.start_process)
        self.start_button.pack(side="left", padx=5)
        clear_button = ctk.CTkButton(master=action_frame, text="Clear", command=self.clear_inputs)
        clear_button.pack(side="left", padx=5)

        # --- Status/Output Display ---
        self.status_text = ctk.CTkTextbox(master=status_frame)
        self.status_text.pack(fill="both", expand=True)

    # Placeholder functions for button actions
    def browse_log_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("All Files", "*.*")]
        )
        if filepath:
            self.log_file_entry.delete(0, "end")
            self.log_file_entry.insert(0, filepath)

    def start_process(self):
        repo_url = self.repo_url_entry.get()
        remove_comments = self.remove_comments_var.get()
        max_size = self.max_size_entry.get()
        exclude_folders = self.exclude_folders_entry.get().replace(" ", "").split(",")
        # ... (Other processing logic)
        harvester = RepoHarvester()

        # Get included/excluded file types
        excluded_extensions = set()
        for group_name, var in self.file_type_vars.items():
            if not var.get():  # If checkbox is unchecked
                excluded_extensions.update(harvester.EXTENSION_GROUPS[group_name])

        # Get custom extensions (if entered)
        custom_exts = self.custom_ext_entry.get().replace(" ", "").split(",")
        excluded_extensions.update(custom_exts)

        # ... (Pass excluded_extensions to the repo harvester logic)

        # Disable start button during processing
        self.start_button.configure(state="disabled") # Unresolved attribute reference 'start_button' for class 'RepoHarvesterGUI'

        # Create and start a thread for the harvesting process
        thread = threading.Thread(target=self.harvesting_thread, args=(repo_url, remove_comments,
                                                                       excluded_extensions, max_size,
                                                                       exclude_folders, harvester))
        thread.start()

    def harvesting_thread(self, repo_url, remove_comments, excluded_extensions, max_size, exclude_folders, harvester):
        try:
            harvester.run_from_gui(repo_url, remove_comments, excluded_extensions, max_size, exclude_folders)
            self.status_text.insert("end", "Harvesting completed successfully!\n")
        except Exception as e:
            self.status_text.insert("end", f"An error occurred: {e}\n")
        finally:
            self.start_button.configure(state="normal")  # Unresolved attribute reference 'start_button' for class 'RepoHarvesterGUI'

    def clear_inputs(self):
        # Implement input clearing logic here
        pass


if __name__ == "__main__":
    RepoHarvesterGUI()