/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.lotDomain = publicWidget.Widget.extend({
    selector: '.lot_domain',
    events: {
        'change select[name="product_id"]': '_OnProductChange',
    },

    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        this.orm = this.bindService("orm");
        this._lotDomain();
        return def
    },

    /**
     * @private
     */
    async _lotDomain() {
        var $product = this.$('select[name="product_id"]');
        var val = ($product.val() || false);
        if (val) {
            const lots = await this.orm.searchRead('stock.lot', [['product_id', '=', parseInt(val)]], ['id', 'name'])

            if (document.getElementById('s2id_lot_ids').querySelectorAll('.select2-search-choice')) {
                document.getElementById('s2id_lot_ids').querySelectorAll('.select2-search-choice').forEach(e => e.remove());
            }
            if (document.getElementById('lot_ids').options) {
                for (let i = document.getElementById('lot_ids').options.length - 1; i >= 0; i--) {
                    document.getElementById('lot_ids').remove(i);
                }
            }

            for (let i = 0; i < lots.length; i++) {
                var opt = document.createElement('option');
                opt.value = lots[i].id
                opt.innerText = lots[i].name
                opt.innerText = lots[i].name
                document.getElementById('lot_ids').appendChild(opt);
            }

        } else {
            if (document.getElementById('lot_ids').options) {
                for (let i = document.getElementById('lot_ids').options.length - 1; i >= 0; i--) {
                    document.getElementById('lot_ids').remove(i);
                }
            }

        }
    },
    /**
     * @private
     */
    async _OnProductChange() {
        await this._lotDomain();
    },
});