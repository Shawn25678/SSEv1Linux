import os
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from item import mod_class, rarity_class, read_item
from net import ninja_currency, trade_search
from state import BOSSES, load, save

EMPTY_ITEM = read_item("")
PAGES = (
    ("item", "Item"),
    ("trade", "Trade"),
    ("economy", "Economy"),
    ("bosses", "Bosses"),
    ("settings", "Settings"),
)


class StillSane(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="exile.stillsane.linux")
        self.state = load()
        self.item = EMPTY_ITEM
        self.nav_buttons = []
        self.kill_labels = {}

    def do_activate(self):
        if self.get_windows():
            self.get_windows()[0].present()
            return
        window = Gtk.ApplicationWindow(application=self, title="Still Sane")
        window.set_default_size(1100, 720)
        self.window = window
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Still Sane"))
        self.league_entry = Gtk.Entry()
        self.league_entry.set_placeholder_text("League")
        self.league_entry.set_text(self.state["league"])
        self.league_entry.set_width_chars(22)
        header.pack_end(self.league_entry)
        window.set_titlebar(header)
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        root.append(self._sidebar())
        root.append(self._stack())
        window.set_child(root)
        self._load_style(window)
        self.nav_buttons[0].set_active(True)
        window.present()

    def _sidebar(self):
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        side.add_css_class("sidebar")
        side.set_size_request(168, -1)
        for name, title in PAGES:
            button = Gtk.ToggleButton(label=title)
            button.add_css_class("nav")
            button.connect("toggled", self._on_nav, name)
            self.nav_buttons.append(button)
            side.append(button)
        return side

    def _stack(self):
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.add_named(self._item_page(), "item")
        self.stack.add_named(self._trade_page(), "trade")
        self.stack.add_named(self._economy_page(), "economy")
        self.stack.add_named(self._boss_page(), "bosses")
        self.stack.add_named(self._settings_page(), "settings")
        return self.stack

    def _item_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.add_css_class("page")
        self.name_label = Gtk.Label(label="No item", xalign=0)
        self.name_label.add_css_class("title")
        self.rarity_label = Gtk.Label(label="", xalign=0)
        self.rarity_label.add_css_class("muted")
        self.detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.detail)
        scroll.add_css_class("frame")
        buttons = Gtk.Box(spacing=8)
        read = Gtk.Button(label="Read clipboard")
        read.add_css_class("action")
        read.connect("clicked", self._read_clipboard)
        clear = Gtk.Button(label="Clear")
        clear.add_css_class("action")
        clear.connect("clicked", lambda *_: self._show_item(EMPTY_ITEM))
        buttons.append(read)
        buttons.append(clear)
        page.append(self.name_label)
        page.append(self.rarity_label)
        page.append(scroll)
        page.append(buttons)
        return page

    def _trade_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.add_css_class("page")
        self.trade_name = Gtk.Label(label="No item", xalign=0)
        self.trade_name.add_css_class("title")
        self.trade_status = Gtk.Label(
            label="Trade search stays off until Check trade is pressed.",
            xalign=0,
            wrap=True,
        )
        self.trade_status.add_css_class("muted")
        check = Gtk.Button(label="Check trade")
        check.add_css_class("action")
        check.set_halign(Gtk.Align.START)
        check.connect("clicked", self._check_trade)
        self.trade_rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.trade_rows)
        page.append(self.trade_name)
        page.append(check)
        page.append(self.trade_status)
        page.append(scroll)
        return page

    def _economy_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.add_css_class("page")
        heading = Gtk.Label(label="Economy", xalign=0)
        heading.add_css_class("title")
        refresh = Gtk.Button(label="Refresh poe.ninja")
        refresh.add_css_class("action")
        refresh.set_halign(Gtk.Align.START)
        refresh.connect("clicked", self._refresh_economy)
        self.economy_status = Gtk.Label(label="Currency prices in divine.", xalign=0)
        self.economy_status.add_css_class("muted")
        self.economy_rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.economy_rows)
        scroll.add_css_class("frame")
        page.append(heading)
        page.append(refresh)
        page.append(self.economy_status)
        page.append(scroll)
        return page

    def _boss_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.add_css_class("page")
        heading = Gtk.Label(label="Bosses", xalign=0)
        heading.add_css_class("title")
        page.append(heading)
        for name in BOSSES:
            row = Gtk.Box(spacing=10)
            label = Gtk.Label(label=name, xalign=0)
            label.set_hexpand(True)
            count = Gtk.Label(label=str(self.state["kills"].get(name, 0)))
            self.kill_labels[name] = count
            plus = Gtk.Button(label="+1")
            plus.add_css_class("action")
            plus.connect("clicked", self._add_kill, name)
            row.append(label)
            row.append(count)
            row.append(plus)
            page.append(row)
        return page

    def _settings_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.add_css_class("page")
        heading = Gtk.Label(label="Settings", xalign=0)
        heading.add_css_class("title")
        note = Gtk.Label(
            label="Path of Exile 2. The league box is used by Check trade and Economy.",
            xalign=0,
            wrap=True,
        )
        note.add_css_class("muted")
        save_btn = Gtk.Button(label="Save league")
        save_btn.add_css_class("action")
        save_btn.set_halign(Gtk.Align.START)
        save_btn.connect("clicked", self._save_league)
        self.settings_status = Gtk.Label(label="", xalign=0)
        self.settings_status.add_css_class("muted")
        page.append(heading)
        page.append(note)
        page.append(save_btn)
        page.append(self.settings_status)
        return page

    def _load_style(self, window):
        css = Gtk.CssProvider()
        css.load_from_path(os.path.join(os.path.dirname(__file__), "style.css"))
        Gtk.StyleContext.add_provider_for_display(
            window.get_display(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _on_nav(self, button, name):
        if not button.get_active():
            if not any(other.get_active() for other in self.nav_buttons):
                button.set_active(True)
            return
        for other in self.nav_buttons:
            if other is not button and other.get_active():
                other.set_active(False)
        self.stack.set_visible_child_name(name)

    def _league(self):
        return self.league_entry.get_text().strip()

    def _save_league(self, *_args):
        self.state["league"] = self._league()
        save(self.state)
        self.settings_status.set_label("League saved.")

    def _read_clipboard(self, *_args):
        clipboard = self.window.get_display().get_clipboard()
        clipboard.read_text_async(None, self._clipboard_ready)

    def _clipboard_ready(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result) or ""
        except Exception:
            text = ""
        self._show_item(read_item(text))

    def _show_item(self, item):
        self.item = item
        name = item["name"] or "No item"
        self._paint_name(self.name_label, name, item["rarity"])
        self._paint_name(self.trade_name, name, item["rarity"])
        bits = [item["rarity"]]
        if item["base"]:
            bits.append(item["base"])
        self.rarity_label.set_label(" · ".join(bit for bit in bits if bit))
        self._clear_box(self.detail)
        self._clear_box(self.trade_rows)
        self.trade_status.set_label("Trade search stays off until Check trade is pressed.")
        for label, value in item["props"].items():
            self.detail.append(self._line(f"{label}: {value}", "mod-plain"))
        for label, value in item["dps"].items():
            self.detail.append(self._line(f"{label} DPS: {value:.2f}", "mod-plain"))
        for line in item["requires"]:
            self.detail.append(self._line(line, "muted"))
        for line in item["mods"]:
            self.detail.append(self._line(line, mod_class(line)))
        for line in item["flags"]:
            self.detail.append(self._line(line, "rarity-unique"))
        if not item["name"]:
            self.detail.append(self._line("Copy an item, then Read clipboard.", "muted"))

    def _paint_name(self, label, name, rarity):
        label.set_label(name)
        for css in (
            "rarity-normal",
            "rarity-magic",
            "rarity-rare",
            "rarity-unique",
            "rarity-gem",
            "rarity-currency",
        ):
            label.remove_css_class(css)
        label.add_css_class(rarity_class(rarity) if rarity else "rarity-normal")

    def _line(self, text, css):
        label = Gtk.Label(label=text, xalign=0, wrap=True)
        label.add_css_class(css)
        return label

    def _clear_box(self, box):
        child = box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt

    def _check_trade(self, *_args):
        if not self.item["name"]:
            self.trade_status.set_label("Paste an item first.")
            return
        league = self._league()
        if not league:
            self.trade_status.set_label("Set a league in the top box first.")
            return
        self.trade_status.set_label("Checking trade...")
        item = self.item
        threading.Thread(target=self._trade_worker, args=(league, item), daemon=True).start()

    def _trade_worker(self, league, item):
        try:
            result = trade_search(league, item)
            GLib.idle_add(self._show_trade, result, "")
        except Exception as exc:
            GLib.idle_add(self._show_trade, None, str(exc))

    def _show_trade(self, result, error):
        self._clear_box(self.trade_rows)
        if error:
            self.trade_status.set_label(error)
            return False
        total = result.get("total", 0)
        self.trade_status.set_label(f"{total} listed.")
        for row in result.get("listings") or []:
            amount = row.get("amount")
            price = f"{amount} {row.get('currency') or ''}".strip()
            account = row.get("account") or ""
            text = price if not account else f"{price}    {account}"
            self.trade_rows.append(self._line(text or "No price", "mod-plain"))
        if total == 0:
            self.trade_rows.append(self._line("No listings.", "muted"))
        return False

    def _refresh_economy(self, *_args):
        league = self._league()
        if not league:
            self.economy_status.set_label("Set a league in the top box first.")
            return
        self.economy_status.set_label("Loading poe.ninja...")
        threading.Thread(target=self._economy_worker, args=(league,), daemon=True).start()

    def _economy_worker(self, league):
        try:
            rows = ninja_currency(league)
            GLib.idle_add(self._show_economy, rows, "")
        except Exception as exc:
            GLib.idle_add(self._show_economy, None, str(exc))

    def _show_economy(self, rows, error):
        self._clear_box(self.economy_rows)
        if error:
            self.economy_status.set_label(error)
            return False
        self.economy_status.set_label(f"{len(rows)} currency prices.")
        for row in rows:
            divine = row.get("divine")
            value = "" if divine is None else f"{divine}"
            self.economy_rows.append(self._line(f"{row['name']}    {value} divine", "mod-plain"))
        return False

    def _add_kill(self, _button, name):
        self.state["kills"][name] = int(self.state["kills"].get(name) or 0) + 1
        self.kill_labels[name].set_label(str(self.state["kills"][name]))
        self.state["league"] = self._league()
        save(self.state)


def main():
    raise SystemExit(StillSane().run(None))


if __name__ == "__main__":
    main()
