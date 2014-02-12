#!/usr/bin/python
"""
TjebCadeStarter, a simplistic frontend for arcade machines.
Or, if you will, a very simple full-screen button menu.
"""
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

#
# Callbacks for gtk events
#
def cb_destroy(widget, data=None):
    """
    Destroy the window
    """
    gtk.main_quit()

def cb_button_gets_focus(widget, event):
    """
    Change colors when button receives focus
    """
    widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#EEEEEE'))
    label = widget.get_children()[0].get_children()[0]
    label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))

def cb_button_loses_focus(widget, event):
    """
    Change colors when button loses focus
    """
    widget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#707070'))
    label = widget.get_children()[0].get_children()[0]
    label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
#
# End of callbacks for GTK events
#

#
# Helper functions
#
def create_button(menuitem):
    """
    Create a button from the given menuitem
    """
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
    button.connect("focus-in-event", cb_button_gets_focus)
    button.connect("focus-out-event", cb_button_loses_focus)
    button.show()
    return button
#
# End of helper functions
#

class MenuItem:
    """
    A single menu item.

    One item corresponds to one button on-screen.

    It can call:
    - a program (derived from config file)
    - a submenu (indirectly derived from config entries that have the
      submenu value set)
    - a special function (either back or quit)
    """
    
    ACTION_RUN = 1
    ACTION_SUBMENU = 2
    ACTION_BACK = 3
    ACTION_QUIT = 4

    def __init__(self, name, action, menu, directory=None, arguments=None):
        """
        name (string): the name that is shown on screen.
        action (int): an ACTION_TYPE which tells the button how to behave
        menu (Menu): the menu this button belongs to
        directory (string): UNUSED ATM, directory to execute the commands in
        arguments (list): either a list of commands, or a 1-element list of the submenu (Menu)
        """
        self.name = name
        self.action = action
        self.menu = menu
        self.directory = directory
        if arguments is None:
            self.args = []
        else:
            self.args = arguments

    def run(self, _):
        """
        Run the action defined by this menu item.
        """
        if self.action == MenuItem.ACTION_QUIT:
            sys.exit(0)
        elif self.action == MenuItem.ACTION_BACK:
            self.menu.back()
        elif self.action == MenuItem.ACTION_SUBMENU:
            self.menu.submenu(self.args[0])
        elif self.action == MenuItem.ACTION_RUN:
            for arg in self.args:
                try:
                    subprocess.call(shlex.split(arg))
                except OSError as ose:
                    print("Error calling: " + arg)
                    print(ose)

    def get_name(self):
        """
        Returns the name of this menu item
        """
        return self.name

    def __str__(self):
        """
        String representation, of the form name: action_type (int)
        """
        return "[MenuItem] " + self.name + ": " + str(self.action)

class Menu:
    """
    Menu is a collection of menuitems and a way to navigate through
    them.
    """
    def __init__(self, main_tcs, name, parent=None):
        self.tcs = main_tcs
        self.name = name
        self.items = []
        self.parent = parent

    def back(self):
        """
        Make TCS go to the parent of this menu
        """
        if self.parent != None:
            self.tcs.show_menu(self.parent)

    def submenu(self, submenu):
        """
        Go to the given submenu (a Menu)
        """
        self.tcs.show_menu(submenu)

    def add_item(self, menuitem):
        """
        Add a MenuItem to this menu
        """
        self.items.append(menuitem)

    def get_items(self):
        """
        Returns a list of all the MenuItems in this menu
        """
        return self.items

    def get_item_count(self):
        """
        Returns the number of MenuItems this menu has
        """
        return len(self.items)

