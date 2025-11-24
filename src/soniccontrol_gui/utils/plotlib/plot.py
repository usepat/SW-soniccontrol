import logging
import matplotlib
from matplotlib.figure import Figure
import pandas as pd

from typing import Dict, Optional
import datetime

from soniccontrol.events import Event, EventManager, PropertyChangeEvent


class Plot(EventManager):
    def __init__(self, subplot: matplotlib.axes.Axes, dataAttrNameXAxis: str, xlabel: str):
        super().__init__()
        self._plot: matplotlib.axes.Axes = subplot
        self._fig: Figure = subplot.get_figure()
        self._plot.set_xlabel(xlabel)
        self._plot.tick_params(axis="x", rotation=45)
        self._plot.spines['right'].set_visible(False)
        self._plot.spines['left'].set_visible(False)
        self._dataAttrNameXAxis = dataAttrNameXAxis
        self._lines: Dict[str, matplotlib.lines.Line2D] = {}
        self._axes: Dict[str, matplotlib.axes.Axes] = {}
        self._logger = logging.getLogger(__name__)
        self._plot.legend(
            loc="upper left",
            handles=[]
        )
        self._lineDefaultStyle: dict = {
            "lw": 2,
            "marker": "o",
            "markersize": 4,
            "linestyle": "-",
            "color": "blue"
        }

    @property
    def plot(self) -> matplotlib.axes.Axes:
        return self._plot
    
    @property
    def lines(self) -> matplotlib.lines.Line2D:
        return self._lines

    @property
    def lineDefaultStyle(self) -> dict:
        return self._lineDefaultStyle
    
    @lineDefaultStyle.setter
    def lineDefaultStyle(self, value) -> None:
        self._lineDefaultStyle = value


    def add_axis(self, axis_id: str, ylabel: str, **kwargs) -> None:
        if axis_id in self._axes:
            raise KeyError(f"There already exists a axis with this id {axis_id}")

        ax = self._plot.twinx()
        self._axes[axis_id] = ax

        ax.set_ylabel(ylabel)
        # set the axis to the right or left with an offset,
        # depending on how many axes are there already
        if len(self._axes) % 2 == 1:
            ax.spines['right'].set_visible(True)
            ax.spines['left'].set_visible(False)
            ax.yaxis.set_label_position("right")
            ax.yaxis.set_ticks_position("right")
            offset = ((len(self._axes) + 1) // 2) * 60
            ax.spines['right'].set_position(
                ("outward", offset)
            )
        else:
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(True)
            ax.yaxis.set_label_position("left")
            ax.yaxis.set_ticks_position("left")
            offset = (len(self._axes) // 2 - 1) * 60
            ax.spines['left'].set_position(
                ("outward", offset)
            )

    def tight_layout(self):
        self._fig.tight_layout()

    def add_line(self, dataAttrName: str, axis_id: str, **kwargs) -> None:
        if dataAttrName in self._lines:
            raise KeyError("There already exists a line for this attribute")
        
        linekwargs = self.lineDefaultStyle.copy()
        linekwargs.update(**kwargs)
        ax = self._axes[axis_id]
        (line, ) = ax.plot([], [], **linekwargs)

        self._lines[dataAttrName] = line

        all_handles = []
        for line in self._lines.values():
            all_handles.append(line)
        self._plot.legend(loc="upper left", handles=all_handles)


    def toggle_line(self, dataAttrName: str, isVisible: bool):
        self._lines[dataAttrName].set_visible(isVisible)
        self.emit(PropertyChangeEvent("plot", self._plot, self._plot))


    def update_plot(self):
        for _, axis in self._axes.items():
            axis.relim()
            axis.autoscale_view()

           

    def update_data(self, data: pd.DataFrame):
        #print(f"📦 update_data received timestamp dtype: {data['timestamp'].dtype} | id={id(data)}")
        if self._dataAttrNameXAxis in data.columns:
            timestamp_col = data[self._dataAttrNameXAxis]
            # If it's object, check for actual types inside
            if timestamp_col.dtype == 'object':
                self._logger.error("Timestamp column is of type object instead of type datetime64[ns]")
                raise TypeError("Timestamp column is of type object instead of type datetime64[ns]")

        for attrName, line in self._lines.items():
                # print(f"data[{self._dataAttrNameXAxis}]:{data[self._dataAttrNameXAxis]}    data[{attrName}]:{data[attrName]}")
                line.set_data(data[self._dataAttrNameXAxis], data[attrName])
        self.update_plot()
        self.emit(PropertyChangeEvent("plot", self._plot, self._plot))
