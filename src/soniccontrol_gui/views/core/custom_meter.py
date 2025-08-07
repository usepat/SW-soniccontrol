import math
import tkinter as tk
from tkinter import EventType, ttk
from ttkbootstrap.constants import *

# meter imports
from PIL import Image, ImageTk, ImageDraw
from ttkbootstrap.style import Colors
from ttkbootstrap import utility
from ttkbootstrap.style import Bootstyle

M = 3 # meter image scale, higher number increases resolution

class CustomMeter(ttk.Frame):
    """A radial meter that can be used to show progress of long
    running operations or the amount of work completed; can also be
    used as a dial when set to `interactive=True`.

    This widget is very flexible. There are two primary meter types
    which can be set with the `metertype` parameter: 'full' and
    'semi', which shows the arc of the meter in a full or
    semi-circle. You can also customize the arc of the circle with
    the `arcrange` and `arcoffset` parameters.

    The meter indicator can be displayed as a solid color or with
    stripes using the `stripethickness` parameter. By default, the
    `stripethickness` is 0, which results in a solid meter
    indicator. A higher `stripethickness` results in larger wedges
    around the arc of the meter.

    Various text and label options exist. The center text and
    meter indicator is formatted with the `meterstyle` parameter.
    You can set text on the left and right of this center label
    using the `textleft` and `textright` parameters. This is most
    commonly used for '$', '%', or other such symbols.

    If you need access to the variables that update the meter, you
    you can access these via the `amountusedvar`, `amounttotalvar`,
    and the `labelvar`. The value of these properties can also be
    retrieved via the `configure` method.

    ![](../../assets/widgets/meter.gif)

    Examples:

        ```python
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import *

        app = ttk.Window()

        meter = ttk.Meter(
            metersize=180,
            padding=5,
            amountused=25,
            metertype="semi",
            subtext="miles per hour",
            interactive=True,
        )
        meter.pack()

        # update the amount used directly
        meter.configure(amountused = 50)

        # update the amount used with another widget
        entry = ttk.Entry(textvariable=meter.amountusedvar)
        entry.pack(fill=X)

        # increment the amount by 10 steps
        meter.step(10)

        # decrement the amount by 15 steps
        meter.step(-15)

        # update the subtext
        meter.configure(subtext="loading...")

        app.mainloop()
        ```
    """

    def __init__(
        self,
        master=None,
        bootstyle=DEFAULT,
        bootstyleneg=None,
        arcrange=None,
        arcoffset=None,
        amounttotal=None,
        amountmax=None,
        amountmin=None,
        amountused=0,
        wedgesize=0,
        metersize=200,
        metertype=FULL,
        meterthickness=10,
        showtext=True,
        interactive=False,
        stripethickness=0,
        textleft=None,
        textright=None,
        textfont="-size 20 -weight bold",
        subtext=None,
        subtextstyle=DEFAULT,
        subtextfont="-size 10",
        stepsize=1,
        step_full_range=True,
        **kwargs,
    ):
        """
        Parameters:

            master (Widget):
                The parent widget.

            arcrange (int):
                The range of the arc if degrees from start to end.

            arcoffset (int):
                The amount to offset the arc's starting position in degrees.
                0 is at 3 o'clock.

            amounttotal (int):
                The maximum value of the meter.

            amountused (int):
                The current value of the meter; displayed in a center label
                if the `showtext` property is set to True.

            wedgesize (int):
                Sets the length of the indicator wedge around the arc. If
                greater than 0, this wedge is set as an indicator centered
                on the current meter value.

            metersize (int):
                The meter is square. This represents the size of one side
                if the square as measured in screen units.

            bootstyle (str):
                Sets the indicator and center text color. One of primary,
                secondary, success, info, warning, danger, light, dark.

            metertype ('full', 'semi'):
                Displays the meter as a full circle or semi-circle.

            meterthickness (int):
                The thickness of the indicator.

            showtext (bool):
                Indicates whether to show the left, center, and right text
                labels on the meter.

            interactive (bool):
                Indicates that the user may adjust the meter value with
                mouse interaction.

            stripethickness (int):
                The indicator can be displayed as a solid band or as
                striped wedges around the arc. If the value is greater than
                0, the indicator changes from a solid to striped, where the
                value is the thickness of the stripes (or wedges).

            textleft (str):
                A short string inserted to the left of the center text.

            textright (str):
                A short string inserted to the right of the center text.

            textfont (Union[str, Font]):
                The font used to render the center text.

            subtext (str):
                Supplemental text that appears below the center text.

            subtextstyle (str):
                The bootstyle color of the subtext. One of primary,
                secondary, success, info, warning, danger, light, dark.
                The default color is Theme specific and is a lighter
                shade based on whether it is a 'light' or 'dark' theme.

            subtextfont (Union[str, Font]):
                The font used to render the subtext.

            stepsize (int):
                Sets the amount by which to change the meter indicator
                when incremented by mouse interaction.

            **kwargs:
                Other keyword arguments that are passed directly to the
                `Frame` widget that contains the meter components.
        """
        super().__init__(master=master, **kwargs)

        # widget variables
        self.amountusedvar = tk.DoubleVar(value=amountused)
        self.amountusedvar.trace_add("write", self._draw_meter)
        if (amountmin or amountmax) and amounttotal:
            raise DeprecationWarning("Using old and new code is not allowed")
        elif amounttotal:
            self.amountmaxvar = tk.IntVar(value=amounttotal)
            self.amountminvar = tk.IntVar(value=0)    
        else:
            self.amountmaxvar = tk.IntVar(value=amountmax)
            self.amountminvar = tk.IntVar(value=amountmin if amountmin else 0)

        self.invalidtextvar = tk.StringVar(value="--")
        self.labelvar = tk.StringVar(value=subtext)

        # misc settings
        self._set_arc_offset_range(metertype, arcoffset, arcrange)
        self._towardsmaximum = True
        self._metersize = utility.scale_size(self, metersize)
        self._meterthickness = utility.scale_size(self, meterthickness)
        self._stripethickness = stripethickness
        self._showtext = showtext
        self._wedgesize = wedgesize
        self._stepsize = stepsize        
        self._textleft = textleft
        self._textright = textright
        self._textfont = textfont
        self._subtext = subtext
        self._subtextfont = subtextfont
        self._subtextstyle = subtextstyle
        self._bootstyle = bootstyle
        self._boostyleneg = bootstyleneg if bootstyleneg  else bootstyle
        self._interactive = interactive
        self._step_full_range = step_full_range
        self._bindids = {}

        self._setup_widget()

    def _setup_widget(self):
        self.meterframe = ttk.Frame(
            master=self, width=self._metersize, height=self._metersize
        )
        self.indicator = ttk.Label(self.meterframe)
        self.textframe = ttk.Frame(self.meterframe)
        self.textleft = ttk.Label(
            master=self.textframe,
            text=self._textleft,
            font=self._subtextfont,
            bootstyle=(self._subtextstyle, "metersubtxt"),
            anchor=tk.S,
            padding=(0, 5),
        )
        self.textcenter = ttk.Label(
            master=self.textframe,
            textvariable=self.amountusedvar,
            bootstyle=(self._bootstyle, "meter"),
            font=self._textfont,
        )
        self.textright = ttk.Label(
            master=self.textframe,
            text=self._textright,
            font=self._subtextfont,
            bootstyle=(self._subtextstyle, "metersubtxt"),
            anchor=tk.S,
            padding=(0, 5),
        )
        self.subtext = ttk.Label(
            master=self.meterframe,
            text=self._subtext,
            bootstyle=(self._subtextstyle, "metersubtxt"),
            font=self._subtextfont,
        )

        self.bind("<<ThemeChanged>>", self._on_theme_change)
        self.bind("<<Configure>>", self._on_theme_change)
        self._set_interactive_bind()
        self._draw_base_image()
        self._draw_meter()

        # set widget geometery
        self.indicator.place(x=0, y=0)
        self.meterframe.pack()
        self._set_show_text()

    def _set_widget_colors(self):
        bootstyle = (self._bootstyle if self["amountused"] >= 0 else self._boostyleneg, "meter", "label")
        self.textcenter.configure(bootstyle=(self._bootstyle if self["amountused"] >= 0 else self._boostyleneg, "meter"))
        ttkstyle = Bootstyle.ttkstyle_name(string="-".join(bootstyle))
        textcolor = self._lookup_style_option(ttkstyle, "foreground")
        background = self._lookup_style_option(ttkstyle, "background")
        troughcolor = self._lookup_style_option(ttkstyle, "space")
        self._meterforeground = textcolor
        self._meterbackground = Colors.update_hsv(background, vd=-0.1)
        self._metertrough = troughcolor

    def _set_meter_text(self):
        """Setup and pack the widget labels in the appropriate order"""
        self._set_show_text()
        self._set_subtext()

    def _set_subtext(self):
        if self._subtextfont:
            if self._showtext:
                self.subtext.place(relx=0.5, rely=0.6, anchor=tk.CENTER)
            else:
                self.subtext.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def _set_show_text(self):
        self.textframe.pack_forget()
        self.textcenter.pack_forget()
        self.textleft.pack_forget()
        self.textright.pack_forget()
        self.subtext.pack_forget()

        if self._showtext:
            if self._subtext:
                self.textframe.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
            else:
                self.textframe.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self._set_text_left()
        self._set_text_center()
        self._set_text_right()
        self._set_subtext()

    def _set_text_left(self):
        if self._showtext and self._textleft:
            self.textleft.pack(side=tk.LEFT, fill=tk.Y)

    def _set_text_center(self):
        if self._showtext:
            self.textcenter.pack(side=tk.LEFT, fill=tk.Y)

    def _set_text_right(self):
        self.textright.configure(text=self._textright)
        if self._showtext and self._textright:
            self.textright.pack(side=tk.RIGHT, fill=tk.Y)

    def _set_interactive_bind(self):
        seq1 = "<B1-Motion>"
        seq2 = "<Button-1>"

        if self._interactive:
            self._bindids[seq1] = self.indicator.bind(
                seq1, self._on_dial_interact
            )
            self._bindids[seq2] = self.indicator.bind(
                seq2, self._on_dial_interact
            )
            return

        if seq1 in self._bindids:
            self.indicator.unbind(seq1, self._bindids.get(seq1))
            self.indicator.unbind(seq2, self._bindids.get(seq2))
            self._bindids.clear()

    def _set_arc_offset_range(self, metertype, arcoffset, arcrange):
        if metertype == SEMI:
            self._arcoffset = 135 if arcoffset is None else arcoffset
            self._arcrange = 270 if arcrange is None else arcrange
        else:
            self._arcoffset = -90 if arcoffset is None else arcoffset
            self._arcrange = 360 if arcrange is None else arcrange
        self._metertype = metertype

    def _draw_meter(self, *_):
        """Draw a meter"""
        self._set_widget_colors()
        img = self._base_image.copy()
        draw = ImageDraw.Draw(img)
        if self._stripethickness > 0:
            self._draw_striped_meter(draw)
        else:
            self._draw_solid_meter(draw)

        self._meterimage = ImageTk.PhotoImage(
            img.resize((self._metersize, self._metersize), Image.CUBIC)
        )
        self.indicator.configure(image=self._meterimage)

    def _draw_base_image(self):
        """Draw base image to be used for subsequent updates"""
        self._set_widget_colors()
        self._base_image = Image.new(
            mode="RGBA", size=(self._metersize * M, self._metersize * M)
        )
        draw = ImageDraw.Draw(self._base_image)

        x1 = y1 = self._metersize * M - 20
        width = self._meterthickness * M
        # striped meter
        if self._stripethickness > 0:
            _from = self._arcoffset
            _to = self._arcrange + self._arcoffset
            _step = 2 if self._stripethickness == 1 else self._stripethickness
            for x in range(_from, _to, _step):
                draw.arc(
                    xy=(0, 0, x1, y1),
                    start=x,
                    end=x + self._stripethickness - 1,
                    fill=self._metertrough,
                    width=width,
                )
        # solid meter
        else:
            draw.arc(
                xy=(0, 0, x1, y1),
                start=self._arcoffset,
                end=self._arcrange + self._arcoffset,
                fill=self._metertrough,
                width=width,
            )

    def _draw_solid_meter(self, draw: ImageDraw.Draw):
        """Draw a solid meter"""
        x1 = y1 = self._metersize * M - 20
        width = self._meterthickness * M

        if self._wedgesize > 0:
            meter_value = self._meter_value()
            draw.arc(
                xy=(0, 0, x1, y1),
                start=meter_value - self._wedgesize,
                end=meter_value + self._wedgesize,
                fill=self._meterforeground,
                width=width,
            )
        else:
            meter_value = self._meter_value()
            correction_factor = -90 if self["metertype"] == "semi" else 0
            start=self._arcoffset if self["amountused"] >= 0 else meter_value + correction_factor
            end=meter_value if self["amountused"] >= 0 else self._arcoffset + correction_factor
            draw.arc(
                xy=(0, 0, x1, y1),
                start=start,
                end=end,
                fill=self._meterforeground,
                width=width,
            )

    def _draw_striped_meter(self, draw: ImageDraw.Draw):
        """Draw a striped meter"""
        meter_value = self._meter_value()
        x1 = y1 = self._metersize * M - 20
        width = self._meterthickness * M

        if self._wedgesize > 0:
            draw.arc(
                xy=(0, 0, x1, y1),
                start=meter_value - self._wedgesize,
                end=meter_value + self._wedgesize,
                fill=self._meterforeground,
                width=width,
            )
        else:
            _from = self._arcoffset
            _to = meter_value - 1
            _step = self._stripethickness
            for x in range(_from, _to, _step):
                draw.arc(
                    xy=(0, 0, x1, y1),
                    start=x,
                    end=x + self._stripethickness - 1,
                    fill=self._meterforeground,
                    width=width,
                )

    def _meter_value(self) -> int:
        """Calculate the value to be used to draw the arc length of the
        progress meter."""
        if self["amountmin"] < 0:
            if self["amountused"] > 0:
                value = int(
                    (self["amountused"] / self["amountmax"]) * self._arcrange
                    + self._arcoffset
                )
            else:
                value = int(
                    -(self["amountused"] / self["amountmin"]) * self._arcrange
                    + self._arcoffset
                )
        else:
            value = int(
                (
                (self["amountused"] - self["amountmin"])
                 / (self["amountmax"] - self["amountmin"])
                ) 
                * self._arcrange
                + self._arcoffset
            )
        return value

    def _on_theme_change(self, *_):
        self._draw_base_image()
        self._draw_meter()

    def _angle_from_mouse(self, x, y):
        """Convert mouse (x, y) position to an angle in degrees from center."""
        center = self._metersize // 2
        dx = x - center
        dy = y - center
        angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        return angle

    
    def _angle_to_partial_value(self, angle, range_start, range_size, value_min, value_max):
        """Maps an angle between [range_start, range_start + range_size] to a value between [value_min, value_max]."""
        rel_angle = (angle - range_start + 360) % 360
        clamped = min(max(rel_angle, 0), range_size)
        return value_min + (clamped / range_size) * (value_max - value_min)




    def _on_dial_interact(self, e: tk.Event):
        angle = self._angle_from_mouse(e.x, e.y)
        min_val = self.amountminvar.get()
        max_val = self.amountmaxvar.get()
        arc_offset = self._arcoffset
        arc_range = self._arcrange

        if min_val < 0:
            # Two independent scenarios: negative (left) and positive (right)
            # Compute rel_angle within arc_range only
            rel_angle = (angle - arc_offset + 360) % 360
            rel_angle = min(max(rel_angle, 0), arc_range)
            rel_angle_norm = rel_angle / arc_range if arc_range else 0

            if e.type == EventType.ButtonPress:
                # Dynamically split arc: negative is left half, positive is right half, regardless of arc_offset/arcrange
                # rel_angle_norm in [0, 1): 0 is arc start, 0.5 is arc middle, 1 is arc end
                using_negative = rel_angle_norm >= 0.5
                self._last_dial_negative = using_negative
            else:
                # For drag, use last value's sign, but do not switch meter if value crosses zero
                using_negative = getattr(self, '_last_dial_negative', self.amountusedvar.get() < 0)


            if using_negative:
                # Negative meter: range is abs(min_val), from arc_offset+90 to arc_offset+270
                neg_start = (arc_offset) % 360
                value = self._angle_to_partial_value(
                    angle, neg_start, arc_range, min_val, 0
                )
            else:
                # Positive meter: range is max_val, from arc_offset+270 to arc_offset+90 (wraps around)
                pos_start = (arc_offset) % 360
                value = self._angle_to_partial_value(
                    angle, pos_start, arc_range, 0, max_val
                )
        else:
            # No negative range; treat as single meter
            value = self._angle_to_partial_value(
                angle, arc_offset, arc_range, min_val, max_val
            )

        # Snap to stepsize
        step = self._stepsize
        value = round(value / step) * step

        # Clamp value
        value = min(max(value, min_val), max_val)

        # Apply if changed
        if value != self.amountusedvar.get():
            self.amountusedvar.set(value)
            self._set_widget_colors()

    def _lookup_style_option(self, style: str, option: str):
        """Wrapper around the tcl style lookup command"""
        value = self.tk.call(
            "ttk::style", "lookup", style, "-%s" % option, None, None
        )
        return value

    def _configure_get(self, cnf):
        """Override the configuration get method"""
        if cnf == "arcrange":
            return self._arcrange
        elif cnf == "arcoffset":
            return self._arcoffset
        elif cnf == "amountmax":
            return self.amountmaxvar.get()
        elif cnf == "amountmin":
            return self.amountminvar.get()
        elif cnf == "amountused":
            return self.amountusedvar.get()
        elif cnf == "interactive":
            return self._interactive
        elif cnf == "subtextfont":
            return self._subtextfont
        elif cnf == "subtextstyle":
            return self._subtextstyle
        elif cnf == "subtext":
            return self._subtext
        elif cnf == "metersize":
            return self._metersize
        elif cnf == "bootstyle":
            return self._bootstyle
        elif cnf == "metertype":
            return self._metertype
        elif cnf == "meterthickness":
            return self._meterthickness
        elif cnf == "showtext":
            return self._showtext
        elif cnf == "stripethickness":
            return self._stripethickness
        elif cnf == "textleft":
            return self._textleft
        elif cnf == "textright":
            return self._textright
        elif cnf == "textfont":
            return self._textfont
        elif cnf == "wedgesize":
            return self._wedgesize
        elif cnf == "stepsize":
            return self._stepsize
        else:
            return super(ttk.Frame, self).configure(cnf)

    def _configure_set(self, **kwargs):
        """Override the configuration set method"""
        meter_text_changed = False
        if "amounttotal" in kwargs and ("amountmax" in kwargs or "amountmin" in kwargs):
            raise DeprecationWarning("Using deprecated and new functionality is not allowed")
        elif "amounttotal" in kwargs:
            amounttotal = kwargs.pop("amounttotal")
            self.amountminvar.set(0)
            self.amountmaxvar(amounttotal)
        else:
            if "amountmin" in kwargs:
                amountmin = kwargs.pop("amountmin")
                self.amountminvar.set(amountmin)
            if "amountmax" in kwargs:
                amountmax = kwargs.pop("amountmax")
                self.amountmaxvar(amountmax)
        if "arcrange" in kwargs:
            self._arcrange = kwargs.pop("arcrange")
        if "arcoffset" in kwargs:
            self._arcoffset = kwargs.pop("arcoffset")
        
        if "amountused" in kwargs:
            amountused = kwargs.pop("amountused")
            if amountused != amountused:
                self.invalidtextvar.set("--")
                self.amountusedvar.set(self.amountminvar.get() if self.amountminvar.get() >= 0 else 0)
                self.textcenter.configure(textvariable=self.invalidtextvar)
            elif amountused < self.amountminvar.get() or amountused > self.amountmaxvar.get():
                self.invalidtextvar.set("out of range")
                self.amountusedvar.set(self.amountminvar.get())
                self.textcenter.configure(textvariable=self.invalidtextvar)
            else:
                self.amountusedvar.set(amountused)
                self.textcenter.configure(textvariable=self.amountusedvar)
        if "interactive" in kwargs:
            self._interactive = kwargs.pop("interactive")
            self._set_interactive_bind()
        if "subtextfont" in kwargs:
            self._subtextfont = kwargs.pop("subtextfont")
            self.subtext.configure(font=self._subtextfont)
            self.textleft.configure(font=self._subtextfont)
            self.textright.configure(font=self._subtextfont)
        if "subtextstyle" in kwargs:
            self._subtextstyle = kwargs.pop("subtextstyle")
            self.subtext.configure(bootstyle=[self._subtextstyle, "meter"])
        if "metersize" in kwargs:
            self._metersize = utility.scale_size(kwargs.pop("metersize"))
            self.meterframe.configure(
                height=self._metersize, width=self._metersize
            )
        if "bootstyle" in kwargs:
            self._bootstyle = kwargs.pop("bootstyle")
            self.textcenter.configure(bootstyle=[self._bootstyle, "meter"])
        if "metertype" in kwargs:
            self._metertype = kwargs.pop("metertype")
        if "meterthickness" in kwargs:
            self._meterthickness = self.scale_size(
                kwargs.pop("meterthickness")
            )
        if "stripethickness" in kwargs:
            self._stripethickness = kwargs.pop("stripethickness")
        if "subtext" in kwargs:
            self._subtext = kwargs.pop("subtext")
            self.subtext.configure(text=self._subtext)
            meter_text_changed = True
        if "textleft" in kwargs:
            self._textleft = kwargs.pop("textleft")
            self.textleft.configure(text=self._textleft)
            meter_text_changed = True
        if "textright" in kwargs:
            self._textright = kwargs.pop("textright")
            meter_text_changed = True
        if "showtext" in kwargs:
            self._showtext = kwargs.pop("showtext")
            meter_text_changed = True
        if "textfont" in kwargs:
            self._textfont = kwargs.pop("textfont")
            self.textcenter.configure(font=self._textfont)
        if "wedgesize" in kwargs:
            self._wedgesize = kwargs.pop("wedgesize")
        if "stepsize" in kwargs:
            self._stepsize = kwargs.pop("stepsize")
        if meter_text_changed:
            self._set_meter_text()

        try:
            if self._metertype:
                self._set_arc_offset_range(
                    metertype=self._metertype,
                    arcoffset=self._arcoffset,
                    arcrange=self._arcrange,
                )
        except AttributeError:
            return

        self._draw_base_image()
        self._draw_meter()

        # pass remaining configurations to `ttk.Frame.configure`
        super(ttk.Frame, self).configure(**kwargs)

    def __getitem__(self, key: str):
        return self._configure_get(key)

    def __setitem__(self, key: str, value) -> None:
        self._configure_set(**{key: value})

    def configure(self, cnf=None, **kwargs):
        """Configure the options for this widget.

        Parameters:
            cnf (Dict[str, Any], optional):
                A dictionary of configuration options.

            **kwargs: Optional keyword arguments.
        """
        if cnf is not None:
            return self._configure_get(cnf)
        else:
            self._configure_set(**kwargs)

    def step(self, delta: float = 1.0):
        """
        Advance the indicator by *delta* and bounce at the correct limits.

        ────────────────────────────────────────────────────────────────
        MODE                       ACTIVE SPAN          BOUNCE LIMITS
        ────────────────────────────────────────────────────────────────
        full_range True  OR
        amountmin ≥ 0          [amountmin … amountmax]   amountmin / amountmax
        ────────────────────────────────────────────────────────────────
        split range
        current value > 0     [0 … amountmax]          0 / amountmax
        current value < 0     [amountmin … 0]          amountmin / 0
        current value == 0    span chosen from sign(delta)
        ────────────────────────────────────────────────────────────────
        Bounces never carry the needle across 0, but an explicit *delta*
        pointing through 0 can switch sides.
        """

        if delta == 0:
            return

        # ─── current values & config ─────────────────────────────────────
        val   = self.amountusedvar.get()
        vmin  = self.amountminvar.get()
        vmax  = self.amountmaxvar.get()
        full  = self._step_full_range or vmin >= 0

        # ----------------------------------------------------------------
        # 1.  Handle user-requested direction
        # ----------------------------------------------------------------
        user_sign = 1 if delta > 0 else -1
        if not hasattr(self, '_dir_user') or self._dir_user != user_sign:
            self._dir_user = user_sign             # remember caller’s wish
            self._dir      = user_sign             # start moving that way
        step_mag = abs(delta)
        step_val = step_mag * self._dir            # signed step for this call

        # ----------------------------------------------------------------
        # 2.  Decide which half-span is active
        # ----------------------------------------------------------------
        if full:
            low, high = vmin, vmax
        else:
            # Have we already chosen a half-span?
            if not hasattr(self, '_span_positive'):
                self._span_positive = val >= 0
            # If we are away from 0, lock the span to the current sign
            if val > 0:
                self._span_positive = True
            elif val < 0:
                self._span_positive = False
            # If val == 0, use the caller’s delta sign to pick the span
            if val == 0:
                self._span_positive = (user_sign > 0)

            low, high = (0, vmax) if self._span_positive else (vmin, 0)

        # ----------------------------------------------------------------
        # 3.  First advance and bounce at the *outer* limit only
        # ----------------------------------------------------------------
        new_val = val + step_val
        bounced = False

        if new_val > high:                 # hit the upper bound
            overs     = new_val - high
            new_val   = high - overs       # reflect inside
            self._dir = -1                 # now heading downward
            bounced   = True
        elif new_val < low:                # hit the lower bound
            overs     = low - new_val
            new_val   = low + overs        # reflect inside
            self._dir = 1                  # now heading upward
            bounced   = True

        # ----------------------------------------------------------------
        # 4.  Handle possible crossing of 0 in split-range mode
        #     • allowed  → if the caller’s delta sign points through 0
        #     • blocked → if it happened only because of a bounce
        # ----------------------------------------------------------------
        if not full and (( self._span_positive and new_val < 0 )
                        or (not self._span_positive and new_val > 0 )):
            intent_cross = ( self._span_positive and user_sign < 0 ) or \
                        ((not self._span_positive) and user_sign > 0)

            if intent_cross and not bounced:
                # user explicitly moved across 0 → switch span
                self._span_positive = not self._span_positive
                low, high = (0, vmax) if self._span_positive else (vmin, 0)
                # If the new value overshoots its new outer limit, bounce once
                if new_val > high:
                    new_val = high - (new_val - high)
                    self._dir = -1
                elif new_val < low:
                    new_val = low + (low - new_val)
                    self._dir = 1
            else:
                # crossing is from a bounce – reflect at 0
                new_val = -new_val           # mirror in place
                self._dir = -self._dir       # reverse again

        # ----------------------------------------------------------------
        # 5.  Clamp to span and apply
        # ----------------------------------------------------------------
        new_val = min(max(new_val, low), high)
        self._towardsmaximum = (self._dir > 0)     # backward-compat flag

        if new_val != val:
            self.amountusedvar.set(new_val)







