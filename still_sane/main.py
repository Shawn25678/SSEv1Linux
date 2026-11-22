import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class StillSane(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="exile.stillsane.linux")

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self, title="Still Sane")
        window.set_default_size(960, 640)

        title = Gtk.Label(label="Still Sane")
        title.add_css_class("title")
        note = Gtk.Label(label="Linux")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(48)
        box.set_margin_start(48)
        box.set_margin_end(48)
        box.append(title)
        box.append(note)
        window.set_child(box)

        css = Gtk.CssProvider()
        css.load_from_string(
            "window { background: #1a1208; }"
            "label { color: #e8d7a8; font-size: 16px; }"
            "label.title { color: #f0d78c; font-size: 28px; }"
        )
        Gtk.StyleContext.add_provider_for_display(
            window.get_display(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        window.present()


def main():
    raise SystemExit(StillSane().run(None))


if __name__ == "__main__":
    main()
