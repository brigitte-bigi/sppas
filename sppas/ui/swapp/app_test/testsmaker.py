# -*- coding: UTF-8 -*-
"""
:filename: sppas.ui.swapp.app_test.testsmaker.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The page "Tests" of the SPPAS wapps.

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

    Copyright (C) 2011-2026  Brigitte Bigi, CNRS
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
import os
import random
import logging
import time

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLButtonNode

from sppas.core.config import sg
from sppas.src.wkps.wio import sppasWJSON
from sppas.ui.agnostic import sppasCommClient
from sppas.ui.agnostic import sppasCommKeys
from sppas.ui.agnostic.filechooser.filechooser_mixin import FileChooserMixin
from sppas.ui.swapp.wappcore.wappsg import wapp_settings
from sppas.ui.swapp.wappcore.wappsg import wapp_wkps
from sppas.ui.swapp.wappcore.wappsg import notify_wkp_changed
from sppas.ui.swapp.wappcore.wappsg import notify_show_page
from sppas.ui.swapp.wappcore.wappsg import wx_is_running
from sppas.ui.swapp.wappcore.wapputils import sppasImagesAccess
from sppas.ui.swapp.nodes import sppasHTMLButton
from sppas.ui.swapp.wappbase.wappresponse import swappBaseResponse

# ---------------------------------------------------------------------------


def _run_file_dialog(filetypes=None):
    try:
        return FileChooserMixin().ask_file(
            mode="openfile",
            title="Choose a file",
            multiple=False,
            filetypes=filetypes,
            defaultextension=None
        )
        #return json.loads(output).get("file_path", "")
    except Exception as e:
        return f"Error : {e}"

# ---------------------------------------------------------------------------

# What the page brings of Whakerexa: the classes are imported, and nothing
# waits for the namespace. A module of the head runs before the loader has
# finished, and window.Wexa holds nothing of the framework yet.
JS_IMPORTS = (
    "import { RequestManager, OnLoadManager, LinkController } from "
    f"'/{wapp_settings.wexa_statics}js/wexa.js';"
)

# javascript code example to send a post request and get data in response
JS_VALUE = JS_IMPORTS + """

const PAGE_URI = window.location.pathname.substring(1);

async function setRandomColor() {
    // test with json post request
    const requestManager = new RequestManager();
    const response = await requestManager.sendPostRequest({update_text_color: true}, "application/json", PAGE_URI);

    let date = new Date();
    console.log("time to receive server response: " + (date.getTime() - response["time"]) + "ms");

    let coloredElement = document.getElementsByName("colored")[0];
    coloredElement.style.color = response["random_color"];
}

async function choisirFichier() {
    const requestManager = new RequestManager();
    const response = await requestManager.sendPostRequest({choose_file: true}, "application/json", PAGE_URI);
    alert("Fichier choisi : " + response["file_path"]);
}

OnLoadManager.addLoadFunction(() => {
    new LinkController().handleLinksWithParameters(["home_button"]);
});

OnLoadManager.addLoadFunction(() => {
    document.getElementsByName("update_btn_text")[0].onclick = async () => {
        const requestManager = new RequestManager();
        await requestManager.sendPostRequest({update_btn_text_event: true}, "application/json", PAGE_URI);
        window.location.reload();
    };
});

OnLoadManager.addLoadFunction(() => {
    document.getElementsByName("socket_ping")[0].onclick = async () => {
        const requestManager = new RequestManager();
        const response = await requestManager.sendPostRequest({socket_ping: true}, "application/json", PAGE_URI);
        alert(JSON.stringify(response["socket_response"]));
    };
});

OnLoadManager.addLoadFunction(() => {
    const pages = ["page_files", "page_annotate", "page_analyze",
                   "page_editor", "page_convert", "page_plugins"];
    pages.forEach((page) => {
        const button = document.getElementsByName("show_" + page)[0];
        if (button === undefined) {
            return;
        }
        button.onclick = async () => {
            const requestManager = new RequestManager();
            const request = {};
            request["show_" + page] = true;
            const response = await requestManager.sendPostRequest(request, "application/json", PAGE_URI);
            alert(JSON.stringify(response["socket_response"]));
        };
    });
});

OnLoadManager.addLoadFunction(() => {
    document.getElementsByName("choose_file")[0].onclick = choisirFichier;
});

