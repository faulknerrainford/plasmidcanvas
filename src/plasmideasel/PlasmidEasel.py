from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
import pandas as pd
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji
from ttkbootstrap.validation import *
from plasmideasel import Plasmid, draw_plasmid
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from functools import partial
from Bio import SeqIO
from plasmideasel.DFTable import DFTable

class PlasmidEasel(ttk.Window):
    """
    Main application window for the PlasmidEasel GUI.

    Extends ``ttkbootstrap.Window`` and provides a matplotlib canvas for
    plasmid visualisation alongside tabbed control panels for editing plasmid
    properties and feature tables.

    Attributes
    ----------
    plasmid_title : tk.StringVar
        The current plasmid name.
    plasmid_bps : tk.IntVar
        The current plasmid length in base pairs.
    show_ticks : tk.BooleanVar
        Whether to show ticks on the plasmid (controls tick_style: 'auto' or 'none').
    title_font_size : tk.IntVar
        Font size for the plasmid title.
    label_font_size : tk.IntVar
        Font size for feature labels and tick labels.
    include_bp_in_labels : tk.StringVar
        Whether to include base pair position in feature labels (``'bases'`` or ``'text_only'``).
    PLASMID : Plasmid
        The Plasmid model object being visualised.
    PLASMID_DF : pd.DataFrame or None
        Feature data loaded from file.
    FIG : matplotlib.figure.Figure
        The active figure used for rendering.
    fig_size : tuple of int
        Width and height in inches for the matplotlib figure.
    canvas_figures : list of FigureCanvasTkAgg
        History of canvas objects; the last entry is the active one.
    plasmid_style : tk.StringVar
        Selected rendering style (``'default'`` or ``'minimalist'``).
    commands_log : list
        Command history for undo/redo, capped at 10 entries.
    commands_pointer : int
        Index into ``commands_log`` pointing to the current state.
    """

    def __init__(self, **kw):
        """
        Initialise the window, menus, matplotlib canvas and control panels.

        Parameters
        ----------
        **kw
            Keyword arguments forwarded to ``ttkbootstrap.Window``.
        """
        super(PlasmidEasel, self).__init__(themename="pulse", **kw)
        self.title("PlasmidEasel")
        self.plasmid_title = tk.StringVar(None, "TORC")
        self.plasmid_bps = tk.IntVar(None, 1200)
        self.PLASMID: Plasmid = Plasmid(self.plasmid_title.get(), self.plasmid_bps.get())
        self.PLASMID_DF: pd.DataFrame = pd.DataFrame()
        self.SEPARATORS = {"tsv": "\t", "csv": ","}
        self.FIG = self.PLASMID.plot()
        self.fig_size = (3, 3)
        self.FIG.set_size_inches(self.fig_size[0], self.fig_size[1])
        self.canvas_figures = []
        self.plasmid_style = tk.StringVar(None, 'default')
        self.show_ticks = tk.BooleanVar(None, True)
        self.title_font_size = tk.IntVar(None, 14)
        self.label_font_size = tk.IntVar(None, 7)
        self.include_bp_in_labels = tk.StringVar(None, 'bases')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.commands_log: list[tuple] = [()]
        self.commands_pointer = 0

        # Creating Menubar
        menubar = tk.Menu(self)

        # Adding File Menu and commands
        file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file)
        file.add_command(label='Open...', command=self.open_file)
        file.add_command(label='Save As...', command=self.save_canvas)
        file.add_separator()
        file.add_command(label='Exit', command=self.destroy)

        # Adding Edit Menu and commands
        self.edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Edit', menu=self.edit)

        self.edit.add_command(label='Undo', command=self.undo_command, accelerator='Ctrl+Z', state='disabled')
        self.edit.add_command(label='Redo', command=self.redo_command, accelerator='Ctrl+Shift+Z', state='disabled')
        self.bind('<Control-z>', self.undo_command, add='+')
        self.bind('<Control-Shift-z>', self.redo_command, add='+')


        # Adding Help Menu
        help_ = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_)
        # help_.add_command(label='PlasmidEasel Docs', command=None, state='disabled')

        self.config(menu=menubar)

        # Add canvas to draw figure on
        CANVAS = FigureCanvasTkAgg(self.FIG, master=self)
        self.canvas_figures.append(CANVAS)
        CANVAS.draw()
        CANVAS.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Add notebook for control pannels
        controlpannels = ttk.Notebook(self, bootstyle="secondary")
        general = GeneralPanel(controlpannels)
        self.table = TablePanel(controlpannels)
        self.features = FeaturePanel(controlpannels)
        controlpannels.add(general, text="General")
        controlpannels.add(self.table, text="Table")
        controlpannels.add(self.features, text="Features")
        controlpannels.grid(row=0, column=1, sticky='nsew')
        controlpannels.columnconfigure(0, weight=1)
        controlpannels.rowconfigure(0, weight=1)

    def open_file(self):
        """
        Open a CSV, TSV or GenBank file and load its contents.

        Prompts the user with a file dialog. On success the plasmid title,
        base-pair count and feature DataFrame are updated, the table panel is
        reloaded and the plasmid canvas is redrawn.
        """
        filename = filedialog.askopenfilename(defaultextension='.csv',
                                              filetypes=[('CSV files', '*.csv'), ('TSV Files', '*.tsv'), ('Genbank', '*.gb')])
        if filename.endswith('.csv') or filename.endswith('.tsv'):
            file = open(filename, mode='r')
            contents = file.readlines()
            self.plasmid_bps.set(int(contents[1]))
            self.plasmid_title.set(contents[0].split()[0])
            # HEADER = contents[0].split()[1:]
            self.PLASMID_DF = pd.read_csv(filename, sep=self.SEPARATORS[filename[-3:]], header=2)
        elif filename.endswith('.gb'):
            # load genbank file and convert to plasmid df
            sequence = SeqIO.read(filename, 'genbank')
            # Get plasmid label and bp_length
            self.plasmid_title.set(sequence.name)
            self.plasmid_bps.set(len(sequence.seq))
            # Set up dataframe to take features
            plasmid_df = pd.DataFrame(columns=["index", "name",	"type",	"start", "end",	"direction", "colour"])
            i = 0
            for feature in sequence.features:
                # For each feature get: name, type, start, end, direction and colour
                # Try to extract feature name from qualifiers in order of preference
                if 'label' in feature.qualifiers:
                    name = feature.qualifiers['label'][0]
                elif 'product' in feature.qualifiers:
                    name = feature.qualifiers['product'][0]
                elif 'gene' in feature.qualifiers:
                    name = feature.qualifiers['gene'][0]
                else:
                    name = feature.type
                type = feature.type
                start = feature.location.start
                end = feature.location.end
                direction = feature.location.strand if feature.location.strand is not None else 0
                colour = 'black'
                # Look for colour qualifiers (case-insensitive, handles both 'color' and 'colour')
                for col in feature.qualifiers.keys():
                    if 'color' in col.lower():
                        colour = feature.qualifiers[col][0]
                        break
                # form row and add to dataframe
                plasmid_df.loc[len(plasmid_df)] = [i, name, type, start, end, direction, colour]
                i += 1
            self.PLASMID_DF = plasmid_df

        self.table.load_data()
        self.features.load_data()
        self.table.apply_to_plasmid()

    def save_canvas(self):
        """
        Save the current plasmid figure to a user-chosen file.

        Supports PNG, SVG, PDF and JPG output formats selected via a save
        dialog.
        """
        filename = filedialog.asksaveasfilename(filetypes=[('PNG files', '*.png'), ('SVG files', '*.svg'),
                                                           ('PDF files', '*.pdf'), ('JPG files', '*.jpg')])
        self.PLASMID.save_to_file(filename)

    def redraw_plasmid(self):
        """
        Replace the active matplotlib canvas with a freshly drawn figure.

        Removes the previous canvas from the grid and places the new one in
        its position.
        """
        self.FIG = self.PLASMID.plot()
        self.FIG.set_size_inches(self.fig_size[0], self.fig_size[1])
        self.canvas_figures[-1].get_tk_widget().pack_forget()
        new_canvas = FigureCanvasTkAgg(self.FIG, master=self)
        self.canvas_figures.append(new_canvas)
        new_canvas.draw_idle()
        new_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    def update_plasmid(self, *kw):
        """
        Record a command snapshot and regenerate the plasmid from current settings.

        Logs the current state to the undo history, rebuilds ``self.PLASMID``
        via ``draw_plasmid`` and triggers a canvas redraw.

        Parameters
        ----------
        *kw
            Unused; present so the method can be used as a tkinter callback.
        """
        self.command_add(("GENERAL_PLASMID_UPDATE", self.PLASMID, self.plasmid_title.get(), self.plasmid_bps.get()))
        self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                    self.plasmid_style.get())
        tick_marker_style = 'auto' if self.show_ticks.get() else 'none'
        self.PLASMID.set_tick_style(tick_marker_style)
        self.PLASMID.set_marker_style(tick_marker_style)
        self.PLASMID.set_title_font_size(self.title_font_size.get())
        self.PLASMID.set_marker_label_font_size(self.label_font_size.get())
        self.PLASMID.set_feature_label_font_size(self.label_font_size.get())
        self.PLASMID.set_feature_label_style(self.include_bp_in_labels.get())
        self.redraw_plasmid()
        self.focus_get().focus_set()

    def command_add(self, command: tuple):
        """
        Append a command tuple to the undo/redo history.

        Truncates any redo-forward history beyond the current pointer, appends
        the new command, and keeps the log to at most 10 entries. Enables the
        Undo menu item and disables Redo.

        Parameters
        ----------
        command : tuple
            A descriptor whose first element is the command name string, e.g.
            ``'GENERAL_PLASMID_UPDATE'``, ``'DELETE'``, or ``'ADD_ROW'``.
        """
        self.commands_pointer += 1
        if self.commands_pointer != len(self.commands_log)-1:
            self.commands_log= self.commands_log[:self.commands_pointer]
        self.commands_log.append(command)
        if len(self.commands_log) > 11:
            self.commands_pointer = 10
            self.commands_log.remove(self.commands_log[1])
        self.edit.entryconfig('Undo', state=tk.NORMAL)
        self.edit.entryconfig('Redo', state=tk.DISABLED)

    def undo_command(self, *kw):
        """
        Undo the most recent logged command.

        Restores the application state described by the command at
        ``commands_pointer`` and decrements the pointer. Disables Undo when
        the beginning of the log is reached and enables Redo.
        """
        if self.commands_log[self.commands_pointer][0]:
            command = self.commands_log[self.commands_pointer]
            if command[0] == "GENERAL_PLASMID_UPDATE":
                self.PLASMID = command[1]
                self.redraw_plasmid()
                self.focus_get().focus_set()
            elif command[0] == "DELETE":
                # Undo delete by restoring the row data
                self.table.Table.undo_delete_row(command[1], command[2], command[3], command[4])
            elif command[0] == "ADD_ROW":
                ind = self.table.Table.table_df.shape[0] - 1
                self.table.Table.delete_row(ind + 1, self.table.Table.table_df.iloc[ind]['name'].get(), index_1=True, log=False)
            self.commands_pointer -= 1
        self.edit.entryconfig('Redo', state=tk.NORMAL)
        if self.commands_pointer == 0:
            self.edit.entryconfig('Undo', state=tk.DISABLED)

    def redo_command(self, *kw):
        """
        Redo the next command in the history log.

        Advances ``commands_pointer`` and re-applies the command at the new
        position. Disables Redo when the end of the log is reached.
        """
        if len(self.commands_log) > self.commands_pointer + 1:
            self.commands_pointer += 1
            if len(self.commands_log)-1 == self.commands_pointer:
                self.edit.entryconfig('Redo', state=tk.DISABLED)
            command = self.commands_log[self.commands_pointer]
            if command[0] == "GENERAL_PLASMID_UPDATE":
                self.plasmid_title.set(command[2])
                self.plasmid_bps.set(command[3])
                self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                            self.plasmid_style.get())
                self.redraw_plasmid()
                self.focus_get().focus_set()
            elif command[0] == "DELETE":
                # Redo delete by deleting the row again
                self.table.Table.delete_row(command[1], command[2], index_1=True)
            elif command[0] == "ADD_ROW":
                self.table.add_row(log=False)


