/** @odoo-module **/

import {renderToMarkup} from "@web/core/utils/render";
import publicWidget from '@web/legacy/js/public/public_widget';
import {InputConfirmationDialog} from '@portal/js/components/input_confirmation_dialog/input_confirmation_dialog';
import {_t} from "@web/core/l10n/translation";


publicWidget.registry.CreateNcrApproval = publicWidget.Widget.extend({
    selector: '.o_portal_create_ncr_approval',
    events: {
        click: '_onClick',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.dialog = this.bindService("dialog");

    },

    async _onClick(e) {
        e.preventDefault();
        // var approval_types = Object.assign({}, await this.orm.searchRead("ir.model.fields.selection", [["field_id.name", "=", "approval_type"], ["field_id.model", "=", "quality.ncr.approvals"]], ["id", "value", "name"]));
        this.call("dialog", "add", InputConfirmationDialog, {
                title: _t("Create Non-Conformance Report Approval"),
                // This fails. Not sure why.
                // TypeError: this.child.mount is not a function
                //     at VToggler.mount (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:645:57)
                //     at B.mount (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:805:269)
                //     at Object.mount$1 [as mount] (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:879:54)
                //     at render (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:5898:209)
                //     at renderToString (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:5896:93)
                //     at renderToMarkup (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:5899:100)
                //     at Class._onClick (https://odoo-devops-1825-v17.ep-sys.net/web/assets/1/3f48c3e/web.assets_frontend_lazy.min.js:8095:1288)

                // body: renderToMarkup("AS9100_quality.portal_create_ncr_approval", { approval_type_list: approval_types}),
                body: renderToMarkup("AS9100_quality.portal_create_ncr_approval"),
                confirmLabel: _t("Request Approval"),
                confirm: async ({}) => {
                    await this.orm.create("quality.ncr.approvals", [{approval_type: document.getElementById('approval_type_input_manual').value, ncr_report_id: parseInt(this.el.dataset.ncrid)}]);
                }
            },

            {
                onClose: () => {
                    window.location = window.location;
                }
            }
        )
    },
});

publicWidget.registry.ApproveNCRApproval = publicWidget.Widget.extend({
    selector: '.o_portal_approve_ncr_approval',
    events: {
        click: '_onClick',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.dialog = this.bindService("dialog");

    },

    async _onClick() {
        await this.orm.write('quality.ncr.approvals', [parseInt(this.el.dataset.approvalid)], {is_approved: !Boolean(this.el.dataset.approval)});
        window.location = window.location;
    },
});

publicWidget.registry.CharAutosave = publicWidget.Widget.extend({
    selector: '.o_portal_autosave_char',
    events: {
        blur: '_AutoSave',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.dialog = this.bindService("dialog");

    },

    async _AutoSave() {
        let field_dict = {};
        field_dict[this.el.id] = this.el.innerText
        await this.orm.write(this.el.dataset.model, [parseInt(this.el.dataset.recordid)], field_dict);
    },
});

publicWidget.registry.One2manyAutosave = publicWidget.Widget.extend({
    selector: '.o_portal_one2many_autosave',
    events: {
        blur: '_AutoSave',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.dialog = this.bindService("dialog");

    },

    async _AutoSave() {
        let field_dict = {};
        if (this.el.value == "False") {
            field_dict[this.el.id] = false;
        } else {
            field_dict[this.el.id] = parseInt(this.el.value);
        }
        await this.orm.write(this.el.dataset.model, [parseInt(this.el.dataset.recordid)], field_dict);
        window.location = window.location;
    },
});

publicWidget.registry.SelectAutosave = publicWidget.Widget.extend({
    selector: '.o_portal_select_autosave',
    events: {
        blur: '_AutoSave',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.dialog = this.bindService("dialog");

    },

    async _AutoSave() {
        let field_dict = {};
        if (this.el.value == "False") {
            field_dict[this.el.id] = false;
        } else {
            field_dict[this.el.id] = this.el.value;
        }
        await this.orm.write(this.el.dataset.model, [parseInt(this.el.dataset.recordid)], field_dict);
    },
});

publicWidget.registry.select_tag  = publicWidget.Widget.extend({
    selector: '.select',
    init: function () {
        $("select.select").select2();
    },
});