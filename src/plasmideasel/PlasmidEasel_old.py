import os

from kivy.app import App
from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from plasmideasel import Plasmid
from kivy.lang import Builder


PLASMID = None

kivy_string = """
BoxLayout:
    orientation: 'horizontal'
    Easel:
        id:easel
    TabbedPanel:
        do_default_tab: False
        TabbedPanelItem:
            text: "Plasmid"
            PlasmidProperties:
        TabbedPanelItem:
            text: "Add Feature"
            AddFeature:
<Easel>:
    plasmid: plasmid_img
    Image:
        id: plasmid_img
        source: 'temp.png'
        size: root.size
<PlasmidProperties>:
    id: interface
    orientation: 'vertical'
    BoxLayout:
        id: style
        orientation: 'horizontal'
        BoxLayout:
            orientation: 'vertical'
            CheckBox:
                id: style_default
                group: 'plasmid_style'
                on_active: interface.set_default()
            Label:
                text: 'Default'
        BoxLayout:
            orientation: 'vertical'
            CheckBox:
                id: style_minimalist
                group: 'plasmid_style'
                on_active: interface.set_minimalist()
            Label:
                text: 'Minimalist'        
    BoxLayout:
        id: Name
        orientation: 'horizontal'
        Label:
            id: label
            text: "Plasmid name"
        PlasmidName:
            id: input_plasmid_name
    BoxLayout:
        id: Size
        orientation: 'horizontal'
        Label:
            id: label
            text: "Number of base pairs"
        PlasmidSize:
            id: input_base_pairs
    Button:
        id: apply
        text: "Apply"
        on_release: interface.update_plasmid()

<AddFeature>:
    id: interface
    orientation: 'vertical'
    BoxLayout:
        id: Name
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            CheckBox:
                id: arrow_cb
                text: 'Arrow Feature'
                group: 'feature_type'
            Label:
                text: 'Arrow Feature'
        BoxLayout:
            orientation: 'horizontal'
            CheckBox:
                id: restriction_cb
                text: 'Restriction Site'
                group: 'feature_type'
            Label:
                text: 'Restriction Site'
        BoxLayout:
            orientation: 'horizontal'
            CheckBox:
                id: rectangle_cb
                text: 'Rectangle Feature'
                group: 'feature_type'
            Label:
                text:'Rectangle Feature'

<PlasmidSize>:

<PlasmidName>:
    
"""

# TODO: Add screen manager
# TODO: Add start screen setting plasmid name and length to generates initial image and open main edit screen
# TODO: Add ability to save plasmid to plasmid settings
# TODO: Turn add feature into a scroll with apply at the bottom of each section so they have accurate parameters to set


class Easel(Label):
    """

    """
    plasmid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Easel, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def update(self, *args):
        self.plasmid.reload()


class PlasmidProperties(BoxLayout):
    def __init__(self, **kwargs):
        super(PlasmidProperties, self).__init__(**kwargs)

    def update_plasmid(self):
        for child1 in self.children:
            for child2 in child1.children:
                try:
                    child2.update()
                except AttributeError:
                    pass

    @staticmethod
    def set_minimalist():
        PLASMID.set_plasmid_line_width_sf(0.1)
        PLASMID.set_color('black')
        PLASMID.set_tick_color('black')

    @staticmethod
    def set_default(self):
        PLASMID.set_plasmid_line_width_sf(1)
        PLASMID.set_color('gray')
        PLASMID.set_tick_color('gray')


class AddFeature(BoxLayout):
    def __init__(self, **kwargs):
        super(AddFeature, self).__init__(**kwargs)


class PlasmidName(TextInput):

    def __init__(self, **kwargs):
        super(PlasmidName, self).__init__(**kwargs)
        self.text = PLASMID.name

    def update(self):
        PLASMID.set_name(self.text)
        PLASMID.save_to_file(os.path.join(os.path.dirname(__file__), "temp.png"))


class PlasmidSize(TextInput):

    def __init__(self, **kwargs):
        super(PlasmidSize, self).__init__(**kwargs)
        self.text = str(PLASMID.base_pairs)

    def update(self):
        try:
            num = int(self.text)
        except ValueError:
            # sort a popup to request valid input
            num = PLASMID.base_pairs
            popup = Popup(title="Base pair size",
                          content=Label(
                              text='Base pair size must be integer greater than 0. Base pair size remains unchanged.',
                              text_size=(self.width*1.5, None),
                              size_hint=(1, 1)),
                          size_hint=(.6, .6),)
            popup.open()
            self.text = str(num)
        PLASMID.base_pairs = (num)
        PLASMID.save_to_file(os.path.join(os.path.dirname(__file__), "temp.png"))


class PlasmidEaselApp(App):
    def build(self):
        # TODO: setup as app after sorting rest of interface
        return Builder.load_string(kivy_string)


if __name__ == '__main__':
    PLASMID = Plasmid("pBR322_1", 4361)
    PLASMID.save_to_file(os.path.join(os.path.dirname(__file__), "temp.png"))
    runTouchApp(Builder.load_string(kivy_string))