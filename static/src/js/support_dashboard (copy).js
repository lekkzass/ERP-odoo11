odoo.define('website_supportzayd.SupportDashboard', function (require) {
"use strict";


var AbstractController = require('web.AbstractController');
var AbstractModel = require('web.AbstractModel');
var AbstractRenderer = require('web.AbstractRenderer');
var AbstractView = require('web.AbstractView');
var viewRegistry = require('web.view_registry');


var SupportDashboardController = AbstractController.extend({});
var SupportDashboardRenderer = AbstractRenderer.extend({});
var SupportDashboardModel = AbstractModel.extend({});

//var support_dashboard=View.extend is optional to only for control panel GUIS
//var support_dashboard= View.extend({
 //icon: 'fa-cogs',
 //display_name: _lt("Dashboard view"),
//});

var SupportDashboardView = AbstractView.extend({});

viewRegistry.add('supportdashboard', SupportDashboardView); //refer to the SupportDashboardView variable for the value in parameter, the one inside the "  " seems to be edittable to anything, havent reconfirm yet

return SupportDashboardView;

});
