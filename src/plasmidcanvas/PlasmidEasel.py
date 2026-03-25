import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
import pandas as pd
from ttkbootstrap.constants import *
from ttkbootstrap.validation import *
from plasmidcanvas import Plasmid, draw_plasmid
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
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
        # edit = tk.Menu(menubar, tearoff=0)
        # menubar.add_cascade(label='Edit', menu=edit)
        #
        # edit.add_command(label='Cut', command=None, state=tk.DISABLED)
        # edit.add_command(label='Copy', command=None, state=tk.DISABLED)
        # edit.add_command(label='Paste', command=None, state=tk.DISABLED)
        # edit.add_command(label='Select All', command=None, state=tk.DISABLED)

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
        table = TablePanel(controlpannels)
        controlpannels.add(general, text="General")
        controlpannels.add(table, text="Table")
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
        self.PLASMID = draw_plasmid(self.PLASMID_DF, self.plasmid_title.get(), self.plasmid_bps.get(),
                                    self.plasmid_style.get())
        self.redraw_plasmid()
        self.focus_get().focus_set()


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


class TablePanel(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)


if __name__ == '__main__':
    easel = PlasmidEasel()
    easel.mainloop()
