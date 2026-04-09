import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
import pandas as pd
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji
from ttkbootstrap.validation import *
from plasmidcanvas import Plasmid, draw_plasmid
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
from functools import partial

from plasmidcanvas.DFTable import DFTable


#


class PlasmidEasel(ttk.Window):

    def __init__(self, **kw):
        super(PlasmidEasel, self).__init__(themename="pulse", **kw)
        self.title("PlasmidEasel")
        self.plasmid_title = tk.StringVar(None, "TORC")
        self.plasmid_bps = tk.IntVar(None, 1200)
        self.PLASMID: Plasmid = Plasmid(self.plasmid_title.get(), self.plasmid_bps.get())
        self.PLASMID_DF: pd.DataFrame = None
        self.SEPERATORS = {"tsv": "\t", "csv": ","}
        self.FIG = self.PLASMID.plot()
        self.fig_size = (3, 3)
        self.FIG.set_size_inches(self.fig_size[0], self.fig_size[1])
        self.canvas_figures = []
        self.plasmid_style = tk.StringVar(None, 'default')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.commands_log = [(None)]
        self.commands_pointer = 0

        # Creating Menubar
        menubar = tk.Menu(self)

        # Adding File Menu and commands
        file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file)
        file.add_command(label='Open...', command=self.open_csv)
        file.add_command(label='Save As...', command=self.save_canvas)
        file.add_separator()
        file.add_command(label='Exit', command=self.destroy)

        # Adding Edit Menu and commands
        self.edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Edit', menu=self.edit)

        self.edit.add_command(label='Undo', command=self.undo_command, accelerator='Ctrl+Z', state=tk.DISABLED)
        self.edit.add_command(label='Redo', command=self.redo_command, accelerator='Ctrl+Shift+Z', state=tk.DISABLED)
        self.bind('<Control-z>', self.undo_command, add=True)
        self.bind('<Control-Shift-z>', self.redo_command, add=True)


        # Adding Help Menu
        help_ = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_)
        help_.add_command(label='PlasmidEasel Docs', command=None, state=tk.DISABLED)

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
        controlpannels.add(general, text="General")
        controlpannels.add(self.table, text="Table")
        controlpannels.grid(row=0, column=1, sticky='nsew')
        controlpannels.columnconfigure(0, weight=1)
        controlpannels.rowconfigure(0, weight=1)

    def open_csv(self):
        filename = filedialog.askopenfilename(defaultextension='.csv',
                                              filetypes=[('CSV files', '*.csv'), ('TSV Files', '*.tsv')])
        file = open(filename, mode='r')
        contents = file.readlines()
        self.plasmid_bps.set(int(contents[1]))
        self.plasmid_title.set(contents[0].split()[0])
        # HEADER = contents[0].split()[1:]
        self.PLASMID_DF = pd.read_csv(filename, sep=self.SEPERATORS[filename[-3:]], header=2)
        self.table.load_data()
        self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                    self.plasmid_style.get())
        self.redraw_plasmid()

    def save_canvas(self):
        filename = filedialog.asksaveasfilename(filetypes=[('PNG files', '*.png'), ('SVG files', '*.svg'),
                                                           ('PDF files', '*.pdf'), ('JPG files', '*.jpg')])
        self.PLASMID.save_to_file(filename)

    def redraw_plasmid(self):
        self.FIG = self.PLASMID.plot()
        self.FIG.set_size_inches(self.fig_size[0], self.fig_size[1])
        self.canvas_figures[-1].get_tk_widget().pack_forget()
        new_canvas = FigureCanvasTkAgg(self.FIG, master=self)
        self.canvas_figures.append(new_canvas)
        new_canvas.draw_idle()
        new_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    def update_plasmid(self, *kw):
        self.command_add(("GENERAL_PLASMID_UPDATE", self.PLASMID, self.plasmid_title.get(), self.plasmid_bps.get()))
        self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                    self.plasmid_style.get())
        self.redraw_plasmid()
        self.focus_get().focus_set()

    def command_add(self, command: tuple):
        self.commands_pointer += 1
        if self.commands_pointer != len(self.commands_log)-1:
            self.commands_log= self.commands_log[:self.commands_pointer]
        self.commands_log.append(command)
        if len(self.commands_log) > 11:
            self.commands_pointer = 10
            self.commands_log.remove(self.commands_log[1])
        self.edit.entryconfig('Undo', state=tk.NORMAL)
        self.edit.entryconfig('Redo', state=tk.DISABLED)

    def undo_command(self):
        if self.commands_log[self.commands_pointer][0]:
            command = self.commands_log[self.commands_pointer]
            if command[0] == "GENERAL_PLASMID_UPDATE":
                self.PLASMID = command[1]
                self.redraw_plasmid()
                self.focus_get().focus_set()
            elif command[0] == "DELETE":
                self.table.RowPanel.undo_delete_row(command[1], command[2], command[3], command[4])
            elif command[0] == "ADD_ROW":
                ind = self.table.Table.table_df.shape[0] - 1
                self.table.RowPanel.delete_row(ind, log=False)
            self.commands_pointer -= 1
        self.edit.entryconfig('Redo', state=tk.NORMAL)
        if self.commands_pointer == 0:
            self.edit.entryconfig('Undo', state=tk.DISABLED)

    def redo_command(self):
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
                self.table.RowPanel.delete_row(command[1], log=False)
                pass
            elif command[0] == "ADD_ROW":
                self.table.add_row(log=False)


