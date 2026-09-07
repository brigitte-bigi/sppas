# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.panels.annot_param.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Class to create a dialog which contains all options of an annotation.

.. _This file is part of SPPAS: https://sppas.org/
..
    -------------------------------------------------------------------------

     ######   ########   ########      ###      ######
    ##    ##  ##     ##  ##     ##    ## ##    ##    ##     the automatic
    ##        ##     ##  ##     ##   ##   ##   ##            annotation
     ######   ########   ########   ##     ##   ######        and
          ##  ##         ##         #########        ##        analysis
    ##    ##  ##         ##         ##     ##  ##    ##         of speech
     ######   ##         ##         ##     ##   ######

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
    Laboratoire Parole et Langage, Aix-en-Provence, France

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    This banner notice must not be removed.

    -------------------------------------------------------------------------

"""


from __future__ import annotations
import logging
from whakerpy import HTMLNode

from sppas.src.structs import sppasOption
from sppas.src.annotations import sppasParam

# -----------------------------------------------------------------------

JS_SCRIPT = """
function validate_options() {
    const dialog_id = "%dialog-id%";
    let data = {}
    
    // get inputs values
    const dialog_options = document.getElementById(dialog_id);
    dialog_options.childNodes.forEach(element => {
        if (element.tagName === "INPUT") {
            console.log(element.type);
            if (element.type === "checkbox") {
                if (element.checked) {
                    data[element.name] = "on";
                } else {
                    data[element.name] = "off";
                }
            } else {
                data[element.name] = element.value;   
            }
        }
    });

    // send options values to the server
    const request_manager = new RequestManager();
    request_manager.sendPostRequest(data);
    
    // close the dialog
    close_dialog(dialog_id);
}
"""

# -----------------------------------------------------------------------


class AnnotParamDialog(HTMLNode):

    REQUIRED = ["dialog.css", "dialog.js"]


    def __init__(self, annotation: str, parent_id: str):
        super(AnnotParamDialog, self).__init__(parent_id, f"{annotation}-options", "dialog", attributes={
            'id': f"{annotation}-options"
        })

        parameters = sppasParam([f"{annotation}.json"])
        ann_step_idx = parameters.get_step_idx(annotation)

        if ann_step_idx == -1:
            raise ValueError(f"The annotation : {annotation} can't be enabled !")

        self.__options = parameters.get_options(ann_step_idx)
        self.__hidden_options = list()

    # -----------------------------------------------------------------------
    # GETTERS
    # -----------------------------------------------------------------------

    def get_script(self) -> str:
        return JS_SCRIPT.replace("%dialog-id%", self.identifier)

    # -----------------------------------------------------------------------

    def get_options(self) -> list[sppasOption]:
        return self.__options

    # -----------------------------------------------------------------------

    def get_option_value(self, option_name) -> object:
        for opt in self.__options:
            if opt.get_key() == option_name:
                return opt.get_value()

        return None

    # -----------------------------------------------------------------------
    # SETTERS
    # -----------------------------------------------------------------------

    def set_option(self, option_name: str, option_value: object) -> bool:
        for opt in self.__options:
            if opt.get_key() == option_name:
                opt.set_value(option_value)
                return True

        return False

    # -----------------------------------------------------------------------
    # PUBLIC METHODS
    # -----------------------------------------------------------------------

    def hide_option_element(self, option_name: str) -> None:
        self.__hidden_options.append(option_name)

        # remove node elements if already bake
        self.remove_child(option_name)
        self.remove_child(f"{option_name}-label")  # for number and text option type

    # -----------------------------------------------------------------------

    def process_event(self, event_name: str, event_value: object) -> int:
        for opt in self.__options:
            if opt.get_key() == event_name:
                # special case for checkbox values
                if opt.get_type() == "bool":
                    opt.set_value(event_value == "on")
                else:
                    opt.set_value(event_value)

                return 200

        return 205

    # -----------------------------------------------------------------------
    # PRIVATE METHODS
    # -----------------------------------------------------------------------

    def bake(self) -> None:
        self.clear_children()

        for opt in self.__options:
            # skip hidden options
            if opt.get_key() in self.__hidden_options:
                continue

            # create html node according to its type
            if opt.get_type() == "str":
                self.__create_text_input(opt)
            elif opt.get_type() == "bool":
                self.__create_checkbox(opt)
            elif opt.get_type() == "int":
                self.__create_number_input(opt)
            elif opt.get_type() == "float":
                self.__create_number_input(opt, is_float=True)
            else:
                logging.warning(f"Unknown annotation option type to create html content : {opt.get_type()}")

        validate_button = HTMLNode(self.identifier, None, "button", value="Confirm", attributes={
            'onclick': "validate_options()",
            'name': "annot-opt-validate-btn"
        })
        self.append_child(validate_button)

    # -----------------------------------------------------------------------

    def __create_checkbox(self, option: sppasOption) -> None:
        checkbox = HTMLNode(self.identifier, option.get_key(), "input", attributes={
            'name': option.get_key(),
            'type': "checkbox"
        })

        checkbox_label = HTMLNode(self.identifier, f"{option.get_key()}-label", "label", value=option.get_text(),
                                  attributes={'for': option.get_key()})

        if option.get_value() is True:
            checkbox.set_attribute("checked", "checked")

        self.append_child(checkbox)
        self.append_child(checkbox_label)
        self.append_child(HTMLNode(self.identifier, None, "br"))

    # -----------------------------------------------------------------------

    def __create_number_input(self, option: sppasOption, is_float: bool = False,
                              min_range: int | float = 0, max_range: int | float = 2000) -> None:

        number_label = HTMLNode(self.identifier, f"{option.get_key()}-label", "label", value=option.get_text(), attributes={
            'for': option.get_key()
        })

        number_input = HTMLNode(self.identifier, option.get_key(), "input", attributes={
            'name': option.get_key(),
            'type': "number",
            'value': str(option.get_value()),
            'min': str(min_range),
            'max': str(max_range)
        })

        if is_float is True:
            number_input.set_attribute("step", "0.01")

        self.append_child(number_label)
        self.append_child(number_input)

    # -----------------------------------------------------------------------

    def __create_text_input(self, option: sppasOption) -> None:
        text_label = HTMLNode(self.identifier, f"{option.get_key()}-label", "label", value=option.get_text(),
                              attributes={'for': option.get_key()})

        text_input = HTMLNode(self.identifier, option.get_key(), "input",
                              attributes={'name': option.get_key(), 'type': "text", 'value': option.get_value()})

        self.append_child(text_label)
        self.append_child(text_input)