OnLoadManager.addLoadFunction(() => {
    document.getElementsByName("choose_txt_file")[0].onclick = async () => {
        const requestManager = new RequestManager();
        const response = await requestManager.sendPostRequest({choose_txt_file: true}, "application/json", PAGE_URI);
        alert("Fichier TXT choici : " + response["file_path"]);
    };
});

OnLoadManager.addLoadFunction(() => {
    document.getElementsByName("show_workspace")[0].onclick = async () => {
        const requestManager = new RequestManager();
        const response = await requestManager.sendPostRequest({show_workspace: true}, "application/json", PAGE_URI);
        const workspaceElement = document.getElementsByName("workspace_content")[0];
        workspaceElement.textContent = JSON.stringify(response["workspace"], null, 4);
    };
});


// we wait that the page finished to load to get the h2 element
OnLoadManager.addLoadFunction(() => {
    // loop every 1.5s times
    setInterval(() => {
        setRandomColor();
    }, 1500);
});

"""

# ---------------------------------------------------------------------------


class TestsResponseRecipe(swappBaseResponse):

    def __init__(self, name="Test", tree=None, title= sg.__name__ + " Tests"):
        """Create a HTTPD Response instance with a default response.

        :param name: (str) Filename of the body main content.

        """
        # Inheritance with a given dynamic HTMLTree.
        super(TestsResponseRecipe, self).__init__(name, tree, title)
        self._bake()

    # -----------------------------------------------------------------------

    @classmethod
    def page(cls) -> str:
        """Return a short description of the application."""
        return "test.html"

    # -----------------------------------------------------------------------

    @staticmethod
    def description() -> str:
        """Return a short description of the response."""
        return "A webapp to test the swapp of SPPAS."

    # -----------------------------------------------------------------------

    def create(self):
        """Override. Create the fixed page content in HTML.

        The fixed content corresponds to the parts that can't be invalidated:
        head, body_header, body_footer.

        """
        super().create()

        # Added js scripts
        script = HTMLNode(self._htree.head.identifier, None, "script",
                          value=JS_VALUE, attributes={'type': "module"})
        self._htree.head.append_child(script)

        # Add elements in the header
        _h1 = HTMLNode(self._htree.body_header.identifier, None, "h1",
                       value="Test of swapp")
        self._htree.body_header.append_child(_h1)

        home_button = sppasHTMLButton(self._htree.body_header.identifier, identifier="home_button")
        home_button.add_attribute("data-href", "/")
        home_button.add_attribute("data-target", "_self")
        home_button.add_attribute("class", "menuitem")
        home_button.set_icon(sppasImagesAccess.get_logo_filename("sppas-logo-v5"))
        home_button.set_text(None, "Home")
        self._htree.body_header.append_child(home_button)

        # Add an element in the footer
        _p = HTMLNode(self._htree.body_footer.identifier, None, "p",
                      value="Copyright 2011-2026 Brigitte Bigi, CNRS")
        self._htree.body_footer.append_child(_p)

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(" >>>>> Page test.html -- Process events: {} <<<<<< ".format(events))
        self._status.code = 200
        dirty = False

        for event_name in events.keys():
            if event_name == "update_text_color":
                random_color = TestsResponseRecipe.__generate_random_color()
                self._data = {"random_color": random_color, "time": round(time.time() * 1000)}

            elif event_name == "update_btn_text_event":
                dirty = True

            elif event_name == "choose_file":
                path = _run_file_dialog()
                if os.path.isfile(path) is True:
                    wapp_wkps.data.add_file(path)
                    notify_wkp_changed()
                self._data = {"file_path": path}

            elif event_name == "choose_txt_file":
                path = _run_file_dialog(filetypes=[("Texts", "*.txt"), ("All files", "*.*")])
                if os.path.isfile(path) is True:
                    wapp_wkps.data.add_file(path)
                    notify_wkp_changed()
                self._data = {"file_path": path}

            elif event_name == "socket_ping":
                client = sppasCommClient(wapp_settings.shost, wapp_settings.sport)
                request = client.format_request(sppasCommKeys.PING, {"source": "test.html"})
                response = client.request(request)
                self._data = {"socket_response": response}

            elif event_name.startswith("show_page_") is True:
                # Ask the wx interface to show one of its pages. Without a
                # running interface, the message is dropped by the notifier:
                # the answer says so, which is what this test is about.
                page_name = event_name[len("show_"):]
                # The interface is asked before the message is sent: the
                # answer says whether there was anybody to send it to.
                alive = wx_is_running()
                notify_show_page(page_name)
                self._data = {"socket_response":
                              "SHOW_PAGE {:s} sent. wx answered: {}"
                              "".format(page_name, alive)}

            elif event_name == "show_workspace":
                wjson = sppasWJSON()
                wjson.set(wapp_wkps.data)
                self._data = {"workspace": wjson.serialize()}

            else:
                logging.warning("Ignore event: {:s}".format(event_name))

        return dirty

    # -----------------------------------------------------------------------

    def _bake(self):
        """Create the dynamic page content in HTML."""
        self.comment("Body content")
        text = TestsResponseRecipe.__generate_random_text()
        logging.debug(" -> new dynamic content: {:s}".format(text))

        # Add element into the main
        _p = HTMLNode(self._htree.body_main.identifier, None, "p",
                      value="THIS text-line is changing color without refreshing the page!")
        _p.set_attribute("name", "colored")
        self._htree.body_main.append_child(_p)

        # The easiest way to create an element and add it into the body->main
        h2 = self.element("h2")
        h2.set_value("Rainbow HTTP response {:d}".format(self._status.code))

        # The powered way to do the same!
        p = HTMLNode(self._htree.body_main.identifier, None, "p",
                     value="Click the button to re-create the dynamic content of the page.")
        self._htree.body_main.append_child(p)

        b = HTMLButtonNode(self._htree.body_main.identifier, "update_btn_text")
        b.set_value(text)
        self._htree.body_main.append_child(b)

        # ---------------------

        h2 = self.element("h2")
        h2.set_value("Test file chooser")

        b = HTMLButtonNode(self._htree.body_main.identifier, "choose_file")
        b.set_value("Choose a file")
        self._htree.body_main.append_child(b)

        b = HTMLButtonNode(self._htree.body_main.identifier, "choose_txt_file")
        b.set_value("Choose a txt file")
        self._htree.body_main.append_child(b)

        # ---------------------

        h2 = self.element("h2")
        h2.set_value("Test socket communication")

        b = HTMLButtonNode(self._htree.body_main.identifier, "socket_ping")
        b.set_value("Send ping to socket server")
        self._htree.body_main.append_child(b)

        # ---------------------

        h2 = self.element("h2")
        h2.set_value("Test the pages of the wx interface")

        p = HTMLNode(self._htree.body_main.identifier, None, "p",
                     value="Each button asks the wx interface to show one of "
                           "its pages, and to come to the front.")
        self._htree.body_main.append_child(p)

        for page_name in ("page_files", "page_annotate", "page_analyze",
                          "page_editor", "page_convert", "page_plugins"):
            b = HTMLButtonNode(self._htree.body_main.identifier, "show_" + page_name)
            b.set_value(page_name)
            self._htree.body_main.append_child(b)

        # ---------------------

        h2 = self.element("h2")
        h2.set_value("Test workspace exchange")

        b = HTMLButtonNode(self._htree.body_main.identifier, "show_workspace")
        b.set_value("Show the shared workspace")
        self._htree.body_main.append_child(b)

        workspace_pre = HTMLNode(self._htree.body_main.identifier, None, "pre", value="")
        workspace_pre.set_attribute("name", "workspace_content")
        self._htree.body_main.append_child(workspace_pre)

    # ------------------------------------------------------------------
    # STATIC METHODS
    # ------------------------------------------------------------------

    @staticmethod
    def __generate_random_color() -> str:
        """Example to the request system. Returns a random color

        :return: (str) The random color

        """
        colors = ["red", "green", "yellow", "blue", "black", "pink", "orange", "maroon", "aqua", "silver", "purple"]
        random_index_color = random.randrange(len(colors))

        return colors[random_index_color]

    # ------------------------------------------------------------------

    @staticmethod
    def __generate_random_text() -> str:
        """Returns a random text.

        :return: (str) The random text

        """
        pronoun = ["I", "you", "we"]
        verb = ["like", "see", "paint"]
        colors = ["red", "green", "yellow", "blue", "black", "pink", "orange", "maroon", "aqua", "silver", "purple"]

        return pronoun[random.randrange(len(pronoun))] + " " \
            + verb[random.randrange(len(verb))] + " " \
            + colors[random.randrange(len(colors))]