class GeneralPanel(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.Easel = self.master.master
        # Radio button style selection
        style = ttk.LabelFrame(self, text='Style')

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
        # Update plasmid with new labels
        apply = ttk.Button(self, command=self.Easel.update_plasmid, text='Apply')
        apply.grid(row=3, column=0, sticky='nsew', pady=5, padx=5)


class RowPanel(ttk.Frame):
    def __init__(self, master =None):
        super().__init__(master)
        self.Table: DFTable = self.master.Table
        if len(self.Table.table_df.columns) % 2:
            bootstyle = 'info-inverse'
        else:
            bootstyle = 'info'
        label = ttk.Label(self, text='delete?', bootstyle=bootstyle)
        label.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
        row_count = self.Table.table_df.shape[0]
        self.buttons = []
        self.delete_icon = Emoji.get("wastebasket")
        for i in range(row_count):
            delete_by_index = partial(self.delete_row, i)
            button = ttk.Button(self, text=self.delete_icon, bootstyle=(INFO, OUTLINE),
                                command=delete_by_index)
            button.grid(row=i+1, column=0, sticky='nsew', pady=4, padx=5)
            self.buttons.append(button)

    def delete_row(self, index, log=True):
        row_name = self.Table.table_df.iloc[index]["name"].get()
        command = ("DELETE", index, row_name, self.Table.rows.copy(), self.Table.table_df.copy())
        row_count = self.Table.table_df.shape[0]
        self.master.Table.delete_row(index+1, row_name)
        self.buttons[row_count-1].grid_forget()
        if log:
            self.master.Easel.command_add(command)

    def undo_delete_row(self, index, label, row=None, table=None):
        self.Table.undo_delete_row(index, label, row, table)
        self.add_row()

    def add_row(self):
        row_count = self.Table.table_df.shape[0]
        if len(self.buttons) >= row_count:
            self.buttons[row_count-1].grid(row=row_count, column=0, sticky='nsew', pady=4, padx=5)
        else:
            button = ttk.Button(self, text=self.delete_icon, bootstyle=(INFO, OUTLINE),
                                command=lambda: self.delete_row(row_count))
            button.grid(row=row_count, column=0, sticky='nsew', pady=4, padx=5)
            self.buttons.append(button)


class TablePanel(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.Easel: PlasmidEasel = self.master.master
        self.Table: DFTable = None
        self.delete_var: tk.StringVar = None
        self.undo_delete_button: ttk.Button = None
        self.delete_select: ttk.Combobox = None

    def load_data(self):
        if self.Table:
            self.Table.grid_forget()
        self.Table = DFTable(self, self.Easel.PLASMID_DF,
                             ['Int', 'String', 'String', 'Int', 'Int', 'Int', 'String'])
        self.Table.grid(row=0, column=0, sticky='nsew', pady=5, padx=5, columnspan=4)
        self.RowPanel = RowPanel(self)
        self.RowPanel.grid(row=0, column=4, sticky='ew', pady=5, padx=5)
        # Add buttons for save data, add row, delete row and undo delete
        apply_button = ttk.Button(self, text='Apply to Plasmid', command=self.apply_to_plasmid)
        apply_button.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        add_button = ttk.Button(self, text='Add Row', command=self.add_row)
        add_button.grid(row=1, column=1, sticky='nsew', pady=5, padx=5)
        save_button = ttk.Button(self, text='Save Data', command=self.save_data)
        save_button.grid(row=1, column=2, sticky='nsew', pady=5, padx=5)
        self.delete_var = ttk.StringVar()
        delete_frame = ttk.Labelframe(self, text='Delete', bootstyle='info')
        delete_frame.grid(row=1, column=3, sticky='nsew', pady=5, padx=5, columnspan=1)
        delete_button = ttk.Button(delete_frame, text='Delete Row', command=self.delete_row)
        delete_button.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)
        self.undo_delete_button = ttk.Button(delete_frame, text='Undo Delete', command=self.undo_delete, state=tk.DISABLED)
        self.undo_delete_button.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        self.delete_select = ttk.Combobox(delete_frame, textvariable=self.delete_var, bootstyle='info')
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        self.delete_select.grid(row=0, column=1, sticky='nsew', pady=5, padx=5)

    def add_row(self, log=True):
        self.Table.add_row()
        self.RowPanel.add_row()
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        if log:
            self.master.Easel.command_add(("ADD_ROW"))

    def delete_row(self, log=True):
        ind, label = self.delete_var.get().split('. ')
        ind = int(ind)
        command = ("DELETE", ind, label, self.Table.rows.copy(), self.Table.table_df.copy())
        if log:
            self.Easel.command_add(command)
        self.Table.delete_row(ind, label)
        self.undo_delete_button.config(state=tk.NORMAL)
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])

    def undo_delete(self, index=None, label=None):
        self.Table.undo_delete_row(index, label)
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])
        if len(self.Table.deleted_rows) == 0:
            self.undo_delete_button.config(state=tk.DISABLED)

    def apply_to_plasmid(self):
        self.Easel.PLASMID_DF = self.Table.update_table()
        self.Easel.update_plasmid()
        self.undo_delete_button.config(state=tk.DISABLED)
        self.delete_select['values']= tuple([str(ind.get())+'. '+label.get() for ind, label in zip(self.Table.table_df['index'],self.Table.table_df['name'])])

    def save_data(self):
        pass


if __name__ == '__main__':
    easel = PlasmidEasel()
    easel.mainloop()
