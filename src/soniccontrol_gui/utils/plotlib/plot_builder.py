from sonic_protocol.field_names import EFieldName
from soniccontrol_gui.utils.plotlib.plot import Plot

import matplotlib
import matplotlib.dates
import matplotlib.axes


class PlotBuilder:
    # creates a timeplot for frequency, urms, irms and phase
    @staticmethod
    def create_timeplot_fuip(subplot: matplotlib.axes.Axes) -> Plot:
        plot = Plot(subplot, EFieldName.TIMESTAMP.name, "Time")
        plot._plot.xaxis.set_major_locator(matplotlib.dates.AutoDateLocator())
        plot._plot.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M:%S"))
        
        plot.add_axis("frequency_axis", "Frequency / Hz")
        plot.add_axis("phase_axis", "Phase / c°")
        plot.add_axis("urms_axis", "U$_{RMS}$ / mV")
        plot.add_axis("irms_axis", "I$_{RMS}$ / mA")

        plot.add_line(
            EFieldName.FREQUENCY.name, 
            "frequency_axis",
            label="Frequency",
            color="black"
        )
        plot.add_line(
            EFieldName.PHASE.name, 
            "phase_axis",
            label="Phase",
            color="green",
        )
        plot.add_line(
            EFieldName.URMS.name, 
            "urms_axis",
            label="Urms",
            color="blue",
        )
        plot.add_line(
            EFieldName.IRMS.name, 
            "irms_axis",
            label="Irms",
            color="red",
        )

        plot.update_plot()
        plot.tight_layout()
        
        return plot
    
    @staticmethod
    def create_timeplot_irms(subplot: matplotlib.axes.Axes) -> Plot:
        plot = Plot(subplot, EFieldName.TIMESTAMP.name, "Time")
        plot._plot.xaxis.set_major_locator(matplotlib.dates.AutoDateLocator())
        plot._plot.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M:%S"))
        
        plot.add_axis("irms_axis", "I$_{RMS}$ / mA")
        plot.add_axis("ipp_axis", "I$_{PP}$ / mA")

        plot.add_line(
            EFieldName.IRMS.name, 
            "irms_axis",
            label="Irms",
            color="red",
        )


        plot.add_line(
            EFieldName.IPP.name, 
            "ipp_axis",
            label="Ipp",
            color="blue",
        )

        plot.update_plot()
        plot.tight_layout()

        return plot

    # creates a spectralplot for urms, irms and phase
    @staticmethod
    def create_spectralplot_uip(subplot: matplotlib.axes.Axes) -> Plot:
        plot = Plot(subplot, EFieldName.FREQUENCY.name, "Frequency / Hz")
        
        plot.add_axis("phase_axis", "Phase / c°")
        plot.add_axis("urms_axis", "U$_{RMS}$ / mV")
        plot.add_axis("irms_axis", "I$_{RMS}$ / mA")
        
        plot.add_line(
            EFieldName.PHASE.name, 
            "phase_axis",
            label="Phase",
            color="green",
        )
        plot.add_line(
            EFieldName.URMS.name, 
            "urms_axis",
            label="Urms",
            color="blue",
        )
        plot.add_line(
            EFieldName.IRMS.name, 
            "irms_axis",
            label="Irms",
            color="red",
        )

        plot.update_plot()
        plot.tight_layout()

        return plot
