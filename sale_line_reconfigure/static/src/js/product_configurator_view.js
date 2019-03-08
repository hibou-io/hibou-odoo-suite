odoo.define('sale_line_reconfigure.ProductConfiguratorFormView', function (require) {
"use strict";

var ProductConfiguratorFormController = require('sale_line_reconfigure.ProductConfiguratorFormController');
var ProductConfiguratorFormRenderer = require('sale_line_reconfigure.ProductConfiguratorFormRenderer');
var FormView = require('web.FormView');
var viewRegistry = require('web.view_registry');

var ProductConfiguratorFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
        Controller: ProductConfiguratorFormController,
        Renderer: ProductConfiguratorFormRenderer,
    }),
});

viewRegistry.add('product_configurator_form', ProductConfiguratorFormView);

return ProductConfiguratorFormView;

});