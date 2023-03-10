odoo.define('website_supportzayd.greeting_message', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

var _t = core._t;


var GreetingMessage = Widget.extend({
    template: 'HrAttendanceGreetingMessage',

    events: {
        "click .o_hr_attendance_button_dismiss": function() { this.do_action(this.next_action, {clear_breadcrumbs: true}); },
    },

    init: function(parent, action) {
        var self = this;
        this._super.apply(this, arguments);
        //this.activeBarcode = true;
        // if no correct action given (due to an erroneous back or refresh from the browser), we set the dismiss button to return
        // to the (likely) appropriate menu, according to the user access rights
        //if(!action.attendance) {
            //this.getSession().user_has_group('website_supportzayd.support_technician').then(function(has_group) {
            //    if(has_group) {
        //    self.next_action = 'website_supportzayd.hr_attendance_action_my_attendances';
            //    }
            //});
        //    return;
        //}

        this.next_action = action.next_action || 'website_supportzayd.hr_attendance_action_my_attendances';

        //this.attendance = action.attendance;
        // check in/out times displayed in the greeting message template.

        //this.attendance.check_in_time = action.check_in
        //this.attendance.check_in_time = (new Date((new Date(this.attendance.check_in)).valueOf() - (new Date()).getTimezoneOffset()*60*1000)).toTimeString().slice(0,8);
        //this.attendance.check_out_time = this.attendance.check_out && (new Date((new Date(this.attendance.check_out)).valueOf() - (new Date()).getTimezoneOffset()*60*1000)).toTimeString().slice(0,8);
        this.employee_name = action.employee_name;
    },

    start: function() {
        //if (this.attendance) {
        //    this.attendance.check_out ? this.farewell_message() : this.welcome_message();
        //}
    },

    welcome_message: function() {
        var self = this;
        var now = new Date((new Date(this.attendance.check_in)).valueOf() - (new Date()).getTimezoneOffset()*60*1000);
        this.return_to_main_menu = setTimeout( function() { self.do_action(self.next_action, {clear_breadcrumbs: true}); }, 5000);

        if (now.getHours() < 5) {
            this.$('.o_hr_attendance_message_message').append(_t("Good night"));
        } else if (now.getHours() < 12) {
            if (now.getHours() < 8 && Math.random() < 0.3) {
                if (Math.random() < 0.75) {
                    this.$('.o_hr_attendance_message_message').append(_t("The early bird catches the worm"));
                } else {
                    this.$('.o_hr_attendance_message_message').append(_t("First come, first served"));
                }
            } else {
                this.$('.o_hr_attendance_message_message').append(_t("Good morning"));
            }
        } else if (now.getHours() < 17){
            this.$('.o_hr_attendance_message_message').append(_t("Good afternoon"));
        } else if (now.getHours() < 23){
            this.$('.o_hr_attendance_message_message').append(_t("Good evening"));
        } else {
            this.$('.o_hr_attendance_message_message').append(_t("Good night"));
        }
        if(this.previous_attendance_change_date){
            var last_check_out_date = new Date((new Date(this.previous_attendance_change_date)).valueOf() - (new Date()).getTimezoneOffset()*60*1000);
            if(now.valueOf() - last_check_out_date.valueOf() > 1000*60*60*24*7){
                this.$('.o_hr_attendance_random_message').html(_t("Glad to have you back, it's been a while!"));
            } else {
                if(Math.random() < 0.02){
                    this.$('.o_hr_attendance_random_message').html(_t("If a job is worth doing, it is worth doing well!"));
                }
            }
        }
    },

    farewell_message: function() {
        var self = this;
        var now = new Date((new Date(this.attendance.check_out)).valueOf() - (new Date()).getTimezoneOffset()*60*1000);
        this.return_to_main_menu = setTimeout( function() { self.do_action(self.next_action, {clear_breadcrumbs: true}); }, 5000);

        if(this.previous_attendance_change_date){
            var last_check_in_date = new Date((new Date(this.previous_attendance_change_date)).valueOf() - (new Date()).getTimezoneOffset()*60*1000);
            if(now.valueOf() - last_check_in_date.valueOf() > 1000*60*60*12){
                this.$('.o_hr_attendance_warning_message').append(_t("Warning! Last check in was over 12 hours ago.<br/>If this isn't right, please contact Human Resources."));
                clearTimeout(this.return_to_main_menu);
                this.activeBarcode = false;v
            } else if(now.valueOf() - last_check_in_date.valueOf() > 1000*60*60*8){
                this.$('.o_hr_attendance_random_message').html(_t("Another good day's work! See you soon!"));
            }
        }

        if (now.getHours() < 12) {
            this.$('.o_hr_attendance_message_message').append(_t("Have a good day!"));
        } else if (now.getHours() < 14) {
            this.$('.o_hr_attendance_message_message').append(_t("Have a nice lunch!"));
            if (Math.random() < 0.05) {
                this.$('.o_hr_attendance_random_message').html(_t("Eat breakfast as a king, lunch as a merchant and supper as a beggar"));
            } else if (Math.random() < 0.06) {
                this.$('.o_hr_attendance_random_message').html(_t("An apple a day keeps the doctor away"));
            }
        } else if (now.getHours() < 17) {
            this.$('.o_hr_attendance_message_message').append(_t("Have a good afternoon"));
        } else {
            if (now.getHours() < 18 && Math.random() < 0.2) {
                this.$('.o_hr_attendance_message_message').append(_t("Early to bed and early to rise, makes a man healthy, wealthy and wise"));
            } else {
                this.$('.o_hr_attendance_message_message').append(_t("Have a good evening"));
            }
        }
    },


    destroy: function () {
        clearTimeout(this.return_to_main_menu);
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('website_supportzayd_hr_attendance_greeting_message', GreetingMessage);

return GreetingMessage;

});

