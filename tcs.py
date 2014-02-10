#!/usr/bin/python

# Copyright (C) 2013 Jelte Jansen
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import gtk
import os
import pango
import pygtk
import shlex
import subprocess
import sys

pygtk.require('2.0')

current_submenu = None

class MenuItem:
    ACTION_RUN=1
    ACTION_SUBMENU=2
    ACTION_BACK=3
    ACTION_QUIT=4

    """
    One item corresponds to one button on-screen.
    It can call:
    - a program (derived from config file)
    - a submenu (indirectly derived from config entries that have the
      submenu value set)
    - a special function (either back or quit)
    """
    def __init__(self, name, action, menu, directory=None, args=[]):
        self.name = name
        self.action = action
        self.menu = menu
        self.args = args

    def run(self, args=None):
        if self.action == MenuItem.ACTION_QUIT:
            sys.exit(0)
        elif self.action == MenuItem.ACTION_BACK:
            self.menu.back()
        elif self.action == MenuItem.ACTION_SUBMENU:
            self.menu.submenu(self.args[0])
        elif self.action == MenuItem.ACTION_RUN:
            for arg in self.args:
                try:
                    subprocess.call(shlex.split(program))
                except OSError as ose:
                    print("Error calling: " + program)
                    print(ose)

    def get_name(self):
        return self.name

    def __str__(self):
        return "[MenuItem] " + self.name + ": " + str(self.action)

class Menu:
    """
    Menu is a collection of menuitems and a way to navigate through
    them.
    """
    def __init__(self, tcs, name):
        self.tcs = tcs
        self.name = name
        self.items = []

    def back(self):
        if self.parent != None:
            self.tcs.showmenu(self.parent)

    def submenu(self, submenu):
        self.tcs.showmenu(submenu)

    def add_item(self, menuitem):
        self.items.append(menuitem)

    def get_items(self):
        return self.items

    def get_item_count(self):
        return len(self.items)

