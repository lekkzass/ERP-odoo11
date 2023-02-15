odoo.define('website_supportzayd.my_attendances', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;


var MyAttendances = Widget.extend({
    events: {
        "click .o_hr_attendance_sign_in_out_icon": function() {
            this.$('.o_hr_attendance_sign_in_out_icon').attr("disabled", "disabled");
            this.update_attendance();
        },
    },

    start: function () {
        var self = this;

        var def = this._rpc({
                model: 'website.supportzayd.ticket',
                method: 'search_read',
                args: [[['state.name','=', 'Open'],['user_id', '=', this.getSession().uid],['attendance_state',  '=', 'checked_out']], ['attendance_state', 'name_check_in', 'subject', 'ticket_number', 'partner_id']], //try to make domain state.name and user_id = uid
            })
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.$el.html(QWeb.render("HrAttendanceMyMainMenu", {widget: self}));
            });

        return $.when(def, this._super.apply(this, arguments));
    },

    update_attendance: function () {
        var self = this;
        this._rpc({
                /*model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'website_supportzayd.hr_attendance_action_my_attendances'],
                */
                model: 'website.supportzayd.ticket',
                method: 'attendance_manual',
                args: [[self.employee.id], 'website_supportzayd.hr_attendance_action_my_attendances'],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
});

core.action_registry.add('website_supportzayd_hr_attendance_my_attendances', MyAttendances);

return MyAttendances;

});

