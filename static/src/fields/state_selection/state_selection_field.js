/** @odoo-module **/

import { StateSelectionField } from "@web/views/fields/state_selection/state_selection_field";
import { patch } from "@web/core/utils/patch";

patch(StateSelectionField.prototype, {
    setup() {
        super.setup(...arguments);
        this.colors = {
            blocked: "red",
            done: "green",
            info: "blue",
            warning: "yellow",
        };
    },
});