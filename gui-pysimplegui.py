import PySimpleGUI as sg
import subprocess
import os

from repoharvester import EXTENSION_GROUPS

# Define layout elements
input_layout = [
    [sg.Text("GitHub Repository URL (SSH)")],
    [sg.InputText(key="-REPO_URL-"), sg.Button("Browse", key="-BROWSE-")],
]

options_layout = [
    [sg.Checkbox("Remove Comments", key="-REMOVE_COMMENTS-")],
    [sg.Frame("Include File Types", layout=[[sg.Checkbox(group, key=f"-SKIP_{group}-")] for group in EXTENSION_GROUPS])],
    [sg.Text("Maximum File Size (KB)"), sg.InputText(key="-MAX_SIZE-", default_text="1000")],
    [sg.Text("Exclude Folders (comma-separated)"), sg.InputText(key="-EXCLUDE_FOLDERS-")],
    [sg.Text("Log File Path"), sg.InputText(key="-LOG_PATH-", default_text="output/union_file.log"), sg.FileBrowse()],
]

action_layout = [
    [sg.Button("Start Harvesting"), sg.Button("Cancel")],
]

output_layout = [
    [sg.Output(size=(80, 20), key="-OUTPUT-")],
]

# Create the main layout
layout = [
    [sg.Column(input_layout)],
    [sg.Column(options_layout)],
    [sg.Column(action_layout)],
    [sg.Column(output_layout)],
]

# Create the window
window = sg.Window("RepoHarvester GUI", layout)

# Event loop
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Cancel":
        break

    elif event == "-BROWSE-":
        # Open file browser and update input
        folder_path = sg.popup_get_folder("Select Repository Folder")
        if folder_path:
            window["-REPO_URL-"].update(folder_path)

    elif event == "Start Harvesting":
        # Get values from input elements
        repo_url = values["-REPO_URL-"]
        remove_comments = values["-REMOVE_COMMENTS-"]
        skip_types = [group for group, checked in values.items() if group.startswith("-SKIP_") and not checked]
        max_size = values["-MAX_SIZE-"]
        exclude_folders = values["-EXCLUDE_FOLDERS-"]
        log_path = values["-LOG_PATH-"]

        # Construct command arguments
        args = ["python", "repoharvester.py", repo_url]
        if remove_comments:
            args.append("--remove")
        for group in skip_types:
            args.extend(["--no-skip", group.replace("-SKIP_", "")])
        args.extend(["--max-size", max_size])
        if exclude_folders:
            args.extend(["--exclude"] + exclude_folders.split(","))
        args.extend(["--log", log_path])

        # Disable input elements
        for key in values:
            window[key].update(disabled=True)

        # Run the process and update output
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip(), end="\n")
                    window["-OUTPUT-"].update(value=window["-OUTPUT-"].get() + output)
            # window["-OUTPUT-"].update(value=window["-OUTPUT-"].get() + f"\nAll files have been written to {os.path.join('output', f'{os.path.basename(repo_url).replace('.git', '')}_all_files.txt')}")
            # 1. Get the current output content
            current_output = window["-OUTPUT-"].get()

            # 2. Construct the output file path
            repo_name = os.path.basename(repo_url).replace(".git", "")
            output_file_path = os.path.join("output", f"{repo_name}_all_files.txt")

            # 3. Create the new message
            new_message = f"\nAll files have been written to {output_file_path}"

            # 4. Update the output element
            window["-OUTPUT-"].update(value=current_output + new_message)
        except Exception as e:
            print(f"Error: {e}")
            window["-OUTPUT-"].update(value=window["-OUTPUT-"].get() + f"\nError: {e}")
        finally:
            # Enable input elements
            for key in values:
                window[key].update(disabled=False)

window.close()