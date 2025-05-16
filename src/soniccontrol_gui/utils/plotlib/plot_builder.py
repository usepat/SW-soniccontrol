from sonic_protocol.field_names import EFieldName
from soniccontrol_gui.utils.plotlib.plot import Plot

import matplotlib
import matplotlib.dates
import matplotlib.axes
import pandas as pd
import datetime


class PlotBuilder:
    # creates a timeplot for frequency, urms, irms and phase
    @staticmethod
    def create_timeplot_fuip(subplot: matplotlib.axes.Axes) -> Plot:
        plot = Plot(subplot, EFieldName.TIMESTAMP.value, "Time")
        plot._plot.xaxis.set_major_locator(matplotlib.dates.AutoDateLocator())
        plot._plot.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M:%S"))
        
        plot.add_axis("frequency_axis", "Frequency / Hz")
        plot.add_axis("phase_axis", "Phase / °")
        plot.add_axis("urms_axis", "U$_{RMS}$ / mV")
        plot.add_axis("irms_axis", "I$_{RMS}$ / mA")
        # for k, ax in plot._axes.items():
        #     print(f"{k:15s} → id = {id(ax)}")
        
        plot.add_line(
            EFieldName.FREQUENCY.value, 
            "frequency_axis",
            label="Frequency",
            color="black"
        )
        plot.add_line(
            EFieldName.PHASE.value, 
            "phase_axis",
            label="Phase",
            color="green",
        )
        plot.add_line(
            EFieldName.URMS.value, 
            "urms_axis",
            label="Urms",
            color="blue",
        )
        plot.add_line(
            EFieldName.IRMS.value, 
            "irms_axis",
            label="Irms",
            color="red",
        )

        plot.update_plot()
        plot.tight_layout()
        # for name, line in plot._lines.items():
        #     print(name, "→ axis:", line.axes is plot._axes[name + "_axis"], line.axes)
        return plot

    # creates a spectralplot for urms, irms and phase
    @staticmethod
    def create_spectralplot_uip(subplot: matplotlib.axes.Axes) -> Plot:
        plot = Plot(subplot, EFieldName.FREQUENCY.value, "Frequency / Hz")
        
        plot.add_axis("phase_axis", "Phase / °")
        plot.add_axis("urms_axis", "U$_{RMS}$ / mV")
        plot.add_axis("irms_axis", "I$_{RMS}$ / mA")
        
        plot.add_line(
            EFieldName.PHASE.value, 
            "phase_axis",
            label="Phase",
            color="green",
        )
        plot.add_line(
            EFieldName.URMS.value, 
            "urms_axis",
            label="Urms",
            color="blue",
        )
        plot.add_line(
            EFieldName.IRMS.value, 
            "irms_axis",
            label="Irms",
            color="red",
        )

        plot.update_plot()
        plot.tight_layout()

        return plot
