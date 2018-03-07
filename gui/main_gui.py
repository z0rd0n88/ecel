import gtk
import os
import subprocess
import definitions
import status_icon

import engine.collector
from gui.export_gui import ExportGUI
from gui.dss_gui import DssGUI
from gui.progress_bar import ProgressBar
from gui.progress_bar_details import ProgressBarDetails
from gui.plugin_config_gui import PluginConfigGUI
from _version import __version__

import time

class MainGUI(gtk.Window):
    def __init__(self, app_engine):
        super(MainGUI, self).__init__()
        self.engine = app_engine

        self.set_title("Evaluator-Centric and Extensible Logger v%s" % (__version__))
        self.set_size_request(500, 500)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete-event", self.hide_on_delete)

        # Create Tool Bar
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        tooltips = gtk.Tooltips()

        self.startall_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "start.png")))
        tooltips.set_tip(self.startall_button, "Start All Automatic Collectors")
        self.startall_button.connect("clicked", self.startall_collectors)

        self.stopall_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "stop.png")))
        tooltips.set_tip(self.stopall_button, "Stop All Automatic Collectors")
        self.stopall_button.connect("clicked", self.stopall_collectors)
        self.stopall_button.set_sensitive(False)

        separator1 = gtk.SeparatorToolItem()

        self.parseall_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "json.png")))
        tooltips.set_tip(self.parseall_button, "Execute All Parsers")
        self.parseall_button.connect("clicked", self.parse_all)

        separator2 = gtk.SeparatorToolItem()

        self.export_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "export.png")))
        tooltips.set_tip(self.export_button, "Export All Collector Data")
        self.export_button.connect("clicked", self.export_all)

        self.remove_data_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "delete.png")))
        tooltips.set_tip(self.remove_data_button, "Delete All Collector Data")
        self.remove_data_button.connect("clicked", self.delete_all)

        separator3 = gtk.SeparatorToolItem()

        self.collector_config_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "settings.png")))
        tooltips.set_tip(self.collector_config_button, "Collector Configurations")
        self.collector_config_button.connect("clicked", self.configure_collectors)
        
        separator4 = gtk.SeparatorToolItem()

        self.dss_button = gtk.ToolButton(gtk.image_new_from_file(os.path.join(definitions.ICONS_DIR, "model.png")))
        tooltips.set_tip(self.dss_button, "DSS")
        self.dss_button.connect("clicked", self.call_dss_module, app_engine.collectors)
        
        toolbar.insert(self.startall_button, 0)
        toolbar.insert(self.stopall_button, 1)
        toolbar.insert(separator1, 2)
        toolbar.insert(self.parseall_button, 3)
        toolbar.insert(separator2, 4)
        toolbar.insert(self.export_button, 5)
        toolbar.insert(self.remove_data_button, 6)
        toolbar.insert(separator3, 7)
        toolbar.insert(self.collector_config_button, 8)
        toolbar.insert(separator4, 9)
        toolbar.insert(self.dss_button, 10)

        vbox = gtk.VBox(False, 2)
        self.add(vbox)
        self.connect("destroy", self.close_all)

        # Create File Menu Bar
        # top_menu_bar = gtk.MenuBar()
        #
        # filemenu = gtk.Menu()
        # file_menu = gtk.MenuItem("File")
        # file_menu.set_submenu(filemenu)
        # top_menu_bar.append(file_menu)
        #
        # collectorConfiguration = gtk.MenuItem("Plugin Configurations")
        # collectorConfiguration.connect("activate", self.configure_collectors)
        #
        # exit = gtk.MenuItem("Exit")
        # exit.connect("activate", self.close_all)
        #
        # filemenu.append(collectorConfiguration)
        # filemenu.append(exit)
        #
        # vbox.pack_start(top_menu_bar)
        vbox.pack_start(toolbar)

        # Load collectors in window
        for i, collector in enumerate(app_engine.collectors):
            print "%d) %s" % (i, collector.name)
            #add collector to GUI
            vbox.pack_start(self.create_collector_bbox(collector), True, True, 5)
        #self.show_all()

        self.status_context_menu = status_icon.CustomSystemTrayIcon(app_engine, self)
        
        self.show_gui() # this line added to show GUI @ start DEBUG ONLY -- AF

    def configure_collectors(self, event):
        PluginConfigGUI(self, self.engine.collectors)

    def show_gui(self):
        self.present()
        self.show_all()

    def export_all(self, event):
        ExportGUI(self)

    def delete_all(self, event):
        if self.show_confirmation_dialog("Are you sure you want to delete all collector data (this cannot be undone)?"):
            remove_cmd = os.path.join(os.path.join(os.getcwd(), "scripts"), "cleanCollectorData.sh")
            subprocess.call(remove_cmd) #TODO: Change this to not call external script

    def create_collector_bbox(self, collector):
        frame = gtk.Frame(collector.name)

        if collector.is_enabled():
            layout = gtk.BUTTONBOX_SPREAD
            spacing = 10

            bbox = gtk.HButtonBox()
            bbox.set_border_width(1)
            bbox.set_layout(layout)
            bbox.set_spacing(spacing)
            frame.add(bbox)

            startCollectorButton = gtk.Button('Start Collector')
            startCollectorButton.connect("clicked", self.startIndividualCollector, collector)
            startCollectorButton.set_sensitive(not isinstance(collector, engine.collector.ManualCollector))
            bbox.add(startCollectorButton)

            stopCollectorButton = gtk.Button('Stop Collector')
            stopCollectorButton.connect("clicked", self.stopIndividualCollector, collector)
            stopCollectorButton.set_sensitive(not isinstance(collector, engine.collector.ManualCollector))
            bbox.add(stopCollectorButton)

            parseButton = gtk.Button('Parse Data')
            parseButton.connect("clicked", self.parser, collector)
            bbox.add(parseButton)
        else:
            label = gtk.Label("Collector Disabled")
            frame.add(label)

        return frame

    def startall_collectors(self, button):
        self.status_context_menu.tray_ind.set_icon(gtk.STOCK_MEDIA_RECORD)
        self.status_context_menu.startall_menu_item.set_sensitive(False)
        self.status_context_menu.stopall_menu_item.set_sensitive(True)
        self.startall_button.set_sensitive(False)
        self.stopall_button.set_sensitive(True)
        i = 0.0
        pb = ProgressBarDetails()
        pb.setValue(0.0)

        while gtk.events_pending():
            gtk.main_iteration()

        for collector in self.engine.collectors:
            if collector.is_enabled() and isinstance(collector, engine.collector.AutomaticCollector):
                collector.run()
            pb.setValue(i / len(self.engine.collectors))
            pb.appendText("processing "+collector.name)

            pb.pbar.set_text("Starting " + collector.name)
            while gtk.events_pending():
                gtk.main_iteration()
            i += 1
        pb.setValue(1.0)

        if not pb.emit("delete-event", gtk.gdk.Event(gtk.gdk.DELETE)):
            pb.destroy()

    def stopall_collectors(self, button):
        self.status_context_menu.tray_ind.set_icon(gtk.STOCK_NO)
        self.status_context_menu.stopall_menu_item.set_sensitive(False)
        self.status_context_menu.startall_menu_item.set_sensitive(True)
        self.stopall_button.set_sensitive(False)
        self.startall_button.set_sensitive(True)
        i = 0.0
        pb = ProgressBarDetails()
        pb.setValue(0.0)

        while gtk.events_pending():
            gtk.main_iteration()

        for collector in self.engine.collectors:
            if collector.is_enabled() and isinstance(collector, engine.collector.AutomaticCollector):
               collector.terminate()
            pb.setValue(i/len(self.engine.collectors))
            pb.appendText("stopping "+collector.name)
            while gtk.events_pending():
                gtk.main_iteration()
            i += 1
        pb.setValue(1.0)

        if not pb.emit("delete-event", gtk.gdk.Event(gtk.gdk.DELETE)):
            pb.destroy()

    def call_dss_module(self, event, collectors):
        DssGUI(self, collectors)
    
    def parse_all(self, event):
        for collector in self.engine.collectors:
            collector.parser.parse()
#        alert = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
#                                       gtk.BUTTONS_CLOSE, "Parsing complete")
#        alert.run()
#        alert.destroy()


    def close_all(self, event):
        for collector in self.engine.collectors:
            if collector.is_enabled:
               collector.terminate()
        os._exit(0)

    def parser(self, event, collector):
        collector.parser.parse()

    def stopIndividualCollector(self, event, collector):
        collector.terminate()

    def startIndividualCollector(self, event, collector):
        collector.run()

    def show_confirmation_dialog(self, msg):
        dialog = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                                      gtk.BUTTONS_YES_NO, msg)
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_YES:
            return True

        return False