class TCS:
    """
    Main TjebCadeStarter class. Shows the 'window' and the menus
    """
    def __init__(self, tcs_config):
        self.config = tcs_config
        self.menus = {}
        self.parse_config_file()
        self.current_menu = self.get_menu("")

        self.pixbuf = None
        self.pixmap = None
        self.buttonbox = None
        self.window = None

    def show_menu(self, menu):
        """
        Show the given Menu
        """
        self.current_menu = menu
        self.show_buttons()

    def get_menu(self, menuname):
        """
        Returns the menu with the given name.
        If the menu doesn't exist yet, it is created with a back
        button, and with a new menuitem in its parent
        Menu definitions are of the form
        'parent_menu.sub_menu.subsub_menu'
        """
        if menuname in self.menus:
            cur_menu = self.menus[menuname]
        else:
            # If this is a new menu, add it to the list
            # First look up the parent and add a submenu item
            menu_parts = menuname.rpartition(".")
            parent_menu = self.get_menu(menu_parts[0])

            cur_menu = Menu(self, menuname, parent_menu)
            parent_menu.add_item(MenuItem(menu_parts[2],
                                          MenuItem.ACTION_SUBMENU,
                                          parent_menu,
                                          arguments=[cur_menu]))
            # Add a back button
            cur_menu.add_item(MenuItem("Back", MenuItem.ACTION_BACK, cur_menu))

            # Add it to the total list of menus
            self.menus[menuname] = cur_menu

        return cur_menu

    def parse_config_file(self):
        """
        Parse the main config file, and create Menus and MenuItems
        from it
        """
        # Add the top-level menu
        self.menus[""] = Menu(self, "")

        # Parse all entries
        for section in self.config.sections():
            name = section
            commands = []
            directory = None
            submenu = ""
            item_type = MenuItem.ACTION_RUN

            if name == "TCS":
                # Skip the main config section
                continue
            name_parts = name.rpartition(".")
            submenu = name_parts[0]
            for item in self.config.items(section):
                if item[0] == 'command':
                    if item[1] == 'quit':
                        item_type = MenuItem.ACTION_QUIT
                    else:
                        commands.append(item[1])
                elif item[0] == 'directory':
                    directory = item[1]
                elif item[0] == 'submenu':
                    submenu = item[1]

            cur_menu = self.get_menu(submenu)

            menuitem = MenuItem(name_parts[2], item_type,
                                cur_menu, directory, commands)
            cur_menu.add_item(menuitem)
        
    def show_buttons(self):
        """
        Show the buttons window element
        """
        self.add_config_buttons()
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
        """
        Create and show the main window
        """
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #self.window.connect("delete_event", self.delete_event)
        self.window.connect("configure_event", self.cb_configure_event)
        self.window.connect("destroy", cb_destroy)
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
        #self.window.fullscreen()
        self.set_background_image(self.config.get("TCS",
                                                  "background_image"))
        self.window.show()
        self.window.present()

        gtk.gdk.display_get_default().warp_pointer(gtk.gdk.screen_get_default(),
                                                   gtk.gdk.screen_width()-2,
                                                   gtk.gdk.screen_height()-2)

    def add_config_buttons(self):
        """
        Add the buttons to the buttonbox
        """
        for old_button in self.buttonbox.get_children():
            self.buttonbox.remove(old_button)
        for menuitem in self.current_menu.get_items():
            self.buttonbox.add(create_button(menuitem))


    def set_background_image(self, filename):
        """
        Set the background image for the main window
        """
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        self.pixmap, _ = self.pixbuf.render_pixmap_and_mask()

        self.window.set_app_paintable(gtk.TRUE)
        self.window.realize()
        self.window.window.set_back_pixmap(self.pixmap, False)

    def resize_background_image(self):
        """
        Resize the background image to the window size
        """
        dst_width, dst_height = self.window.window.get_size()

        new_pixbuf = self.pixbuf.scale_simple(dst_width,
                                              dst_height,
                                              gtk.gdk.INTERP_BILINEAR)
        pixmap, _ = new_pixbuf.render_pixmap_and_mask()
        self.window.window.set_back_pixmap(pixmap, False)
    
    def cb_configure_event(self, widget, event):
        """
        Configure event callback
        """
        self.resize_background_image()
        
def add_command(config, section, settings):
    """
    Config initializer on --init; add a command
    """
    config.add_section(section)
    for name, value in settings:
        config.set(section, name, value)

def initialize_config_file(file_name):
    """
    Config initializer on --init, initialize an example config file
    """
    if os.path.exists(file_name):
        print("Error: %s already exists, please remove it "
              "or use a different file to initialize" % (file_name))
    else:
        # Initialize empty config file
        confp = ConfigParser.ConfigParser()
        add_command(confp, "TCS", [("background_image", 
                    os.getcwd() + 
                    '/images/default_background.jpg')])
        add_command(confp, "Gnome Terminal",
                    [("command", "gnome-terminal")])
        add_command(confp, "Example of three commands in a directory",
                    [("directory", "/home/foo/bar"),
                     ("pre_command", "command 1"),
                     ("command", "command 2"),
                     ("post_command", "command 3"),
                    ])
        add_command(confp, "Quit",
                    [("command", "quit")])
        with open(file_name, "w") as out:
            confp.write(out)
            print(file_name + " written")

def main():
    """
    Main function, run a TCS instance.
    """
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
            tcs.show_window()
            tcs.show_menu(tcs.current_menu)
            gtk.main()
        else:
            print("Config file " + args.config_file +
                  " not found, please use --init to generate one")

if __name__ == "__main__":
    main()
