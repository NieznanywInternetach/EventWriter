import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk, filedialog
from psycopg2 import connect
from string import punctuation, digits, whitespace

"""
######################################
todo: refactor names -> <class_name>_<type_name>_<info_if_needed>
for indexes and data dicts
tkinter -> implement dnd
bugs:

######################################
"""


class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        """
        For app general settings
        
        Widgets - add as class' property if (visible all the time or root widget) else add to widget_cache
        unless it's a pop-up window, then it can be destroyed after usage
        
        Naming convention of variables/keys for the cache:
        first word - arbitrary name of the thing, category/mode etc
        second word - class/type (usually based on TK)
        third - name of the instance if needed
        """
        super().__init__(*args, **kwargs)
        # General settings
        self.title("EventWriter - Dev")
        self.wm_minsize(width=400, height=400)
        self.option_add('*tearOff', False)
        self.app_root = self  # more meaningful name
        self.widgets_cache: dict = {}  # the main "storage" of the app
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # events
        self.field_button_refs = {}  # actually more cache than the widgets_cache
        # database
        self.db_cursor = None
        self.db_connector = None
        self.db_event_id_current = -1
        self.db_set_tags = set()  # setter: db_filter()/return_tags()
        self.db_event_data = {}
        # database-related info strings
        self.info_string_tags = "Use space to separate tags\nUse underscore to add multi-word tag"
        self.success_string_tags = "\nTags added successfully"
        self.warning_string_tags = "\nSome of your tags exist in the database!\n{}\nIt was already handled though."
        self.error_string_tags = "\nAll your tags already exist in the database!\nAdding canceled."
        # SQL (Postgres) strings
        self.db_string_search = "SELECT titles, desc_texts, dict_data, stats_data, embed_texts, options, panel_name, event_codes, tags FROM event_table WHERE id_event=%s"
        self.db_string_save = "INSERT INTO event_table (titles, desc_texts, dict_data, stats_data, embed_texts, options, panel_name, event_codes, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.db_string_get_events = "SELECT panel_name, id_event FROM event_table"
        self.db_string_get_tags = "SELECT tag FROM tags_list"
        self.db_string_add_tags = "INSERT INTO tags_list (tag) VALUES "  # should be used as base for proper SQL request
        self.db_string_delete_tags = "DELETE FROM tags_list WHERE tag IN "  # As above
        
        # initialization of menus
        self.main_menu = tk.Menu(self.app_root)
        # instead of playing with "root['menu'] = main_menu"
        self.app_root.config(menu=self.main_menu)
        # menu's items are added using these (modes)
        self.modes_menu = tk.Menu(self.main_menu)
        self.event_menu = tk.Menu(self.main_menu)
        self.help_menu = tk.Menu(self.main_menu)
        # Adding the (modes) to the main menu
        self.main_menu.add_cascade(menu=self.modes_menu, label="Modes")
        self.main_menu.add_cascade(menu=self.event_menu, label="Event")
        self.main_menu.add_cascade(menu=self.help_menu, label="Help")
        # adding items to the modes
        self.modes_menu.add_command(label="Event Mode", command=lambda: self.switch_mode(1))
        self.modes_menu.add_command(label="Database Mode", command=lambda: self.switch_mode(2))

        self.event_menu.add_command(label="New")
        self.event_menu.add_command(label="Open...")
        self.event_menu.add_command(label="Save")
        self.event_menu.add_command(label="Save As...")

        self.help_menu.add_command(label="Quick Guide", command=self.start_help_mode)
        
        # initialization of base frames
        # Just a small thing
        self.init_frame = ttk.Frame(self.app_root, width=400, height=400)
        self.init_frame.grid()
        init_label = ttk.Label(self.init_frame, text="Select Modes to begin.")
        init_label.grid(padx=100, pady=100)

        # mode id -> event - 1, database - 2
        self.event_frame = ttk.Frame(self.app_root, padding=3)
        self.database_frame = ttk.Frame(self.app_root, padding=3)
        self.help_frame = ttk.Frame(self.app_root, padding=3)  # maybe, maybe not
        self.widgets_cache["previous_frame_id"] = 0
    """
    def load_recently(self):
        data = "get data from the localisation"
        self.loaded_recently = data
        # and stuff
    
    def autosave(self):
        # save data to the localisation
        pass
    """
    # the basis for GUI
    def switch_mode(self, mode_id):
        if self.widgets_cache["previous_frame_id"] == 0:
            self.init_frame.destroy()
            del self.init_frame
        elif self.widgets_cache["previous_frame_id"] == 1:
            # TODO save changes in the widgets' values
            self.event_frame.grid_forget()
        elif self.widgets_cache["previous_frame_id"] == 2:
            self.database_frame.grid_forget()
        elif self.widgets_cache["previous_frame_id"] == -1:
            print("EvenWriter started")
        else:
            print("Error switch_mode: previous_frame_id {} todo".format(self.widgets_cache["previous_frame_id"]))
        if mode_id == 1:
            self.start_event_mode()
            self.widgets_cache["previous_frame_id"] = 1
        elif mode_id == 2:
            self.start_database_mode()
            self.widgets_cache["previous_frame_id"] = 2
        else:
            print(f"Error switch_mode: mode_id {mode_id} todo")

    # Functions for buttons
    def start_event_mode(self):
        self.event_frame.grid(column=0, row=0, sticky=tk.NSEW)
        # todo test later if ... in widgets_cache -> return, as it's just removes event frame from grid
        self.event_frame.rowconfigure(0, weight=1)
        self.event_frame.columnconfigure(0, weight=1)
        # arbitrary key, little need for checking the second element
        if "event_event_notebook" not in self.widgets_cache.keys():
            event_event_notebook = EventNotebook(self.event_frame)
            event_frame_buttons = ttk.Frame(self.event_frame)
            event_event_notebook.add_tab("test1")
            event_event_notebook.add_tab("test2")
            event_event_notebook.switch_event_button(0)
            self.widgets_cache["event_event_notebook"] = event_event_notebook
            self.widgets_cache["event_frame_buttons"] = event_frame_buttons
        else:
            event_event_notebook = self.widgets_cache["event_event_notebook"]
            event_frame_buttons = self.widgets_cache["event_frame_buttons"]

        event_event_notebook.grid(column=0, row=0, sticky=tk.N)
        event_frame_buttons.grid(column=1, row=0, padx=5)
        
        if "event_button_add" not in self.widgets_cache.keys():
            event_button_add = ttk.Button(event_frame_buttons, text="Add...", command=self.add_event_elements)
            event_button_delete = ttk.Button(event_frame_buttons, text="Delete", command=self.delete_event_elements)
            event_button_edit = ttk.Button(event_frame_buttons, text="Edit")
            event_button_save = ttk.Button(event_frame_buttons, text="Save")
            event_button_verify = ttk.Button(event_frame_buttons, text="Verify")
            event_button_back = ttk.Button(event_frame_buttons, text="Back")
            
            self.widgets_cache["event_button_add"] = event_button_add
            self.widgets_cache["event_button_delete"] = event_button_delete
            self.widgets_cache["event_button_edit"] = event_button_edit
            self.widgets_cache["event_button_save"] = event_button_save
            self.widgets_cache["event_button_verify"] = event_button_verify
            self.widgets_cache["event_button_back"] = event_button_back
        else:
            event_button_add = self.widgets_cache["event_button_add"]
            event_button_delete = self.widgets_cache["event_button_delete"]
            event_button_edit = self.widgets_cache["event_button_edit"]
            event_button_save = self.widgets_cache["event_button_save"]
            event_button_verify = self.widgets_cache["event_button_verify"]
            event_button_back = self.widgets_cache["event_button_back"]

        event_button_add.grid(row=1, pady=(0, 10))
        event_button_delete.grid(row=2)
        event_button_edit.grid(row=3)
        event_button_save.grid(row=4)
        event_button_verify.grid(row=5, pady=(0, 10))
        event_button_back.grid(row=6)
        
    def start_database_mode(self):
        """
        Naming convention: Variables etc use db instead of database
        """
        self.database_frame.grid(sticky=tk.NSEW)
        # todo test later if ... in widgets_cache -> return, as it's just removes database frame from grid
        if "db_frame_preview" not in self.widgets_cache.keys():
            db_frame_prev = ttk.Frame(self.database_frame, width=100)
            db_frame_preview = ttk.Frame(self.database_frame)
            db_frame_next = ttk.Frame(self.database_frame, width=100)
            db_frame_buttons = ttk.Frame(self.database_frame)
            
            self.widgets_cache["db_frame_prev"] = db_frame_prev
            self.widgets_cache["db_frame_preview"] = db_frame_preview
            self.widgets_cache["db_frame_next"] = db_frame_next
            self.widgets_cache["db_frame_buttons"] = db_frame_buttons
        else:
            db_frame_prev = self.widgets_cache["db_frame_prev"]
            db_frame_preview = self.widgets_cache["db_frame_preview"]
            db_frame_next = self.widgets_cache["db_frame_next"]
            db_frame_buttons = self.widgets_cache["db_frame_buttons"]
        
        db_frame_prev.grid(column=0, sticky=tk.NS)
        db_frame_preview.grid(column=1, sticky=tk.NSEW)
        db_frame_next.grid(column=2, sticky=tk.NS)
        db_frame_buttons.grid(column=3, sticky=tk.NS)
        
        if "db_button_reconnect" not in self.widgets_cache.keys():
            db_button_reconnect = ttk.Button(db_frame_buttons, text="Connect...", command=self.connect_db)
            db_button_filter = ttk.Button(db_frame_buttons, text="Filter Tags...", command=self.filter_db)
            db_button_add_tags = ttk.Button(db_frame_buttons, text="Add Tags...", command=self.add_tags_db)
            db_button_delete_tags = ttk.Button(db_frame_buttons, text="Delete Tags...", command=self.delete_tags_db)
            db_button_edit = ttk.Button(db_frame_buttons, text="Edit Event")
            
            self.widgets_cache["db_button_reconnect"] = db_button_reconnect
            self.widgets_cache["db_button_filter"] = db_button_filter
            self.widgets_cache["db_button_add_tags"] = db_button_add_tags
            self.widgets_cache["db_button_delete_tags"] = db_button_delete_tags
            self.widgets_cache["db_button_edit"] = db_button_edit
        else:
            db_button_reconnect = self.widgets_cache["db_button_reconnect"]
            db_button_filter = self.widgets_cache["db_button_filter"]
            db_button_add_tags = self.widgets_cache["db_button_add_tags"]
            db_button_delete_tags = self.widgets_cache["db_button_delete_tags"]
            db_button_edit = self.widgets_cache["db_button_edit"]
        
        db_button_reconnect.grid(row=0)
        db_button_filter.grid(row=1)
        db_button_filter["state"] = tk.DISABLED
        db_button_add_tags.grid(row=2)
        db_button_add_tags["state"] = tk.DISABLED
        db_button_delete_tags.grid(row=3)
        db_button_delete_tags["state"] = tk.DISABLED
        db_button_edit.grid(row=4)
    
    def start_help_mode(self):
        self.help_frame.grid(sticky=tk.NSEW)
        pass
    
    # event mode funcs
    def add_event_elements(self):  # TODO make mandatory to add a title first etc
        def update_and_add_field(idx):
            nonlocal current_event_base
            current_event_base = self.widgets_cache["event_event_notebook"].get_active_tab()
            current_event_base.add_field(idx)
            # blocking not proper field settings
            fields_list = [len(x) for x in current_event_base.data_dict.values()]
            root.disable_buttons(fields_list)
            # todo replace root...._buttons, buttons should listen to data_dict

        def add_buttons():
            nonlocal tab_flag
            if tab_flag:
                tab_flag = False
                add_xor_close()
                return
            else:
                tab_flag = True
            info_label.grid(row=1)
            name_entry.grid(row=2)
            confirm_button.grid(row=3)
        
        def unlock():
            name = name_svar.get()
            if name:
                confirm_button["state"] = tk.NORMAL
            else:
                confirm_button["state"] = tk.DISABLED
        
        def add_xor_close():
            nonlocal tab_flag
            if tab_flag:
                self.widgets_cache["event_event_notebook"].add_tab(name_svar.get())
                name_svar.set("")
            info_label.grid_remove()
            name_entry.grid_remove()
            confirm_button.grid_remove()
            tab_flag = False
            
        def exit_and_clear():
            self.field_button_refs.clear()
            new_toplevel.destroy()

        tab_flag = False  # to check if the add tab submenu is open or not
        err_string = ""
        try:
            current_event_base = self.widgets_cache["event_event_notebook"].get_active_tab()
        except KeyError as e:
            print(f"ERROR - getting active tab: {e}")
            err_string = "You must have at least one opened event!"
            
        new_toplevel = tk.Toplevel()
        new_toplevel.title(string="Add event fields")
        new_toplevel.resizable(False, False)
        new_toplevel.bind("<Destroy>", lambda event: exit_and_clear())
        main_frame = ttk.Frame(new_toplevel, width=300, height=300)
        main_frame.grid()
        if err_string:
            err_label = ttk.Label(main_frame, text=err_string)
            err_label.place(relheight=0.5, x=40, y=50)
            return
        tab_button = ttk.Button(main_frame, text="Add an event", width=20, command=add_buttons)
        tab_button.grid(row=0, sticky=tk.EW)

        info_label = ttk.Label(main_frame, text="Name your event:")
        
        name_svar = tk.StringVar()
        name_svar.trace_add("write", lambda name, idx_, mode: unlock())
        name_entry = ttk.Entry(main_frame, textvariable=name_svar)
        confirm_button = ttk.Button(main_frame, text="Add the event", command=add_xor_close)
        confirm_button["state"] = tk.DISABLED
        
        title_button = ttk.Button(main_frame, text="Add title", command=lambda: update_and_add_field(0))
        title_button.grid(row=4, sticky=tk.EW)
        separator_button = ttk.Button(main_frame, text="Add separator", command=lambda: update_and_add_field(1))
        separator_button.grid(row=5, sticky=tk.EW)
        description_button = ttk.Button(main_frame, text="Add description", command=lambda: update_and_add_field(2))
        description_button.grid(row=6, sticky=tk.EW)
        embed_button_simple = ttk.Button(main_frame, text="Add simple field", command=lambda: update_and_add_field(3))
        embed_button_simple.grid(row=7, sticky=tk.EW)
        embed_button_stats = ttk.Button(main_frame, text="Add stats field", command=lambda: update_and_add_field(4))
        embed_button_stats.grid(row=8, sticky=tk.EW)
        embed_button_text = ttk.Button(main_frame, text="Add text field", command=lambda: update_and_add_field(5))
        embed_button_text.grid(row=9, sticky=tk.EW)
        
        # todo independence from current event frame (bind destroy)
        self.field_button_refs["title"] = title_button
        self.field_button_refs["separator"] = separator_button
        self.field_button_refs["desc"] = description_button
        
    def delete_event_elements(self):
        """deletes all selected fields from active EventBase"""
        self.widgets_cache["event_event_notebook"].data[self.widgets_cache["event_event_notebook"].index()].delete_field()
    
    # database mode funcs
    def connect_db(self):
        file_path = filedialog.askopenfilename(filetypes=[('Special key', '*.key')])
        with open(file_path, 'r') as file:
            var_list = file.readlines()
            
            database_url = var_list[0][:-1]
            password_db = var_list[1][:-1]
            user_db = var_list[2][:-1]
            name_db = var_list[3][:-1]
            port_db = var_list[4]
            
        self.db_connector = connect(host=str(database_url), password=str(password_db), user=str(user_db), port=str(port_db), dbname=str(name_db))
        self.db_cursor = self.db_connector.cursor()
        self.widgets_cache["db_button_filter"]["state"] = tk.NORMAL
        self.widgets_cache["db_button_add_tags"]["state"] = tk.NORMAL
        self.widgets_cache["db_button_delete_tags"]["state"] = tk.NORMAL
        self.widgets_cache["db_button_reconnect"]["state"] = tk.DISABLED
        print(self.db_cursor)
    
    def filter_db(self):  # TODO connect with the event system
        
        def insert_tags():
            tags = self.get_tags()
            for tag in tags:
                if tag[0] not in self.db_set_tags:
                    tags_tree.insert("", "end", iid=tag, text=tag)
            for tag in self.db_set_tags:
                select_tree.insert("", "end", iid=tag, text=tag)
                
        def move_to_selected_tags():
            tags = tags_tree.selection()
            if tags:
                for tag in tags:
                    select_tree.insert("", "end", iid=tag, text=tag)
                tags_tree.delete(*tags)
            
        def move_to_unselected_tags():
            tags = select_tree.selection()
            if tags:
                for tag in tags:
                    tags_tree.insert("", "end", iid=tag, text=tag)
                select_tree.delete(*tags)
        
        def return_tags():
            tags = set(select_tree.get_children())
            print(f"previous tags: {self.db_set_tags}")
            self.db_set_tags.clear()
            self.db_set_tags.update(tags)
            print(f"tags now: {self.db_set_tags}")
            new_toplevel.destroy()
        
        new_toplevel = tk.Toplevel()
        new_toplevel.title(string="Filter results")
        new_toplevel.resizable(False, False)
        
        tags_frame = ttk.Frame(new_toplevel, width=300, height=500)
        buttons_frame = ttk.Frame(new_toplevel, width=100, height=500)
        select_frame = ttk.Frame(new_toplevel, width=300, height=500)
        tags_frame.grid(column=0, sticky=tk.NSEW)
        buttons_frame.grid(column=1, row=0)
        select_frame.grid(column=2, row=0, sticky=tk.NSEW)
        
        #  sides
        tags_tree = ttk.Treeview(tags_frame, selectmode="extended")
        select_tree = ttk.Treeview(select_frame, selectmode="extended")
        tags_tree.grid(row=0, column=0)
        tags_tree.heading("#0", text="Available tags")
        tags_tree.column("#0", width=100, anchor="center")
        insert_tags()
        select_tree.grid(row=0, column=0)
        select_tree.heading("#0", text="Selected tags")
        select_tree.column("#0", width=100, anchor="center")
        
        tags_scroll = ttk.Scrollbar(tags_frame, orient=tk.VERTICAL, command=tags_tree.yview)
        select_scroll = ttk.Scrollbar(select_frame, orient=tk.VERTICAL, command=select_tree.yview)
        tags_scroll.grid(row=0, column=1, sticky=tk.NS)
        select_scroll.grid(row=0, column=1, sticky=tk.NS)
        tags_tree.config(yscrollcommand=tags_scroll.set)
        select_tree.config(yscrollcommand=select_scroll.set)
        #  center
        tags_button = ttk.Button(buttons_frame, text="<", command=move_to_unselected_tags)
        select_button = ttk.Button(buttons_frame, text=">", command=move_to_selected_tags)
        exit_button = ttk.Button(buttons_frame, text="OK", command=return_tags)
        tags_button.grid(row=0, padx=10)
        select_button.grid(row=1, padx=10)
        exit_button.grid(row=2, padx=10)
    
    def add_tags_db(self):
        
        all_unwanted_chars_list = list(punctuation)
        allowed_punctuation = ["_", "-"]
        for char in allowed_punctuation:
            all_unwanted_chars_list.remove(char)
        [all_unwanted_chars_list.append(x) for x in list(digits)]
        [all_unwanted_chars_list.append(x) for x in list(whitespace)]
        auc_set = set(all_unwanted_chars_list)
        
        tags_set = set()
        
        def verify_entry():
            nonlocal tags_set
            raw_list = tags_svar.get().split(sep=" ")
            tags_set = set([x for x in raw_list if x and x not in auc_set])
            if tags_set:
                """a note
                execute_button.state(["active"]) has no effect, while .state([tk.NORMAL]) throws TclError: Invalid state name normal
                both execute_button["state"] = "active" and execute_button["state"] = tk.NORMAL works just fine though
                """
                execute_button["state"] = tk.NORMAL
                
            else:
                execute_button["state"] = tk.DISABLED
        
        def add_tags():
            self.add_tags(tags_set, info_svar)
            tags_svar.set("")
            execute_button["state"] = tk.DISABLED
        
        new_toplevel = tk.Toplevel()
        new_toplevel.title(string="Add tags")
        new_toplevel.resizable(False, False)
        main_frame = ttk.Frame(new_toplevel, width=300, height=500)
        main_frame.grid()
        
        tags_svar = tk.StringVar()
        tags_svar.trace_add("write", lambda name, idx, mode: verify_entry())  # lambda for handling redundant data
        
        info_svar = tk.StringVar(value=self.info_string_tags)
        info_label = ttk.Label(main_frame, textvariable=info_svar, text=info_svar.get())
        tag_entry = ttk.Entry(main_frame, textvariable=tags_svar)
        execute_button = ttk.Button(main_frame, text="Add the tag(s)", command=add_tags)
        info_label.grid(column=1, row=0)
        tag_entry.grid(column=1, row=1)
        execute_button.grid(column=1, row=2)
        execute_button["state"] = tk.DISABLED
        print(f"Label: {info_label}, entry: {tag_entry}, button: {execute_button}")
    
    def delete_tags_db(self):
        def delete_tags():
            tags = tags_tree.selection()
            if tags:
                tags_tree.delete(*tags)
                # creates an sql request that deletes any given number of tags, [:-1]+")" is to replace the last comma
                # "DELETE FROM tags_list WHERE tag IN ('tag1', 'tag2')"
                self.db_cursor.execute("".join([self.db_string_delete_tags, "(", *[f"'{tag}'," for tag in tags]])[:-1]+")")
                self.db_connector.commit()
                self.db_set_tags.difference(tags)
                delete_button["state"] = tk.DISABLED
        
        def insert_tags():
            tags = self.get_tags()
            for tag in tags:
                tags_tree.insert("", "end", iid=tag, text=tag)
        
        def check_if_selected():
            if tags_tree.selection():
                delete_button["state"] = tk.NORMAL
            else:
                delete_button["state"] = tk.DISABLED
        
        new_toplevel = tk.Toplevel(width=300)
        new_toplevel.title(string="Delete tags")
        new_toplevel.resizable(False, False)
        main_frame = ttk.Frame(new_toplevel, width=300, height=500)
        main_frame.grid(row=0, column=0)

        tags_tree = ttk.Treeview(main_frame, selectmode="extended")
        tags_tree.grid(row=1, column=0)
        tags_tree.heading("#0", text="Available tags")
        tags_tree.column("#0", width=120, anchor="center")
        tags_tree.bind("<<TreeviewSelect>>", lambda redundant_event_coords: check_if_selected())
        insert_tags()
        tags_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tags_tree.yview)
        
        delete_button = ttk.Button(main_frame, text="Delete", command=delete_tags)
        delete_button.grid(row=0, column=0, columnspan=2, sticky=tk.EW)
        delete_button["state"] = tk.DISABLED
        tags_scroll.grid(row=1, column=1, sticky=tk.NS)
        tags_tree.config(yscrollcommand=tags_scroll.set)
    
    def edit_db(self):  # to edit a field and save new value / additional buttons?
        # take loaded data and replace it / commit() on save
        pass

    # Additional functions for GUI
    def get_event_data(self, event_id):
        self.db_cursor.execute(self.db_string_search, event_id)
        self.db_event_data["titles"], self.db_event_data["desc_texts"], self.db_event_data["dict_data"], \
            self.db_event_data["stats_data"], self.db_event_data["embed_texts"], self.db_event_data["options"], \
            self.db_event_data["panel_name"], self.db_event_data["event_codes"], self.db_event_data["tags"] \
            = self.db_cursor.fetchone()
    
    def get_events(self, tags=None, event_id=None):
        if not event_id:
            # @> - checks if provided tags are a subset of event's. From ["tag1", "tag2"] makes " AND tags @> {'tag1', 'tag2'}"
            db_string_search_new = "".join([self.db_string_get_events, " WHERE tags @> {{{}}}".format("".join([f"'{tag}', " for tag in tags])[:-2])])
            self.db_cursor.execute(db_string_search_new)
        else:
            db_string_search_new = "".join([self.db_string_get_events, " WHERE id_event=%s"])
            self.db_cursor.execute(db_string_search_new, tuple(event_id))
        events_list = self.db_cursor.fetchall()
        print("Get Events DEBUG: ", events_list)
        if not events_list:
            return "None found, change tags."
        elif len(events_list) > 10:
            return f"Overflow of events, adjust tags. Number of events: {len(events_list)}. Expected up to 10."
        else:
            return events_list  # list of tuples (panel_name, id_event)
    
    def get_tags(self):
        self.db_cursor.execute(self.db_string_get_tags)
        return self.db_cursor.fetchall()  # list of tags
    
    def add_tags(self, tags_list, debug_label_svar=None):
        tags_raw = self.get_tags()
        tags_db = set()
        [tags_db.add(tag[0]) for tag in tags_raw]  # get_tags() returns a list of tuples, it converts the data into a set of strings
        duplicates = set(tags_list).intersection(tags_db)  # gets a set of duplicates if entry contains something already existing in the database
        [tags_list.remove(tag) for tag in duplicates]  # removes duplicates
        if debug_label_svar:
            if duplicates:
                debug_label_svar.set(self.info_string_tags+self.warning_string_tags.format(duplicates))
            else:
                debug_label_svar.set(self.info_string_tags+self.success_string_tags)
        #  print("tags list: {}, sql request: {}".format(tags_list, "".join([self.db_string_add_tags, *[f"('{tag}'), " for tag in tags_list]])[:-2]))
        if tags_list:  # writes an SQL request with all the data, [:-2] deletes ", "
            self.db_cursor.execute("".join([self.db_string_add_tags, *[f"('{tag}'), " for tag in tags_list]])[:-2])
            self.db_connector.commit()
        else:
            if debug_label_svar:
                debug_label_svar.set(self.info_string_tags+self.error_string_tags)