class GeneralPanel(ttk.Frame):
    """
    A control panel for editing high-level plasmid properties.

    Provides style-selection radio buttons, plasmid title and base-pair-size
    inputs, font size controls, tick label display option, and label formatting
    options. All controls are bound to the parent ``PlasmidEasel`` instance.

    Parameters
    ----------
    master : tk.Widget, optional
        The parent notebook or container widget.
    """

    def __init__(self, master=None):
        """
        Build and lay out the style selector, title/BP inputs and Apply button.

        Parameters
        ----------
        master : tk.Widget, optional
            The parent widget (typically a ``ttk.Notebook``).
        """
        super().__init__(master)
        self.Easel = self.master.master
        # Radio button style selection
        style = tk.LabelFrame(self, text='Style')

        style_default = ttk.Radiobutton(style, text='Default', variable=self.Easel.plasmid_style, value='default',
                                        command=self.Easel.update_plasmid)
        style_mini = ttk.Radiobutton(style, text='Minimalist', variable=self.Easel.plasmid_style, value='minimalist',
                                     command=self.Easel.update_plasmid)
        style_default.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
        style_mini.grid(row=0, column=1, sticky='nsew', pady=5, padx=5)

        style.grid(row=0, column=0, sticky='nsew', pady=5, padx=5, columnspan=2)

        # Title label with textinput, preset to match plasmid_title and updates when modified
        title_label = ttk.Label(self, text='Plasmid Title', font=('Arial', 12))
        title_label.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        self.title_input = ttk.Entry(self, textvariable=self.Easel.plasmid_title)
        self.title_input.grid(row=1, column=1, sticky='nsew', pady=5, padx=5)
        # Same as above with bp size
        bps_label = ttk.Label(self, text='Base Pair Size', font=('Arial', 12))
        bps_label.grid(row=2, column=0, sticky='nsew', pady=5, padx=5)
        self.bps_input = ttk.Entry(self, textvariable=self.Easel.plasmid_bps)
        add_numeric_validation(self.bps_input, when='key')
        self.bps_input.grid(row=2, column=1, sticky='nsew', pady=5, padx=5)
        
        # Title Font Size
        title_font_label = ttk.Label(self, text='Title Font Size', font=('Arial', 12))
        title_font_label.grid(row=3, column=0, sticky='nsew', pady=5, padx=5)
        self.title_font_input = ttk.Spinbox(self, from_=6, to=32, textvariable=self.Easel.title_font_size, 
                                             command=self.Easel.update_plasmid, width=10)
        self.title_font_input.grid(row=3, column=1, sticky='nsew', pady=5, padx=5)
        
        # Label Font Size
        label_font_label = ttk.Label(self, text='Label Font Size', font=('Arial', 12))
        label_font_label.grid(row=4, column=0, sticky='nsew', pady=5, padx=5)
        self.label_font_input = ttk.Spinbox(self, from_=4, to=24, textvariable=self.Easel.label_font_size, 
                                             command=self.Easel.update_plasmid, width=10)
        self.label_font_input.grid(row=4, column=1, sticky='nsew', pady=5, padx=5)
        
        # Show Ticks Checkbox
        self.ticks_check = ttk.Checkbutton(self, text='Show Ticks', variable=self.Easel.show_ticks,
                                           command=self.Easel.update_plasmid)
        self.ticks_check.grid(row=5, column=0, sticky='nsew', pady=5, padx=5, columnspan=2)
        
        # Include BP in Labels Checkbox
        self.bp_labels_check = ttk.Checkbutton(self, text='Include BP Position in Labels', 
                                               variable=self.Easel.include_bp_in_labels, 
                                               onvalue='bases', offvalue='text_only',
                                               command=self.Easel.update_plasmid)
        self.bp_labels_check.grid(row=6, column=0, sticky='nsew', pady=5, padx=5, columnspan=2)
        
        # Update plasmid with new labels
        apply = ttk.Button(self, command=self.Easel.update_plasmid, text='Apply')
        apply.grid(row=7, column=0, sticky='nsew', pady=5, padx=5)

