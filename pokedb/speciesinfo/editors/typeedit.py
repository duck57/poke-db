#!/usr/bin/env python3
# coding=UTF-8
# -*- coding: UTF-8 -*-
# vim: set fileencoding=UTF-8 :


import os
import sys
from asciimatics.widgets import (
    Frame,
    Layout,
    Divider,
    Text,
    Button,
    Widget,
    MultiColumnListBox,
)
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

    # Setup django
    import django

    django.setup()

    # now you can import your ORM models
    from speciesinfo.models import Type
    from nestlist.utils import nested_dict


class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            on_load=self._reload_list,
            hover_focus=True,
            title="Type List",
        )
        # Save off the model that accesses the types database.
        self._model = model

        # Create the form for displaying the list of types.
        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            ["<0", ">5"],
            model.get_summary(),
            name="types",
            on_change=self._on_pick,
            on_select=self._edit,
        )
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        # layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._delete_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()
        self._delete_button.disabled = True

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None

    def _reload_list(self, new_value=None):
        self._list_view.options = self._model.get_summary()
        self._list_view.value = new_value

    def _add(self):
        self._model.current_id = None
        raise NextScene("Edit Type")

    def _edit(self):
        self.save()
        self._model.current_type = self.data["types"]
        raise NextScene("Edit Type")

    def _delete(self):
        self.save()
        self._model.delete_type(self.data["types"])
        self._reload_list()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


class TypeView(Frame):
    def __init__(self, screen, model):
        super(TypeView, self).__init__(
            screen,
            screen.height,
            screen.width,
            hover_focus=True,
            title="Type Effectiveness Editor",
            # title=model.get_cur_type_name(),
            reduce_cpu=True,
        )
        # Save off the model that accesses the type database.
        self._model = model

        # Create the form for displaying the type effectivenesses.
        head = Layout([25, 50, 25])
        self.add_layout(head)
        head.add_widget(Text("Name:", "name"), 1)
        layout = Layout([4, 1, 4, 1], fill_frame=True)
        self.add_layout(layout)
        # layout.add_widget()
        layout.add_widget(Text("Address:", "address"))
        layout.add_widget(Text("Phone number:", "phone"))
        layout.add_widget(Text("Email address:", "email"))
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(TypeView, self).reset()
        self.data = self._model.get_current_type()

    def _ok(self):
        self.save()
        self._model.update_current_type(self.data)
        raise NextScene("Main")

    @staticmethod
    def _cancel():
        raise NextScene("Main")


def demo(screen, scene):
    scenes = [
        Scene([ListView(screen, types)], -1, name="Main"),
        Scene([TypeView(screen, types)], -1, name="Edit Type"),
    ]

    screen.set_title("Type Effectiveness Editor")
    screen.play(scenes, stop_on_resize=True, start_scene=scene)


types = TypeModel()
last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
