import getpass
import os
import shutil
import subprocess

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.properties import ObjectProperty # Cannot find reference 'properties' in '__init__.py'
from kivy.uix.popup import Popup
from kivy.clock import Clock
import threading


# (Import functions from repoharvester.py as needed)
from repoharvester import get_repo_name, clone_repository, get_file_list, write_to_union_file, EXTENSION_GROUPS

def clone_repository_with_password(repo_url, temp_dir):
    # Run git clone command and capture output
    process = subprocess.Popen(['git', 'clone', repo_url, temp_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(f'stdout.decode("utf-8"): {stdout.decode("utf-8")}')
    print(f'stderr.decode("utf-8"): {stderr.decode("utf-8")}')

    # If output contains password prompt
    if b'passphrase' in stderr:
        # Display Kivy popup to get password from user
        password_popup = PasswordPopup(on_submit=clone_repository_with_password, repo_url=repo_url, temp_dir=temp_dir)
        password_popup.open()

        # Wait for user to enter password and close popup
        while password_popup.is_open:
            pass

        # Get password entered by user
        password = password_popup.password_input.text

        # Run git clone command again with password
        process = subprocess.Popen(['git', 'clone', repo_url, temp_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        process.communicate(input=password.encode())
class PasswordPopup(Popup):
    password_input = ObjectProperty()

    def __init__(self, on_submit, **kwargs):
        super().__init__(**kwargs)
        self.on_submit = on_submit
        self.title = "Enter Password"
        self.size_hint = (0.5, 0.3)
        self.auto_dismiss = False

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Password:"))
        self.password_input = TextInput(password=True)
        layout.add_widget(self.password_input)
        submit_button = Button(text="Submit", on_press=self._submit)
        layout.add_widget(submit_button)
        self.content = layout

    def _submit(self, instance):
        password = self.password_input.text
        self.on_submit(password)
        self.dismiss()

class RepoHarvesterApp(App):
    repo_url_input = ObjectProperty()
    progress_bar = ObjectProperty()
    progress_label = ObjectProperty()
    # Add checkboxes for more options
    include_media_check = ObjectProperty()
    include_office_check = ObjectProperty()
    max_size_input = ObjectProperty()
    excluded_folders_input = ObjectProperty()

    def build(self):
        # Main Layout
        main_layout = BoxLayout(orientation='vertical')

        # Input Section
        input_grid = GridLayout(cols=2, padding=10, spacing=5)
        input_grid.add_widget(Label(text="Repo URL:"))
        self.repo_url_input = TextInput()
        input_grid.add_widget(self.repo_url_input)

        # Options Section
        options_grid = GridLayout(cols=2, padding=5, spacing=5)
        self.remove_comments_check = CheckBox(active=False)
        options_grid.add_widget(Label(text="Remove Comments:"))
        options_grid.add_widget(self.remove_comments_check)
        # ... (Add more checkboxes for other options)
        self.include_media_check = CheckBox(active=False)
        options_grid.add_widget(Label(text="Include Media:"))
        options_grid.add_widget(self.include_media_check)

        self.include_office_check = CheckBox(active=False)
        options_grid.add_widget(Label(text="Include Office:"))
        options_grid.add_widget(self.include_office_check)

        options_grid.add_widget(Label(text="Max File Size (KB):"))
        self.max_size_input = TextInput(text="1000")
        options_grid.add_widget(self.max_size_input)

        options_grid.add_widget(Label(text="Excluded Folders (comma-separated):"))
        self.excluded_folders_input = TextInput()
        options_grid.add_widget(self.excluded_folders_input)

        # Add input and options sections to main layout
        main_layout.add_widget(input_grid)
        main_layout.add_widget(options_grid)

        # Action Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        harvest_button = Button(text="Harvest", on_press=self.start_harvest)
        clear_button = Button(text="Clear", on_press=self.clear_inputs)
        button_layout.add_widget(harvest_button)
        button_layout.add_widget(clear_button)

        # Add buttons to main layout
        main_layout.add_widget(button_layout)

        # Progress Section (initially hidden)
        self.progress_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        self.progress_bar = ProgressBar(max=100)
        self.progress_label = Label(text="Status:")
        self.progress_layout.add_widget(self.progress_label)
        self.progress_layout.add_widget(self.progress_bar)

        # Add progress section to main layout (hidden initially)
        self.progress_layout.opacity = 0
        main_layout.add_widget(self.progress_layout)

        return main_layout

    def build_excluded_extensions_set(self):
        excluded_extensions = set()
        for extensions in EXTENSION_GROUPS.values():
            excluded_extensions.update(extensions)
        # ... (Implement logic to add/remove extensions based on user options) ...
        if self.include_media_check.active:
            excluded_extensions -= EXTENSION_GROUPS['media']
        if self.include_office_check.active:
            excluded_extensions -= EXTENSION_GROUPS['office']
        # ...
        return excluded_extensions

    def harvest_repo(self, repo_url, remove_comments, excluded_extensions):
        # 1. Get repo name and create temp directory
        repo_name = get_repo_name(repo_url)
        temp_dir = f'tmp_{repo_name}'

        # 2. Update progress and clone repository
        self.update_progress(10, "Cloning repository...")

        clone_repository_with_password(repo_url, temp_dir)
        # while True:
        #     try:
        #         clone_repository(repo_url, temp_dir)
        #         break  # Successful clone, exit loop
        #     except Exception as e:
        #         print(f"Error: {e}")
        #         password = getpass.getpass(prompt="Enter password: ")
        #         self.repo_url_input.password = password
        # clone_repository(repo_url, temp_dir)


        # 3. Get file list
        self.update_progress(30, "Getting file list...")
        max_size = 1000  # Replace with value from user input
        excluded_folders = []  # Replace with value from user input
        file_list = get_file_list(temp_dir, excluded_extensions, max_size, excluded_folders)

        # 4. Write to union file
        self.update_progress(60, "Writing to file...")
        log_file = "output/union_file.log"  # Replace with value from user input
        union_filename = write_to_union_file(file_list, repo_name, remove_comments, log_file)

        # 5. Update progress and clean up
        self.update_progress(90, "Cleaning up...")
        shutil.rmtree(temp_dir)

        # 6. Display results
        self.update_progress(100, "Done!")
        Clock.schedule_once(lambda dt: self.show_results_popup(union_filename), 1)

    def show_results_popup(self, filename):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f"Output file: {filename}"))
        open_button = Button(text="Open File")
        open_button.bind(on_press=lambda instance: self.open_output_file(filename))
        content.add_widget(open_button)
        content.add_widget(Button(text="Close", on_press=lambda instance: popup.dismiss()))

        popup = Popup(title="Harvesting Complete", content=content, size_hint=(0.5, 0.5), auto_dismiss=False)
        popup.open()

    def open_output_file(self, filename):
        try:
            # (Implement opening the file using the appropriate system command or library)
            # For example, on Linux/macOS:
            os.system(f"xdg-open {filename}")
        except Exception as e:
            self.show_error_popup(f"Error opening file: {e}")

    def show_error_popup(self, message):
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.5, 0.3))
        popup.open()

    def update_progress(self, value, message):
        self.progress_bar.value = value
        self.progress_label.text = message

    def start_harvest(self, instance):
        # 1. Get values from input fields and options
        repo_url = self.repo_url_input.text
        remove_comments = self.remove_comments_check.active
        # ... (get other options)
        if not repo_url:
            self.show_error_popup("Please enter a repository URL.")
            return

        # 2. Show progress layout
        self.progress_layout.opacity = 1

        # 3. Call RepoHarvester functions (using threading or multiprocessing)
        #    (Update progress bar and label as needed)
        # ...
        # Build excluded extensions set
        excluded_extensions = self.build_excluded_extensions_set()

        # Start harvesting in a separate thread
        thread = threading.Thread(target=self.harvest_repo, args=(repo_url, remove_comments, excluded_extensions))
        thread.start()

    def clear_inputs(self, instance):
        self.repo_url_input.text = ""
        self.remove_comments_check.active = False
        # ... (clear other inputs)


if __name__ == "__main__":
    RepoHarvesterApp().run()