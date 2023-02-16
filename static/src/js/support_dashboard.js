odoo.define('website_supportzayd.SupportDashboard', function (require) {
"use strict";


var KanbanController = require('web.KanbanController');
var KanbanModel = require('web.KanbanModel');
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanView = require('web.KanbanView');
var viewRegistry = require('web.view_registry');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');



var SupportDashboardController = KanbanController.extend({});
var SupportDashboardRenderer = KanbanRenderer.extend({
    //className: "o_helpdesk_dashboard",

    xmlDependencies: ['/website_supportzayd/static/src/xml/ebsupport_dashboard.xml'],
    events: _.extend({}, KanbanRenderer.prototype.events, {
        //"eventName . variable's unique selector: function name defined"
        //"click .dropdown-menu li a": "_onDropdownClicked"
        "click .onHighPriorityTickets" : "_onHighPriorityTicketsClicked",
        "click .onUnattendedTickets" : "_onUnattendedTicketsClicked",
        "click .onUrgentPriorityTickets" : "_onUrgentPriorityTicketsClicked",
        //"click .onAvgOpenHours" : "_onAvgOpenHoursClicked", commented this line as we might not need the pivot view things.
        "click .onSLAFailed" : "_onSLAFailedClicked",
        "click .onSLAFailed_highpriority" : "_onSLAFailed_highpriorityClicked",
        "click .onSLAFailed_urgent" : "_onSLAFailed_urgentClicked",
        "click .onClosedTicketsToday" : "_onClosedTicketsTodayClicked",
        "click .onClosedTicketsWeek" : "_onClosedTicketsWeekClicked",
        "click .onClosedTicketsMonth" : "_onClosedTicketsMonthClicked",


        }),
        init: function(){
        //this is a default constructor
            this.name= "Testing";
            this._super.apply(this, arguments);
        },

        _render: function () {
            var self = this;

            return this._super.apply(this, arguments).then(function () {

                var helpdesk_dashboard = QWeb.render('helpdesk-template');

                self.$el.prepend(helpdesk_dashboard);

                //this.$el.html(QWeb.render('helpdesk-template'));
                self._get_average_openhours();
                self._get_average_openhours_highpriority();
                self._get_average_openhours_urgent();
                //self._get_closed_ticket_count(); this is the code to count for ALL closed ticket count. it is commented for now because it isnt needed yet
                self._get_closed_ticket_today_count()
                self._get_closed_ticket_week_count();
                self._get_closed_ticket_month_count();
                self._get_open_ticket_count();
                self._get_highpriority_ticket_count();
                self._get_urgent_ticket_count();
                self._get_failedSLA_count();
                self._get_failedSLA_highpriority_count();
                self._get_failedSLA_urgent_count();
                self._get_success_rate_today();
                self._get_success_rate_week();
                self._get_success_rate_month();

            });
                //this.$el.html(QWeb.render('helpdesk-template'));
                //var rendered_html = QWeb.render('helpdesk-template',{ key: value });

            //return this._super.apply(this, arguments)
        },

        /*_onAvgOpenHoursClicked: function(e){
            var self = this;
            e.preventDefault();
            e.stopPropagation();

            //for reference of taking specific record for views of any type (pivot, form, tree, etc), please see this link.
            //https://www.odoo.com/forum/help-1/how-to-call-a-specific-view-of-odoo-from-js-in-the-current-window-124181
            //the information gained from the link are analysed and used in this function
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['website_supportzayd_ticket.website_supportzayd_ticket_view_pivot'], // View id goes here in the format of args: ['modelname', 'viewid']

            }).then(function(data){
            // Open view

                self.do_action({
                    name: 'My Avg Open Hours Tickets',
                    type: 'ir.actions.act_window',
                    res_model: 'website.supportzayd.ticket',
                    view_mode: 'pivot',
                    view_type: 'pivot',
                    views: [[data[1], 'pivot']],
                    //view_id : 'website_supportzayd_ticket_view_pivot', //refer to specific view type according to its <record id="" />
                    //https://www.odoo.com/forum/help-1/how-to-call-a-specific-view-of-odoo-from-js-in-the-current-window-124181
                    //domain: [['employee_id','=', this.login_employee.id]],
                    //domain: [('create_date','<',datetime.strftime('%%Y-%%m-%%d 23:59:59')),    ('create_date','>=',(datetime.date.today()-datetime.timedelta(days=7)).strftime('%%Y-%%m-%%d 00:00:00'))],
                    target: 'current',
                    //context:{'search_default_unattended_tickets':1}
                });
            });
        },*/

        _onSLAFailedClicked : function(e){
            var self = this;
            e.preventDefault();
            e.stopPropagation();
            this.do_action({
                name: 'My "Open" SLA Failed Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                domain: [['state.name','=', 'Open'],['sla_timer','<','0']], // set domain to only show tickets with status 'OPEN'
                target: 'current',
                context:{'search_default_slafailed_tickets':1,'search_default_unattended_tickets':1}
            });
        },

        _onSLAFailed_highpriorityClicked : function(e){
            var self = this;
            e.preventDefault();
            e.stopPropagation();
            this.do_action({
                name: 'My "Open" SLA Failed with High Priority Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                domain: [['state.name','=', 'Open'],['sla_timer','<','0']],
                target: 'current',
                context:{'search_default_slafailed_tickets_highpriority':1}
            });
        },


        _onSLAFailed_urgentClicked : function(e){
            var self = this;
            e.preventDefault();
            e.stopPropagation();
            this.do_action({
                name: 'My "Open" SLA Failed with Urgent Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                domain: [['state.name','=', 'Open'],['sla_timer','<','0']],
                target: 'current',
                context:{'search_default_slafailed_tickets_urgent':1}
            });
        },

        //probably need to check into schedule actions AKA ir.cron for this. because conceptually the idea is to  do the current datetime minus "OPEN TICKETS"'s create_time
        //second choice is i think the best choice, which is to do it the normal javascript way, and then the data will be updated upon refresh :)
        _get_average_openhours: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_average_openhours",
                args: [],
            }).then(function (count){
                $('#avg_openhours_id').text(count); //finally... assign returned value from python and write it into the table using getelementID javascript or (#)
                console.log(count);
            });
        },

        _get_average_openhours_highpriority: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_average_openhours_highpriority",
                args: [],
            }).then(function (result){
                $('#avg_openhours_highpriority_id').text(result);
                console.log("average openhours highpriority: ", result)//finally... assign returned value from python and write it into the table using getelementID javascript or (#)
            });
        },


        _get_average_openhours_urgent: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_average_openhours_urgent",
                args: [],
            }).then(function (result){
                console.log("average open hours is ",result)
                $('#avg_openhours_urgent_id').text(result); //finally... assign returned value from python and write it into the table using getelementID javascript or (#)
            });
        },



         _get_closed_ticket_week_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_closedticket_week_count",
                args: [],
            })
            // then(function(count)) akan call function di python get_closedticket_count and take the returned value from get_closedticket_count
            .then(function (count) {
                $('#closedtickets_week_id').text(count); //finally... assign returned value from python and write it into the table using getelementID javascript or (#)
            });
        },

        _get_closed_ticket_month_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_closedticket_month_count",
                args: [],
            })
            // then(function(count)) akan call function di python get_closedticket_count and take the returned value from get_closedticket_count
            .then(function (count) {
                $('#closedtickets_month_id').text(count); //finally... assign returned value from python and write it into the table using getelementID javascript or (#)
            });
        },

            //the function get_closed_ticket_count is to count all closed ticket
            _get_closed_ticket_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_closedticket_count",
                args: [],
            })
            // then(function(count)) akan call function di python get_closedticket_count and take the returned value from get_closedticket_count
            .then(function (count) {
                $('#closedtickets_id').text(count); //finally... assign returned value from python and write it into the table using getelementID javascript or (#)
            });
        },

        _get_closed_ticket_today_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_closedticket_today_count",
                args: [],
            })
            // then(function(count)) akan call function di python get_closedticket_count and take the returned value from get_closedticket_count
            .then(function (count) {
                $('#closedtickets_today_id').text(count); //finally... assign returned value from python and write it into the table using getelementID javascript or (#)
            });
        },


        _get_open_ticket_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_openticket_count",
                args: [],
            })
            .then(function (count) {
                $('#opentickets_id').text(count); //write value into table>span in helpdesk-template
            });
        },


        _get_highpriority_ticket_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_highpriorityticket_count",
                args: [],
            })
            .then(function (count) {
                $('#highprioritytickets_id').text(count); //write value into table>span in helpdesk-template
            });
        },

        _get_urgent_ticket_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_urgentticket_count",
                args: [],
            })
            .then(function (count) {
                $('#urgenttickets_id').text(count); //write value into table>span in helpdesk-template
            });
        },

        _get_failedSLA_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_failedSLA_count",
                args: [],
            })
            .then(function (count) {
                $('#failedSLA_id').text(count); //write value into table>span in helpdesk-template
            });
        },

        _get_failedSLA_highpriority_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_failedSLA_highpriority_count",
                args: [],
            })
            .then(function (count) {
                $('#failedSLA_highpriority_id').text(count); //write value into table>span in helpdesk-template
            });
        },


        _get_failedSLA_urgent_count: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_failedSLA_urgent_count",
                args: [],
            })
            .then(function (count) {
                $('#failedSLA_urgent_id').text(count); //write value into table>span in helpdesk-template
            });
        },

        _get_success_rate_today: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_success_rate_today",
                args: [],
            })
            .then(function (count) {
                $('#success_rate_today_id').text(count); //write value into table>span in helpdesk-template
            });
        },

        _get_success_rate_week: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_success_rate_week",
                args: [],
            })
            .then(function (count) {
                $('#success_rate_week_id').text(count); //write value into table>span in helpdesk-template
                console.log(count)
            });
        },

        _get_success_rate_month: function(){
            var self=this;
            rpc.query({
                model: "website.supportzayd.ticket",
                method: "get_success_rate_month",
                args: [],
            })
            .then(function (count) {
                $('#success_rate_month_id').text(count); //write value into table>span in helpdesk-template
                console.log( count)
            });
        },






        //https://www.odoo.com/forum/help-1/how-to-use-rpc-query-in-javascript-with-read-method-for-get-all-rows-from-table-173529 @hafizalwi20januari
        _onUnattendedTicketsClicked: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: 'My Open Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                //domain: [['employee_id','=', this.login_employee.id]],
                target: 'current',
                context:{'search_default_unattended_tickets':1}
            });
        },

        _onHighPriorityTicketsClicked: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: 'My High Priority Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                domain: [['state.name','in',['Open','Customer Replied']]],
                target: 'current',
                context:{'search_default_highpriority_tickets':1}
            });
        },


        _onUrgentPriorityTicketsClicked: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: 'My Urgent Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                domain: [['state.name','in',['Open','Customer Replied']]],
                target: 'current',
                context:{'search_default_urgentpriority_tickets':1}
            });
        },

        //https://www.odoo.com/forum/help-1/how-to-use-rpc-query-in-javascript-with-read-method-for-get-all-rows-from-table-173529 @hafizalwi20januari
        _onClosedTicketsTodayClicked: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: 'My Closed Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                //domain: [['employee_id','=', this.login_employee.id]],
                target: 'current',
                context:{'search_default_closed_tickets':1, 'search_default_today_closed':1}
            });
        },
        _onClosedTicketsWeekClicked: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: 'My Weekly Closed Tickets ',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                //domain: [['employee_id','=', this.login_employee.id]],
                target: 'current',
                context:{'search_default_closed_tickets':1,'search_default_current_week_closed':1}
            });
        },

        _onClosedTicketsMonthClicked: function(e){
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            this.do_action({
                name: 'My Monthly Closed Tickets',
                type: 'ir.actions.act_window',
                res_model: 'website.supportzayd.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'],[false, 'form']],
                //domain: [['employee_id','=', this.login_employee.id]],
                target: 'current',
                context:{'search_default_closed_tickets':1,'search_default_current_month_closed':1}
            });
        },



        
});

var SupportDashboardModel = KanbanModel.extend({


});

/*var support_dashboard= View.extend({
 icon: 'fa-cogs',
 display_name: _lt("Dashboard view"),
});
*/

var SupportDashboardView = KanbanView.extend({

    config: _.extend({}, KanbanView.prototype.config, {
        Model: SupportDashboardModel,
        Controller: SupportDashboardController,
        Renderer: SupportDashboardRenderer,
    }),


});


viewRegistry.add('supportdashboard', SupportDashboardView); //refer to the SupportDashboardView variable for the value in parameter, the one inside the "  " seems to be edittable to anything, havent reconfirm yet

return SupportDashboardView;

});