class TablePanel(ttk.Frame):
    """
    A control panel providing the editable feature table and row-management controls.

    Hosts a ``DFTable``, a ``RowPanel`` for per-row deletion, and buttons for
    adding rows, deleting rows by name, undoing deletions, applying changes to
    the plasmid and saving data.

    Parameters
    ----------
    master : ttk.Notebook, optional
        The parent notebook widget.

    Attributes
    ----------
    Easel : PlasmidEasel
        Reference to the top-level application window.
    Table : DFTable or None
        The active editable table widget; None until ``load_data`` is called.
    delete_var : tk.StringVar or None
        Holds the currently selected delete-target string.
    undo_delete_button : ttk.Button or None
        Enabled when deletions are available to undo.
    delete_select : ttk.Combobox or None
        Lists rows available for deletion by index and name.
    """

    def __init__(self, master: ttk.Notebook =None):
        """
        Initialise the panel with empty attribute placeholders.

        Parameters
        ----------
        master : ttk.Notebook, optional
            The parent notebook widget.
        """
        super().__init__(master)
        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.Easel: PlasmidEasel | Misc | None = self.master.master
        self.Table: DFTable | None = None
        self.table_frame: ttk.Frame | None = None
        self.delete_var: tk.StringVar | None = None
        self.undo_delete_button: ttk.Button | None = None
        self.delete_select: ttk.Combobox | None = None

    def load_data(self):
        """
        Build the DFTable and all row-management controls from ``Easel.PLASMID_DF``.

        Replaces any existing table with a freshly constructed ``DFTable`` and
        wraps it with a scrollbar for vertical scrolling.
        """
        if hasattr(self, 'table_frame') and self.table_frame:
            self.table_frame.grid_forget()
        
        # Create frame to hold canvas and scrollbar
        self.table_frame = ttk.Frame(self)
        self.table_frame.grid(row=0, column=0, sticky='nsew', pady=5, padx=5, columnspan=4)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar with specific height
        canvas = tk.Canvas(self.table_frame, highlightthickness=0, bg='white', height=400)
        scrollbar = ttk.Scrollbar(self.table_frame, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid canvas and scrollbar
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='nsew')
        
        # Create the table inside the canvas
        def on_delete_row(index, name):
            """Handle row deletion with undo/redo logging."""
            command = ("DELETE", index + 1, name, self.Table.rows.copy(), self.Table.table_df.copy())
            self.Easel.command_add(command)
            self.Table.delete_row(index, name, index_1=False)
        
        self.Table = DFTable(canvas, self.Easel.PLASMID_DF,
                             ['Int', 'String', 'String', 'Int', 'Int', 'Int', 'Colour', 'Select', 'String'],
                             on_delete=on_delete_row)
        self.table_window = canvas.create_window(0, 0, window=self.Table, anchor='nw')
        
        # Update scroll region when table is configured
        def on_table_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        
        self.Table.bind('<Configure>', on_table_configure)
        # Initial scroll region update
        canvas.configure(scrollregion=canvas.bbox('all'))
        
        # Enable mouse wheel scrolling with proper event handling
        def on_mousewheel(event):
            # Windows and MacOS use event.delta (positive = up, negative = down)
            if hasattr(event, 'delta') and event.delta != 0:
                # Scroll up on positive delta, down on negative delta
                canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
            # Linux uses event.num (4 = up, 5 = down)
            elif hasattr(event, 'num'):
                canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
            return 'break'  # Prevent event propagation
        
        # Bind mousewheel to canvas
        canvas.bind('<MouseWheel>', on_mousewheel)
        canvas.bind('<Button-4>', on_mousewheel)
        canvas.bind('<Button-5>', on_mousewheel)
        
        # Also bind to the table itself so scrolling works when mouse is over table
        self.Table.bind('<MouseWheel>', on_mousewheel)
        self.Table.bind('<Button-4>', on_mousewheel)
        self.Table.bind('<Button-5>', on_mousewheel)
        
        # Add buttons for save data, add row, delete row and undo delete
        apply_button = ttk.Button(self, text='Apply to Plasmid', command=self.apply_to_plasmid)
        apply_button.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        add_button = ttk.Button(self, text='Add Row', command=self.add_row)
        add_button.grid(row=1, column=1, sticky='nsew', pady=5, padx=5)
        save_button = ttk.Button(self, text='Save Data', command=self.save_data)
        save_button.grid(row=1, column=2, sticky='nsew', pady=5, padx=5)

    def add_row(self, log=True):
        """
        Append a blank row to the table and refresh the delete combobox.

        Parameters
        ----------
        log : bool, optional
            If ``True`` (default), records the operation in the undo history.
        """
        self.Table.add_row()
        self.RowPanel.add_row()
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        if log:
            self.master.Easel.command_add(("ADD_ROW"))

    def apply_to_plasmid(self):
        """
        Flush table edits to the plasmid model and trigger a redraw.

        Calls ``update_table`` on the ``DFTable``, updates ``Easel.PLASMID_DF``,
        invokes ``update_plasmid``, and resets the undo-delete button state.
        """
        self.Easel.PLASMID_DF = self.Table.update_table()
        self.Easel.update_plasmid()

    def save_data(self):
        """
        Save the current table data to a CSV or TSV file.
        
        Opens a file dialog allowing the user to choose between CSV and TSV
        formats. Saves all table data including show/hide visibility flags.
        The file can be reloaded in future sessions.
        """
        if not self.Table or self.Easel.PLASMID_DF.empty:
            messagebox.showwarning("No Data", "No feature data to save.")
            return
        
        # Update table to get latest values
        updated_df = self.Table.update_table()
        
        # Ask user for file format
        format_choice = messagebox.askyesno(
            "Save Format",
            "Save as CSV?\n\nYes: CSV (comma-separated)\nNo: TSV (tab-separated)"
        )
        
        # Set separator and file extension
        separator = "," if format_choice else "\t"
        file_ext = ".csv" if format_choice else ".tsv"
        
        # Open file save dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=[
                ("CSV files", "*.csv") if format_choice else ("TSV files", "*.tsv"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return  # User cancelled

        try:
            # Title and length lines come first so the file can be reopened; the loader keeps only the first word of the title
            title = "_".join(self.Easel.plasmid_title.get().split()) or "plasmid"
            with open(filename, mode='w', newline='') as file:
                file.write(f"{title}\n{self.Easel.plasmid_bps.get()}\n")
                updated_df.to_csv(file, sep=separator, index=False, lineterminator='\n')
            messagebox.showinfo("Success", f"Data saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def add_row(self):
        """
        Show or create a delete button for a newly added table row.

        If a previously hidden button exists it is re-gridded at the correct
        position; otherwise a new button is created and appended to
        ``self.buttons``.
        """
        row_count = self.Table.table_df.shape[0]
        if len(self.buttons) >= row_count:
            self.buttons[row_count-1].grid(row=row_count, column=0, sticky='nsew', pady=4, padx=5)
        else:
            button = ttk.Button(self, text=self.delete_icon, bootstyle=(INFO, OUTLINE),
                                command=lambda: self.delete_row(row_count))
            button.grid(row=row_count, column=0, sticky='nsew', pady=4, padx=5)
            self.buttons.append(button)


class FeaturePanel(ttk.Frame):
    """
    A control panel for filtering features by type.

    Displays checkboxes for each unique feature type in the DataFrame.
    Toggling a type checkbox sets all features of that type's 'show'
    column to match the toggle state. Individual toggles remain editable.

    Parameters
    ----------
    master : ttk.Notebook, optional
        The parent notebook widget.

    Attributes
    ----------
    Easel : PlasmidEasel
        Reference to the top-level application window.
    type_toggles : dict
        Maps feature type string to tk.BooleanVar toggle state.
    type_frames : dict
        Maps feature type string to its frame widget for updates.
    """

    def __init__(self, master: ttk.Notebook = None):
        """
        Initialise the feature filter panel with empty placeholders.

        Parameters
        ----------
        master : ttk.Notebook, optional
            The parent notebook widget.
        """
        super().__init__(master)
        self.Easel = self.master.master
        self.type_toggles = {}
        self.type_frames = {}
        self.columnconfigure(0, weight=1)

    def load_data(self):
        """
        Build the feature type toggles from unique types in PLASMID_DF.

        Clears existing toggles and creates a new one for each unique
        feature type. Each toggle controls the 'show' column for all
        rows of that type.
        """
        # Clear existing toggles
        for widget in self.winfo_children():
            widget.grid_forget()
        self.type_toggles.clear()
        self.type_frames.clear()

        # Get unique types from DataFrame
        if self.Easel.PLASMID_DF.empty or 'type' not in self.Easel.PLASMID_DF.columns:
            empty_label = ttk.Label(self, text='No features loaded')
            empty_label.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
            return

        unique_types = sorted(self.Easel.PLASMID_DF['type'].unique())

        # Create a scrollable frame for many feature types
        canvas = ttk.Canvas(self, height=200)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Create toggle for each type
        for idx, feature_type in enumerate(unique_types):
            var = ttk.BooleanVar(value=True)
            self.type_toggles[feature_type] = var

            callback = partial(self.on_type_toggle, feature_type)
            checkbox = ttk.Checkbutton(
                scrollable_frame,
                text=feature_type,
                variable=var,
                command=callback,
                bootstyle="info"
            )
            checkbox.grid(row=idx, column=0, sticky='w', pady=5, padx=10)

        canvas.grid(row=0, column=0, sticky='nsew', rowspan=2)
        scrollbar.grid(row=0, column=1, sticky='ns', rowspan=2)
        self.rowconfigure(0, weight=1)

        # Add buttons
        select_all = ttk.Button(
            self,
            text='Select All',
            command=self.select_all_types
        )
        select_all.grid(row=2, column=0, sticky='ew', pady=5, padx=5)

        deselect_all = ttk.Button(
            self,
            text='Deselect All',
            command=self.deselect_all_types
        )
        deselect_all.grid(row=3, column=0, sticky='ew', pady=5, padx=5)

        apply_button = ttk.Button(
            self,
            text='Apply to Plasmid',
            command=self.apply_filters
        )
        apply_button.grid(row=4, column=0, sticky='ew', pady=5, padx=5)

    def on_type_toggle(self, feature_type):
        """
        Handle type toggle change by updating all rows of that type.

        Sets the 'show' column value for all features matching
        feature_type to the current toggle state.

        Parameters
        ----------
        feature_type : str
            The feature type being toggled.
        """
        state = self.type_toggles[feature_type].get()

        # Update all rows of this type in the table
        if self.Easel.table and self.Easel.table.Table:
            table_df = self.Easel.table.Table.table_df

            for idx, row in table_df.iterrows():
                if row['type'].get() == feature_type:
                    # Update the 'show' column (last column before delete)
                    if 'show' in table_df.columns:
                        row['show'].set(state)

    def select_all_types(self):
        """Enable all feature type toggles."""
        for var in self.type_toggles.values():
            var.set(True)
            # Trigger callbacks manually
        for feature_type in self.type_toggles:
            self.on_type_toggle(feature_type)

    def deselect_all_types(self):
        """Disable all feature type toggles."""
        for var in self.type_toggles.values():
            var.set(False)
            # Trigger callbacks manually
        for feature_type in self.type_toggles:
            self.on_type_toggle(feature_type)

    def apply_filters(self):
        """Apply feature filters to the plasmid display."""
        if self.Easel.table:
            self.Easel.table.apply_to_plasmid()

if __name__ == '__main__':
    easel = PlasmidEasel()
    easel.mainloop()
