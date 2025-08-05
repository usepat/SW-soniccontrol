import matplotlib.figure
from soniccontrol_gui.views.measure.plotting import PlotView, PlotViewModel
from soniccontrol_gui.utils.plotlib.plot import Plot
from soniccontrol_gui.utils.plotlib.plot_builder import PlotBuilder 

import pandas as pd
import tkinter as tk
import matplotlib
matplotlib.use('TkAgg')


def main():    
    figure = matplotlib.figure.Figure(dpi=100)
    subplot = figure.add_subplot(1, 1, 1)
    plot = PlotBuilder.create_timeplot_fuip(subplot)

    filepath = "./logs/status_log.csv"
    data = pd.read_csv(filepath)
    data["TIMESTAMP"] = pd.to_datetime(data["TIMESTAMP"])
    plot.update_data(data)

    root = tk.Tk()
    plotViewModel = PlotViewModel(plot)
    plotView = PlotView(root, plotViewModel)
    plotView.grid()
    root.mainloop()


if __name__ == "__main__":
    main()