class TCS:
    def __init__(self, config):
        self.current_menu = ""
        self.parse_config_file(config)
        self.window = None
        self.show_window()
        self.show_buttons()

    def quit(self, widget, data=None):
        gtk.Widget.destroy(self.window)

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    # XX TODO: data=None can be removed?
    def button_gets_focus(self, widget, event, data=None):
        widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#EEEEEE'))
        label = widget.get_children()[0].get_children()[0]
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))

    # XX TODO: data=None can be removed?
    def button_loses_focus(self, widget, event, data=None):
        widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#707070'))
        label = widget.get_children()[0].get_children()[0]
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))

    def get_menu(self, menuname):
        print("[XX] get menu: " + menuname)
        if menuname in self.menus:
            cur_menu = self.menus[menuname]
        else:
            # If this is a new menu, add it to the list
            cur_menu = Menu(self, menuname)
            self.menus[menuname] = cur_menu
            # Also look up the parent and add a submenu item
            menu_parts = menuname.rpartition(".")[0]
            parent_menu = self.get_menu(menu_parts[0])
            parent_menu.add_item(MenuItem(menu_parts[2], MenuItem.ACTION_SUBMENU, parent_menu))
        print("[XX] returning menu")
        return cur_menu

    def parse_config_file(self, config):
        self.menus = {}
        # Add the top-level menu
        self.menus[""] = Menu(self, "")

        # Parse all entries
        for section in config.sections():
            name = section
            commands = []
            directory = None
            special_command = None
            submenu = ""

            if name == "TCS":
                # Skip the main config section
                continue
            for item in config.items(section):
                print("ITEM: " + str(item))
                if item[0] == 'command':
                    commands.append(item[1])
                elif item[0] == 'directory':
                    directory = item[1]
                elif item[0] == 'submenu':
                    submenu = item[1]

            cur_menu = self.get_menu(submenu)

            menuitem = MenuItem(name, MenuItem.ACTION_RUN, cur_menu, directory, commands)
            cur_menu.add_item(menuitem)
        
    def show_buttons(self):
        self.add_config_buttons(config)
        self.buttonbox.show()
        for child in self.buttonbox.children():
            child.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#707070'))
            child.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#EEEEEE'))
            child.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#EEEEEE'))
            child.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#FF0000'))
            label = child.get_children()[0].get_children()[0]
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
            child.modify_fg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#000000'))
            child.modify_fg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#000000'))
            child.modify_fg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#FFFFFF'))

    def show_window(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("configure_event", self.configure_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(10)

        # This is where the actual buttons will go, the rest
        # is layout and spacing
        self.buttonbox = gtk.VBox(homogeneous=False, spacing=0)
        # Layout:
        # main_vbox
        main_vbox = gtk.VBox(homogeneous=False, spacing=1)
        top_hbox = gtk.HBox(homogeneous=False, spacing=1)
        mid_hbox = gtk.HBox(homogeneous=False, spacing=1)
        midleft_vbox = gtk.VBox(homogeneous=False, spacing=1)
        midright_vbox = gtk.VBox(homogeneous=False, spacing=1)
        bot_hbox = gtk.HBox(homogeneous=False, spacing=1)
        
        main_vbox.add(top_hbox)
        main_vbox.add(mid_hbox)
        main_vbox.add(bot_hbox)
        
        mid_hbox.add(midleft_vbox)
        mid_hbox.add(self.buttonbox)
        mid_hbox.add(midright_vbox)
        self.window.add(main_vbox)
        top_hbox.show()
        mid_hbox.show()
        midleft_vbox.show()
        midright_vbox.show()
        bot_hbox.show()
        main_vbox.show()
        self.window.resize(gtk.gdk.screen_width(), gtk.gdk.screen_height())
        # TODO: enable fs again
        #self.window.fullscreen()
        self.set_background_image(config.get("TCS",
                                             "background_image"))
        self.window.show()
        self.window.present()

        gtk.gdk.display_get_default().warp_pointer(gtk.gdk.screen_get_default(), gtk.gdk.screen_width()-2, gtk.gdk.screen_height()-2)

    def run_program(self, program):
        # some special cases
        if program == "quit":
            self.quit(self)
            return
        try:
            subprocess.call(shlex.split(program))
        except OSError as ose:
            print("Error calling: " + program)
            print(ose)

    def run_command(self, widget, data=None):
        orig_directory = os.getcwd()
        if data['directory']:
            os.chdir(data['directory'])
        # make sure the post always gets run
        if data['pre_command']:
            self.run_program(data['pre_command'])
        self.run_program(data['command'])
        if data['post_command']:
            self.run_program(data['post_command'])
        os.chdir(orig_directory)
    
    def set_data(self, data, config, section, command):
        if config.has_option(section, command):
            data[command] = config.get(section, command)
        else:
            data[command] = None

    def add_config_buttons(self, config):
        mn = self.current_menu
        if mn == "":
            print("[XX] current menu: main")
        else:
            print("[XX] current menu: %s" % mn)
        menu = self.get_menu(mn)
        print("[XX] has %d elements" % menu.get_item_count())
        for old_button in self.buttonbox.get_children():
            self.buttonbox.remove(old_button)
        for menuitem in menu.get_items():
            print("[XX] item: " + str(menuitem))
            self.buttonbox.add(self.create_button(menuitem))
        #for section in config.sections():
        #    name = section
        #    if name == "TCS":
        #        # Skip the main config section
        #        continue
        #    data = { 'command' : config.get(section, "command")}
        #    self.set_data(data, config, section, "directory")
        #    self.set_data(data, config, section, "pre_command")
        #    self.set_data(data, config, section, "post_command")
        #    self.buttonbox.add(self.add_button(name, self.run_command,
        #                                       data))

    def create_button(self, menuitem):
        label = gtk.Label(menuitem.get_name())
        label.set_justify(gtk.JUSTIFY_CENTER)
        label.modify_font(pango.FontDescription("sans bold 20"))
        label.show()
        button_hbox = gtk.HBox(True, 0)
        button_hbox.pack_start(label, True, True, 0)
        button_hbox.show()
        button = gtk.Button()
        button.add(button_hbox)
        button.connect("clicked", menuitem.run)
        button.connect("focus-in-event", self.button_gets_focus)
        button.connect("focus-out-event", self.button_loses_focus)
        button.show()
        return button

    def old_XX_add_button(self, text, callback, data=None):
        label = gtk.Label(text)
        label.set_justify(gtk.JUSTIFY_CENTER)
        label.modify_font(pango.FontDescription("sans bold 20"))
        label.show()
        button_hbox = gtk.HBox(True, 0)
        button_hbox.pack_start(label, True, True, 0)
        button_hbox.show()
        button = gtk.Button()
        button.add(button_hbox)
        button.connect("clicked", callback, data)
        button.connect("focus-in-event", self.button_gets_focus, data)
        button.connect("focus-out-event", self.button_loses_focus, data)
        button.show()
        return button
    
    def set_background_image(self, filename):
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        self.pixmap, mask = self.pixbuf.render_pixmap_and_mask()

        self.window.set_app_paintable(gtk.TRUE)
        self.window.realize()
        self.window.window.set_back_pixmap(self.pixmap, False)

    def resize_background_image(self):
        src_width = self.pixbuf.get_width()
        src_height = self.pixbuf.get_height()
        dst_width, dst_height = self.window.window.get_size()

        # Scale preserving ratio
        scale = min(float(dst_width)/src_width, float(dst_height)/src_height)
        new_width = int(scale*src_width)
        new_height = int(scale*src_height)
        new_pixbuf = self.pixbuf.scale_simple(dst_width,
                                              dst_height,
                                              gtk.gdk.INTERP_BILINEAR)
        self.pixmap, mask = new_pixbuf.render_pixmap_and_mask()
        self.window.window.set_back_pixmap(self.pixmap, False)
    
    def configure_event(self, widget, event):
        self.resize_background_image()
        
    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

def add_command(config, section, settings):
    config.add_section(section)
    for name, value in settings:
        config.set(section, name, value)

def initialize_config_file(file_name):
    if os.path.exists(file_name):
        print("Error: %s already exists, please remove it "
              "or use a different file to initialize" % (file_name))
    else:
        # Initialize empty config file
        cp = ConfigParser.ConfigParser()
        add_command(cp, "TCS", [("background_image", 
                    os.getcwd() + 
                    '/images/default_background.jpg')])
        add_command(cp, "Gnome Terminal",
                    [("command", "gnome-terminal")])
        add_command(cp, "Example of three commands in a directory",
                    [("directory", "/home/foo/bar"),
                     ("pre_command", "command 1"),
                     ("command", "command 2"),
                     ("post_command", "command 3"),
                    ])
        add_command(cp, "Quit",
                    [("command", "quit")])
        with open(file_name, "w") as out:
            cp.write(out)
            print(file_name + " written")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true",
                        help="Initialize a configuration file")
    parser.add_argument("-c", "--config", dest="config_file",
                        default="tcs.conf",
                        help="use the given configuration file")
    args = parser.parse_args()

    if args.init:
        initialize_config_file(args.config_file)
    else:
        if os.path.exists(args.config_file):
            config = ConfigParser.ConfigParser()
            config.readfp(open(args.config_file))
            tcs = TCS(config)
            tcs.main()
        else:
            print("Config file " + args.config_file +
                  " not found, please use --init to generate one")
