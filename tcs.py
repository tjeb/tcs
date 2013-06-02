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

import pygtk
pygtk.require('2.0')
import gtk
import ConfigParser
import os
import subprocess
import sys

class TCS:
    def quit(self, widget, data=None):
        gtk.Widget.destroy(self.window)

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def __init__(self, config, quit_button_at_start):
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    
        # When the window is given the "delete_event" signal (this is given
        # by the window manager, usually by the "close" option, or on the
        # titlebar), we ask it to call the delete_event () function
        # as defined above. The data passed to the callback
        # function is NULL and is ignored in the callback function.
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("configure_event", self.configure_event)
        
        # Here we connect the "destroy" event to a signal handler.  
        # This event occurs when we call gtk_widget_destroy() on the window,
        # or if we return FALSE in the "delete_event" callback.
        self.window.connect("destroy", self.destroy)
    
        # Sets the border width of the window.
        self.window.set_border_width(10)

        # This is where the actual buttons will go, the rest
        # is layout and spacing
        self.buttonbox = gtk.VBox(homogeneous=False, spacing=0)
        if quit_button_at_start:
            self.buttonbox.add(self.add_button("Quit", self.quit))
        self.add_config_buttons(config)
        if not quit_button_at_start:
            self.buttonbox.add(self.add_button("Quit", self.quit))
        self.buttonbox.show()

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
        self.window.fullscreen()
        self.set_background_image(config.get("TCS",
                                             "background_image"))
        self.window.show()
        self.window.present()

    def run_program(self, program):
        try:
            subprocess.call(program.split(' '))
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
        for section in config.sections():
            name = section
            if name == "TCS":
                # Skip the main config section
                continue
            data = { 'command' : config.get(section, "command")}
            self.set_data(data, config, section, "directory")
            self.set_data(data, config, section, "pre_command")
            self.set_data(data, config, section, "post_command")
            self.buttonbox.add(self.add_button(name, self.run_command,
                                               data))

    def add_button(self, text, callback, data=None):
        button = gtk.Button(text)
        button.connect("clicked", callback, data)
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
    parser.add_argument("--quit-button-at-start", action="store_true",
                        help="Make the quit button the first instead "
                             "of the last button in the list")
    args = parser.parse_args()

    if args.init:
        initialize_config_file(args.config_file)
    else:
        if os.path.exists(args.config_file):
            config = ConfigParser.ConfigParser()
            config.readfp(open(args.config_file))
            tcs = TCS(config, args.quit_button_at_start)
            tcs.main()
        else:
            print("Config file " + args.config_file +
                  " not found, please use --init to generate one")
