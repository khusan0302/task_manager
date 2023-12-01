import json
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import colorchooser
from tkinter import font as tkFont
from tkcalendar import DateEntry
from operator import attrgetter
from datetime import datetime, timedelta
from plyer import notification
import pyttsx3

class Task:
    def __init__(self, title, description, due_date, priority, completed=False):
        self.title = title
        self.description = description
        self.completed = completed
        self.due_date = due_date
        self.priority = priority
        


class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("800x600")  # Set initial window size
        self.root.resizable(width=True, height=True)
        
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150) #Adjust the rate value

        # Make custom_font an instance variable
        self.custom_font = tkFont.Font(family="Helvetica", size=12)

        # Default color theme
        self.theme_colors = {
            "background": "#f2f2f2",
            "button_bg": "#4CAF50",
            "button_fg": "white",
            "label_bg": "#007BFF",
            "label_fg": "white",
            "listbox_bg": "#f2f2f2",
            "status_bar_fg": "black"
        }

        # Initialize tasks attribute
        self.tasks = []

        # Check reminders on startup
        self.check_reminders()

        # Create a frame to hold the main content with a border
        self.main_frame = tk.Frame(self.root, bd=1, relief=tk.GROOVE, bg=self.theme_colors["background"])
        self.main_frame.pack(expand=True, fill="both")

        # Create a status bar for notifications
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=self.custom_font, fg=self.theme_colors["status_bar_fg"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # GUI Elements
        self.setup_task_listbox()
        self.setup_buttons()
        self.setup_entry_fields()

        # Set initial focus
        self.title_entry.focus()

        # Add Task Sorting buttons
        self.sort_buttons_frame = tk.Frame(self.root, bg=self.theme_colors["background"])
        self.sort_buttons_frame.pack()
        self.add_sort_buttons()

        # Add details view button
        self.view_details_button = self.create_button(self.main_frame, "View Details", self.view_task_details)
        self.view_details_button.pack(pady=10)

        # Add search entry
        self.search_entry = tk.Entry(self.main_frame, width=50, font=self.custom_font)
        self.search_entry.pack(pady=10)
        self.search_button = self.create_button(self.main_frame, "Search", self.search_tasks)
        self.search_button.pack()

        # Load tasks
        self.load_tasks()

        # Add Settings button
        self.settings_button = self.create_button(self.main_frame, "Settings", self.open_settings)
        self.settings_button.pack(pady=10)

    def setup_task_listbox(self):
        # Task Listbox with a different background color and font
        self.task_listbox = tk.Listbox(self.main_frame, selectmode=tk.SINGLE, width=80, height=15, bg=self.theme_colors["listbox_bg"], font=self.custom_font)
        self.task_listbox.pack(pady=10, padx=10)
        self.task_listbox.bind("<<ListboxSelect>>", self.on_task_select)
    
    def view_task_details(self):
        selected_index = self.task_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            task = self.tasks[index]

            # Create a new window for task details
            details_window = tk.Toplevel(self.root)
            details_window.title("Task Details")

            # Display task details
            details_text = f"Title: {task.title}\n\n"
            details_text += f"Description:\n{task.description}\n\n"
            details_text += f"Due Date: {task.due_date if task.due_date else 'N/A'}\n"
            details_text += f"Priority: {task.priority}\n"
            details_text += f"Status: {'Done' if task.completed else 'Not Done'}"

            details_label = tk.Label(details_window, text=details_text, font=self.custom_font)
            details_label.pack(padx=20, pady=20)

            # Use threading for asynchronous TTS
            t = threading.Thread(target=self.read_task_aloud, args=(task,))
            t.start()    
        
    def read_task_aloud(self, task):
        details_text = f"Title: {task.title}\n\n"
        details_text += f"Description:\n{task.description}\n\n"
        details_text += f"Due Date: {task.due_date if task.due_date else 'N/A'}\n"
        details_text += f"Priority: {task.priority}\n"
        details_text += f"Status: {'Done' if task.completed else 'Not Done'}"

        self.engine.say(details_text)
        self.engine.runAndWait()
    
    
    def speak_notification(self, message):
        self.engine.say(message)
        self.engine.runAndWait()    

    def setup_buttons(self):
        button_frame = tk.Frame(self.main_frame, bg=self.theme_colors["background"])
        button_frame.pack()

        # Styled buttons with consistent colors
        self.add_button = self.create_button(button_frame, "Add Task", self.add_task)
        self.complete_button = self.create_button(button_frame, "Mark as Complete", self.complete_task)
        self.delete_button = self.create_button(button_frame, "Delete Task", self.delete_task)

        self.add_button.grid(row=0, column=0, padx=5)
        self.complete_button.grid(row=0, column=1, padx=5)
        self.delete_button.grid(row=0, column=2, padx=5)

    def create_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"], padx=10, pady=5, font=self.custom_font)

    def setup_entry_fields(self):
        entry_frame = tk.Frame(self.main_frame, bg=self.theme_colors["background"])
        entry_frame.pack()

        labels = ["Title", "Description", "Due Date", "Priority (1-5)"]
        entries = [tk.Entry, tk.Text, DateEntry]

        for i, (label, entry_type) in enumerate(zip(labels, entries)):
            label_widget = self.create_label(entry_frame, f"{label}:", row=i, column=0, sticky="e")
            label_widget.grid(row=i, column=0, padx=(10, 5), pady=5)

            if entry_type == tk.Entry:
                entry_widget = entry_type(entry_frame, width=80, font=self.custom_font)
                entry_widget.grid(row=i, column=1, padx=(0, 10), pady=5)
                setattr(self, f"{label.lower().replace(' ', '_')}_entry", entry_widget)
            elif entry_type == tk.Text:
                entry_widget = entry_type(entry_frame, width=80, height=4, font=self.custom_font)
                entry_widget.grid(row=i, column=1, padx=(0, 10), pady=5)
                setattr(self, f"{label.lower().replace(' ', '_')}_entry", entry_widget)
            elif entry_type == DateEntry:
                entry_widget = entry_type(entry_frame, font=self.custom_font)
                entry_widget.grid(row=i, column=1, padx=(0, 10), pady=5)
                setattr(self, f"{label.lower().replace(' ', '_')}_entry", entry_widget)

        # Priority Scale with values from 1 to 5
        priority_label = self.create_label(entry_frame, "Priority (1-5):", row=len(labels), column=0, sticky="e")
        priority_label.grid(row=len(labels), column=0, padx=(10, 5), pady=5)

        self.priority_scale = tk.Scale(entry_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=200, font=self.custom_font)
        self.priority_scale.grid(row=len(labels), column=1, padx=(0, 10), pady=5)

    def create_label(self, parent, text, row, column, sticky):
        return tk.Label(parent, text=text, padx=10, pady=5, bg=self.theme_colors["label_bg"], fg=self.theme_colors["label_fg"], anchor=sticky, font=self.custom_font)

    def add_sort_buttons(self):
        sort_buttons = [
            ("Sort by Due Date", lambda: self.sort_tasks("due_date")),
            ("Sort by Priority", lambda: self.sort_tasks("priority")),
            ("Sort by Completion", lambda: self.sort_tasks("completed"))
        ]

        for i, (text, command) in enumerate(sort_buttons):
            sort_button = self.create_button(self.sort_buttons_frame, text, command)
            sort_button.grid(row=0, column=i, padx=5)

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        settings_frame = tk.Frame(settings_window, bg=self.theme_colors["background"])
        settings_frame.pack(expand=True, fill="both")

        # Add a button to change background color
        bg_color_button = self.create_button(settings_frame, "Change Background Color", self.change_bg_color)
        bg_color_button.pack(pady=10)

        # Add a button to reset to default colors
        reset_button = self.create_button(settings_frame, "Reset to Default Colors", self.reset_colors)
        reset_button.pack(pady=10)

    def change_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")[1]
        if color:
            self.theme_colors["background"] = color
            self.root.config(bg=color)
            self.main_frame.config(bg=color)
            self.sort_buttons_frame.config(bg=color)
            self.load_tasks()

    def reset_colors(self):
        # Reset to default colors
        self.theme_colors = {
            "background": "#f2f2f2",
            "button_bg": "#4CAF50",
            "button_fg": "white",
            "label_bg": "#007BFF",
            "label_fg": "white",
            "listbox_bg": "#f2f2f2",
            "status_bar_fg": "black"
        }
        self.root.config(bg=self.theme_colors["background"])
        self.main_frame.config(bg=self.theme_colors["background"])
        self.sort_buttons_frame.config(bg=self.theme_colors["background"])
        self.load_tasks()

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as file:
                tasks_data = json.load(file)
                self.tasks = [Task(**task_data) for task_data in tasks_data]
        except FileNotFoundError:
            self.tasks = []

        self.all_tasks = self.tasks.copy()  # Initialize all_tasks
        self.update_task_listbox(self.all_tasks)
        self.update_task_listbox(self.all_tasks)


    def save_tasks(self):
        tasks_data = [{"title": task.title, "description": task.description, "completed": task.completed,
                       "due_date": task.due_date, "priority": task.priority} for task in self.tasks]
        with open("tasks.json", "w") as file:
            json.dump(tasks_data, file)

    def add_task(self):
        title = self.title_entry.get()
        description = self.description_entry.get("1.0", tk.END).strip()
        try:
            due_date_str = self.due_date_entry.get()
            due_date = datetime.strptime(due_date_str, "%m/%d/%y").strftime("%Y-%m-%d")
        except ValueError:
            self.show_status("Invalid due date. Please enter a valid date.")
            return
        priority = self.priority_scale.get()

        if title:
            task = Task(title, description, due_date, priority)
            self.tasks.append(task)
            self.all_tasks.append(task)
            self.clear_entry_fields()
            self.update_task_listbox(self.all_tasks)
            self.save_tasks()
            self.show_status(f'Task "{title}" added successfully.', success=True)

            # Notify the user with voice
            self.speak_notification(f'Task "{title}" added successfully.')


    def complete_task(self):
        selected_index = self.task_listbox.curselection()
        print("Selected Index (Complete Task):", selected_index)  # Add this line for debugging
        if selected_index:
            index = selected_index[0]
            print("Index (Complete Task):", index)  # Add this line for debugging
            self.tasks[index].completed = True
            self.update_task_listbox(self.all_tasks)
            self.save_tasks()
            self.show_status("Task marked as complete.", success=True)

    def delete_task(self):
        selected_index = self.task_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            task_title = self.tasks[index].title
            confirmation = messagebox.askyesno("Delete Task", f"Are you sure you want to delete the task: {task_title}?")
            if confirmation:
                del self.tasks[index]
                self.all_tasks = self.tasks.copy()
                self.update_task_listbox(self.all_tasks)
                self.save_tasks()
                self.show_status(f'Task "{task_title}" deleted successfully.', success=True)

                # Notify the user with voice
                self.speak_notification(f'Task "{task_title}" deleted successfully.')



    def clear_entry_fields(self):
        for entry_widget in [self.title_entry, self.description_entry, self.due_date_entry]:
            entry_widget.delete(0, tk.END) if isinstance(entry_widget, tk.Entry) else entry_widget.delete("1.0", tk.END)
        self.priority_scale.set(1)

    def update_task_listbox(self, tasks):
        self.task_listbox.delete(0, tk.END)
        for i, task in enumerate(tasks):
            status = "Done" if task.completed else "Not Done"
            due_date_str = task.due_date if task.due_date else "N/A"

            task_text = f"{i+1}. {task.title} ({status}) - Due Date: {due_date_str}, Priority: {task.priority}"

            # Use tags for different formatting
            self.task_listbox.insert(tk.END, task_text)
            if task.completed:
                self.task_listbox.itemconfig(i, {'fg': 'gray'})
            else:
                self.task_listbox.itemconfig(i, {'fg': 'black'})

        # Check for reminders after updating
        self.check_reminders()





        
    def check_reminders(self):
        for task in self.tasks:
            if not task.completed and task.due_date:
                due_date = datetime.strptime(task.due_date, "%Y-%m-%d")
                current_date = datetime.now()
                time_difference = due_date - current_date

                # Check if the task is overdue or due within 24 hours
                if time_difference <= timedelta(days=1) and time_difference >= timedelta():
                    self.show_notification(f"Task Reminder: {task.title}", f"Due in {time_difference}")
    
    def show_notification(self, title, message):
        # Display a desktop notification
        notification.notify(
            title=title,
            message=message,
            app_name="Task Manager",
        )
        
                            
    def on_task_select(self, event):
        # Clear any existing task details label
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.winfo_name() == "task_details_label":
                widget.destroy()

        selected_index = self.task_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            task = self.tasks[index]

            # Additional code to prevent showing description when just clicking
            task_details_text = f"Title: {task.title}\n\n"
            task_details_text += f"Due Date: {task.due_date if task.due_date else 'N/A'}\n"
            task_details_text += f"Priority: {task.priority}\n"
            task_details_text += f"Status: {'Done' if task.completed else 'Not Done'}"

            # Create a label to display task details
            task_details_label = tk.Label(self.root, text=task_details_text, font=self.custom_font, name="task_details_label")
            task_details_label.pack(side=tk.TOP, pady=10)


    def sort_tasks(self, criterion):
        if criterion == "completed":
            self.tasks.sort(key=attrgetter(criterion))
        else:
            self.tasks.sort(key=attrgetter(criterion), reverse=True)
        self.update_task_listbox(self.tasks)  # Pass the sorted tasks to update_task_listbox


    def show_status(self, message, success=False):
        if success:
            self.status_bar.config(fg="green")
        else:
            self.status_bar.config(fg="red")
        self.status_var.set(message)
        self.root.after(3000, self.clear_status)

    def clear_status(self):
        self.status_var.set("")
        self.status_bar.config(fg=self.theme_colors["status_bar_fg"])

    def search_tasks(self):
        query = self.search_entry.get().lower()
        if query:
            matching_tasks = [task for task in self.all_tasks if query in task.title.lower() or query in task.description.lower()]
            self.update_task_listbox(matching_tasks)
            self.show_status(f"Found {len(matching_tasks)} matching task(s).", success=True)
        else:
            self.update_task_listbox(self.all_tasks)
            self.show_status("Search query empty. Showing all tasks.", success=True)


    def view_task_details(self):
        selected_index = self.task_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            task = self.tasks[index]

            # Create a new window for task details
            details_window = tk.Toplevel(self.root)
            details_window.title("Task Details")

            # Display task details
            details_text = f"Title: {task.title}\n\n"
            details_text += f"Description:\n{task.description}\n\n"
            details_text += f"Due Date: {task.due_date if task.due_date else 'N/A'}\n"
            details_text += f"Priority: {task.priority}\n"
            details_text += f"Status: {'Done' if task.completed else 'Not Done'}"

            details_label = tk.Label(details_window, text=details_text, font=self.custom_font)
            details_label.pack(padx=20, pady=20)

            # Read task details aloud
            self.read_task_aloud(task)

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerApp(root)
    root.mainloop()