class EventNotebook(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)



        self.data = ObservableDict()
        self.data_index = ObservableInt(-1)
        self.last_button_index = ObservableInt(-1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.buttons_frame = ttk.Frame(self, width=200, height=20)
        self.buttons_frame.grid(column=0, row=0, sticky=tk.N)
        self.events_frame = ttk.Frame(self, width=200, height=200)  # hmm
        self.events_frame.grid(column=0, row=1)

    @property
    def last_index(self):
        return self.last_button_index.value

    @last_index.setter
    def last_index(self, new_value):
        self.last_button_index.value = new_value

    def add_tab(self, text):
        """
        EventButton( ..., command=...) is a hacky part which works because
        the value of command isn't evaluated till the button is clicked
        so can get it assigned before the value exist.  But it is necessary,
        otherwise all buttons would refer to the EventBase of index == self.data_index
        instead of the index when they were created
        """
        self.data_index += 1
        event_button = EventButton(self.data_index, master=self.buttons_frame, text=text,
                                   command=lambda: self.switch_event_button(event_button.get_index()))
        event_button.grid(row=0, column=self.data_index)
        event_handler = EventBase(self.events_frame)
        event_handler.columnconfigure((0, 1, 2), weight=1)
        self.data[self.data_index] = event_handler

    def remove_tab(self, idx):
        self.data_index -= 1
        pass

    def get_active_tab(self):
        return self.data[self.last_index]

    def index(self, set_to: int = -1):
        if set_to != -1:
            self.last_index = set_to
        else:
            return self.last_index

    def switch_event_button(self, index):
        if index != self.last_index:
            # if index changed - change the "tab"
            if self.last_index != -1:
                # -1 is an indicator of the first run, when the EventBase frames doesn't exist yet
                self.data[self.last_index].grid_remove()
                val_list = list(self.data[index].data_dict.values())
                # todo replace root...._buttons
                root.disable_buttons(val_list)
                root.enable_buttons(val_list)
            self.data[index].grid()
            self.last_index = index


class EventBase(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # 0 - titles, 1 - separator, 2 - description text || pre-init of Embed
        # 3 - embed field ("name":value), 4 - stats embed field ("name":60/100), 5 - descriptions embeds || post-init of Embed
        self.data_dict = ObservableDict({  # lists of EventFields
            "title": [],
            "separator": [],
            "desc": [],
            "embed": [],
            "embed_stats": [],
            "embed_text": []
        })
        self._index_simple = -1
        self.row_number = -1  # just for now
        self.bind("<Expose>", self.on_expose)

    @staticmethod
    def on_expose(event):
        """to solve an issue about not resizing after deletion of text fields"""
        if not event.widget.children:
            event.widget.configure(height=1)

    def add_field(self, idx_field):
        if idx_field <= 2:
            self._index_simple += 1
        self.row_number += 1
        event_field = EventField(self._index_simple, self)
        event_field.grid(column=1, row=self.row_number)
        self.rowconfigure(self.row_number, weight=1)
        self.columnconfigure(1, weight=1)
        if idx_field == 0:
            event_field.add_title()
            self.data_dict["title"].append(event_field)
        elif idx_field == 1:
            event_field.add_separator()
            self.data_dict["separator"].append(event_field)
        elif idx_field == 2:
            event_field.add_description()
            self.data_dict["desc"].append(event_field)
        elif idx_field == 3:
            event_field.add_embed()
            self.data_dict["embed"].append(event_field)
        elif idx_field == 4:
            event_field.add_embed_stats()
            self.data_dict["embed_stats"].append(event_field)
        elif idx_field == 5:
            event_field.add_embed_text()
            self.data_dict["embed_text"].append(event_field)

    def delete_field(self):
        for field_type in self.data_dict.keys():
            temp_list = self.data_dict[field_type]  # temp list so there's no issue when deleting the elements
            for field in temp_list:
                if field.selected.get():
                    field.destroy()
            for field in temp_list:
                if field.selected.get():
                    self.data_dict[field_type].remove(field)
        # todo replace root...._buttons
        root.enable_buttons(list(self.data_dict.values()))

    def recalculate_fields_position(self):
        # ensures there's no empty rows
        pass

    def verify_field(self):
        for field_type in self.data_dict.keys():
            if self.data_dict[field_type]:  # doesn't bother to check empty lists
                temp_list = self.data_dict[field_type]
                for idx, field in enumerate(temp_list):  # looking through the elements of a list
                    if field.selected.get():
                        pass


class EventField(ttk.Labelframe):
    def __init__(self, instance_idx, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.instance_idx = instance_idx
        self.chosen_field = ""
        self.selected = tk.BooleanVar(master=self, value=False)
        self.inline = tk.BooleanVar(master=self, value=False)  # if relevant
        self.text = tk.StringVar(master=self)  # master=self so it gets deleted with widget

    def add_title(self):
        self.chosen_field = "title"
        if self.instance_idx == 0:
            self.config(text="Event Title")
        else:
            self.config(text="Text Title")
        text_entry = ttk.Entry(self, textvariable=self.text)
        text_entry.grid(column=0, row=0)
        select_check = ttk.Checkbutton(self, text="select", variable=self.selected, onvalue=True,
                                       offvalue=False)
        select_check.grid(column=1, row=0)

    def add_separator(self):
        def verify():
            if len(self.text.get()) > 1:
                self.text.set(self.text.get()[:1])

        self.chosen_field = "separator"
        self.config(text="Separator")
        text_entry = ttk.Entry(self, textvariable=self.text)
        text_entry.grid(column=0, row=0)
        self.text.trace_add("write", lambda name, idx_, mode: verify())
        select_check = ttk.Checkbutton(self, text="select", variable=self.selected, onvalue=True,
                                       offvalue=False)
        select_check.grid(column=1, row=0)

    def add_description(self):  # TODO add verify
        def update_text():
            self.text.set(text_text.get("1.0", "end-1c"))

        self.chosen_field = "desc"
        self.config(text="Description")
        text_text = tk.Text(self, width=40, height=5, wrap="word")
        text_text.grid(column=0, row=0)
        text_text.bind("<<Modified>>", lambda e: update_text())
        select_check = ttk.Checkbutton(self, text="select", variable=self.selected, onvalue=True,
                                       offvalue=False)
        select_check.grid(column=1, row=0)
        print(text_text)

    def add_embed(self):
        self.chosen_field = "embed"
        self.config(text="Simple Embed")
        text_entry = ttk.Entry(self, textvariable=self.text)
        text_entry.grid(column=0, row=0)
        select_check = ttk.Checkbutton(self, text="select", variable=self.selected, onvalue=True,
                                       offvalue=False)
        select_check.grid(column=1, row=0)
        inline_check = ttk.Checkbutton(self, text="inline", variable=self.inline, onvalue=True,
                                       offvalue=False)
        inline_check.grid(column=2, row=0)

    def add_embed_stats(self):
        self.chosen_field = "embed_stats"
        self.config(text="Embed Stats")
        text_entry = ttk.Entry(self, textvariable=self.text)
        text_entry.grid(column=0, row=0)
        select_check = ttk.Checkbutton(self, text="select", variable=self.selected, onvalue=True,
                                       offvalue=False)
        select_check.grid(column=1, row=0)
        inline_check = ttk.Checkbutton(self, text="inline", variable=self.inline, onvalue=True,
                                       offvalue=False)
        inline_check.grid(column=2, row=0)

    def add_embed_text(self):
        def update_text():
            self.text.set(text_text.get("1.0", "end-1c"))

        self.chosen_field = "embed_text"
        self.config(text="Embed Text")
        text_text = tk.Text(self, width=40, height=5, wrap="word")
        text_text.grid(column=0, row=0, rowspan=2)
        text_text.bind("<<Modified>>", lambda e: update_text())
        select_check = ttk.Checkbutton(self, text="select", variable=self.selected, onvalue=True,
                                       offvalue=False)
        select_check.grid(column=1, row=0, sticky=tk.N, pady=5)
        inline_check = ttk.Checkbutton(self, text="inline", variable=self.inline, onvalue=True,
                                       offvalue=False)
        inline_check.grid(column=1, row=1)


class EventButton(ttk.Button):
    def __init__(self, index, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.index = index

    def set_index(self, value):
        self.index = value

    def get_index(self):
        return self.index


class EventButtonLogic:
    # todo rework
    def __init__(self, event_base, buttons_count_dict):
        self._observer: EventBase = event_base
        self._buttons_cd = buttons_count_dict

    def enable_buttons(self, button_list):
        if isinstance(button_list[3], int):
            if button_list[3] + button_list[4] + button_list[5] > 0:
                self._observer["title"]["state"] = tk.NORMAL
                self._observer["separator"]["state"] = tk.NORMAL
                self._observer["desc"]["state"] = tk.NORMAL
        else:
            if len(button_list[3] + button_list[4] + button_list[5]) == 0:
                self._observer["title"]["state"] = tk.NORMAL
                self._observer["separator"]["state"] = tk.NORMAL
                self._observer["desc"]["state"] = tk.NORMAL

    def disable_buttons(self, button_list):
        if isinstance(button_list[3], int):
            if button_list[3] + button_list[4] + button_list[5] > 0:
                self._observer["title"]["state"] = tk.DISABLED
                self._observer["separator"]["state"] = tk.DISABLED
                self._observer["desc"]["state"] = tk.DISABLED
        else:
            if len(button_list[3] + button_list[4] + button_list[5]) > 0:
                self._observer["title"]["state"] = tk.DISABLED
                self._observer["separator"]["state"] = tk.DISABLED
                self._observer["desc"]["state"] = tk.DISABLED


class Observable(ABC):
    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def delete_observer(self, observer):
        self._observers.remove(observer)

    def get_observers(self):
        return self._observers

    @abstractmethod
    def notify(self, *args):
        """to implement conditions when observers gets notified
        if ...:
            for observer in self._observers:
                observer.notified()"""
        pass


class Observer(ABC):
    @abstractmethod
    def notified(self, *args):
        """what to do when you get notified"""
        pass


class ObservableDict(dict, Observable):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.notify("ObsDict_setitem", key, value)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.notify("ObsDict_delitem", key)

    def notify(self, *args):
        for observer in self.get_observers():
            observer.notified(*args)


class ObservableInt(Observable, int):
    """
    Warning - don't use plain assignment because it overwrites the class
    use <obj>.value instead, eg.
    my_special_int.value = 10
    everything else should be fine
    """
    def __init__(self, value):
        super().__init__()
        print("init value: ", value)
        self._value = value

    def notify(self, *args):
        for observer in self.get_observers():
            observer.notified(*args)

    @property
    def value(self):
        print("simple value: ", self._value)
        return self._value

    @value.setter
    def value(self, new_value):
        print("setter - new value: ", new_value)
        self._value = new_value
        self.notify("ObsInt_setter", new_value)

    def __add__(self, other):
        return self.value + other

    def __iadd__(self, other):
        self.value = self.value + other
        return self

    def __sub__(self, other):
        return self.value - other

    def __isub__(self, other):
        self.value = self.value - other
        return self


if __name__ == "__main__":
    root = Application()
    root.mainloop()
