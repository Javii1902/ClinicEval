def bind_mousewheel_scrolling(canvas):
    # bind_all is global, so only claim it while the pointer is actually
    # over this canvas and release it on <Leave>. Otherwise, whichever
    # scrollable tab's canvas the mouse left last "wins" the binding
    # permanently, and other tabs lose mousewheel scrolling entirely.
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux(event):
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

    def bind_wheel(event=None):
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", on_mousewheel_linux)
        canvas.bind_all("<Button-5>", on_mousewheel_linux)

    def unbind_wheel(event=None):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", bind_wheel)
    canvas.bind("<Leave>", unbind_wheel)


def bind_bounded_mousewheel_scrolling(widget, outer_canvas):
    # Scroll `widget` itself first; only once it's already at the top/bottom
    # in the direction being scrolled does the wheel fall through to scroll
    # `outer_canvas` (the enclosing page) instead. Bound directly on the
    # widget (not via bind_all) so it takes priority over the outer canvas's
    # own bind_all handler while the pointer is over this widget, and always
    # returns "break" so the two scrolls never both fire for one wheel tick.
    def at_top():
        top, _bottom = widget.yview()
        return top <= 0.0

    def at_bottom():
        _top, bottom = widget.yview()
        return bottom >= 1.0

    def scroll(delta_units):
        if delta_units < 0 and at_top():
            outer_canvas.yview_scroll(delta_units, "units")
        elif delta_units > 0 and at_bottom():
            outer_canvas.yview_scroll(delta_units, "units")
        else:
            widget.yview_scroll(delta_units, "units")
        return "break"

    def on_mousewheel(event):
        return scroll(int(-1 * (event.delta / 120)))

    def on_mousewheel_linux(event):
        if event.num == 4:
            return scroll(-1)
        if event.num == 5:
            return scroll(1)
        return None

    widget.bind("<MouseWheel>", on_mousewheel)
    widget.bind("<Button-4>", on_mousewheel_linux)
    widget.bind("<Button-5>", on_mousewheel_linux)
