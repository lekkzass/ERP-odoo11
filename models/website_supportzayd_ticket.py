# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp import tools
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID, tools
from random import randint
import datetime
from datetime import date, time, timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID
from dateutil import tz
import re

import logging

_logger = logging.getLogger(__name__)

AVAILABLE_PRIORITIES = [
    ('0', 'Neutral'),
    ('1', 'Low'),
    ('2', 'High Priority'),
    ('3', 'Urgent'),
]

class WebsiteSupportTicket(models.Model):
    _name = "website.supportzayd.ticket"
    _description = "Website Support Ticket @sigmarectrix"
    _order = "create_date desc"
    _rec_name = "subject"
    _inherit = ['mail.thread']
    _translate = True

    @api.multi
    def unlink(self):
        res = super(WebsiteSupportTicket, self).unlink()
        #override delete method so that will delete record of oe_chatter from database, this was an issue because after uninstallation the oe_chatter logs are not deleted from database

        for record in self:
            record_id = record.id

            self.env.cr.execute("DELETE FROM mail_message WHERE model='website.supportzayd.ticket' AND res_id = %s"%(record_id))

        return res

    @api.multi
    def unlink_on_uninstall(self):
        res = super(WebsiteSupportTicket, self).unlink()
        #override delete method so that will delete record of oe_chatter from database, this was an issue because after uninstallation the oe_chatter logs are not deleted from database
        self.env.cr.execute("DELETE FROM mail_message WHERE model='website.supportzayd.ticket'")

        return res

    @api.model
    def _read_group_state(self, states, domain, order):
        """ Read group customization in order to display all the states in the
            kanban view, even if they are empty
        """
        staff_replied_state = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                   'website_ticket_state_staff_replied')
        customer_replied_state = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                      'website_ticket_state_customer_replied')
        customer_closed = self.env['ir.model.data'].get_object('website_supportzayd',
                                                               'website_ticket_state_customer_closed')
        staff_closed = self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_staff_closed')
        exclude_states = [staff_replied_state.id, customer_replied_state.id, customer_closed.id, staff_closed.id]
        # state_ids = states._search([('id','not in',exclude_states)], order=order, access_rights_uid=SUPERUSER_ID)
        state_ids = states._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return states.browse(state_ids)

    def _default_state(self):
        return self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_open')

    def _default_approval_id(self):
        try:
            return self.env['ir.model.data'].get_object('website_supportzayd', 'no_approval_required')
        except ValueError:
            return False

    equipment_location = fields.Char(string='Equipment Location', readonly=True, force_save="1", placeholder="Eg: Bahagian Kewangan, Aras 5")
    channel = fields.Char(string="Channel", default="Manual")
    create_user_id = fields.Many2one('res.users', "Create User" )
    priority_star = fields.Selection(AVAILABLE_PRIORITIES, index=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    partner_image = fields.Binary(related='partner_id.image_medium', string="Partner image", readonly='True')
    user_id = fields.Many2one('res.users', string="Assigned to")
    person_name = fields.Char(string='Reported By')
    equipment_user = fields.Char(string='Equipment User')# changed String from 'Company location' to 'Customer' 13dec
    email = fields.Char(string="Email")
    support_email = fields.Char(string="Support Email")
    category = fields.Many2one('website.supportzayd.ticket.categories', required="True", string="Category", track_visibility='onchange')
    sub_category_id = fields.Many2one('website.supportzayd.ticket.subcategory', string="Sub Category")
    problem = fields.Many2many('problem_many2many_tags', string="Problem") # TODO this should be renamed to problem_ids because its a many2many field. but currently have no time to change too at email templates, and views
    subject = fields.Char(string="Subject")
    description = fields.Text(string="Description")
    state = fields.Many2one('website.supportzayd.ticket.states', group_expand='_read_group_state', default=_default_state,string="Status")
    state_id = fields.Integer(related='state.id', string="State ID")
    conversation_history = fields.One2many('website.supportzayd.ticket.message', 'ticket_id', string="Conversation History")
    attachment = fields.Binary(string="Attachments")
    attachment_filename = fields.Char(string="Attachment Filename")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'website.supportzayd.ticket')],
                                     string="Media Attachments")
    unattended = fields.Boolean(string="Unattended", compute="_compute_unattend", store=True, help="In 'Open' state or 'Customer Replied' state taken into consideration name changes")
    portal_access_key = fields.Char(string="Portal Access Key")
    ticket_number = fields.Integer(string="Ticket Number", readonly=True, default="5197")
    ticket_number_display = fields.Char(string="Ticket Number Display", compute="_compute_ticket_number_display", store=True)
    color = fields.Integer(string="Color") #color for usage of kanban view @hafizalwi
    company_id = fields.Many2one('res.company', string="Client", default=lambda self: self.env['res.company']._company_default_get('website.supportzayd.ticket'))
    support_rating = fields.Integer(string="Support Rating")
    support_comment = fields.Text(string="Support Comment")
    close_comment = fields.Text(string="Close Comment")
    close_time = fields.Datetime(string="Close Time")
    close_date = fields.Date(string="Close Date")
    closed_by_id = fields.Many2one('res.users', string="Closed By")
    close_lock = fields.Boolean(string="Close Lock")
    contact_num = fields.Char(string="Contact Number", help="by default will prioritize taking customer's mobile number and then phone number.")
    time_to_close = fields.Float(string="Time to close", help="seconds") #reeditted from format seconds to : @hafizalwi11jan
    time_to_close_hhmm = fields.Float(string="Time to close: ", help="hh:mm format")
    extra_field_ids = fields.One2many('website.supportzayd.ticket.field', 'wst_id', string="Extra Details")
    planned_time = fields.Datetime(string="Planned Time")
    planned_time_format = fields.Char(string="Planned Time Format", compute="_compute_planned_time_format")
    approval_id = fields.Many2one('website.supportzayd.ticket.approval', default=_default_approval_id, string="Approval")
    approval_message = fields.Text(string="Approval Message")
    approve_url = fields.Char(compute="_compute_approve_url", string="Approve URL")
    disapprove_url = fields.Char(compute="_compute_disapprove_url", string="Disapprove URL")
    cmform = fields.Char(string="CM Form")
    sla_policies_id = fields.Many2one('website.supportzayd.sla.policies', string="SLA")
    #hafizalwi 27jan2022 , for testing and calculation purpose, this section are separated from others for a while, For the next dev, if you saw spaces between columns, this is the reason why.
    sla_timer = fields.Float(string="SLA Time Remaining", help="SLA timer is in 24 hours format HH:MM",
                             compute="_compute_sla_calculation", store=True)
    sla_timer_format = fields.Char(string="SLA Timer Format", compute="_compute_sla_timer_format")
    #hafizalwi 22jun2022, adding new sla timer for each SLA, eg: sla_helpdesk,sla_onsite, and sla_total, instead of just showing total sla tiemer
    #hafizalwi 23jun2022, add temporary sla timer for using it as dependency for sla_timer
    #temporarySLA_timer = fields.Float(string="temporarySLA_timer_hidden", help="this should be hidden field, only shown for debug", compute="_compute_sla_calculation")
    sla_duration_helpdesk = fields.Float(string="Duration of Helpdesk Response Time: ", help="this is optional field, it is set only if helpdesk response time exist in SLA", compute="_compute_sla_calculation", default="0.0000000", store=True)
    sla_duration_onsite = fields.Float(string="Duration of On-Site Response Time: ", help="this is optional field, it is set only if onsite response time exist in SLA. Onsite response time means how long it takes for technician to get to customer's location", compute="_compute_sla_calculation", default="0.0000000", store=True)
    sla_duration_resolution = fields.Float(string="Duration of Resolution Response Time: ", help="This is resolution response time in SLA", compute="_compute_sla_calculation",default="0.0000000", store=True)
    #hafizalwi 20 jun creating time exceeding SLA
    sla_timer_violation_helpdesk = fields.Float(string="Time exceeding for Helpdesk SLA", help="SLA's violation for helpdesk", compute="_compute_sla_calculation", store=True)
    sla_timer_violation_onsite = fields.Float(string="Time exceeding for Onsite SLA", help="SLA's violation for onsite", compute="_compute_sla_calculation", store=True)
    sla_timer_violation_resolution = fields.Float(string="Time exceeding for Resolution SLA", help="SLA's violation for resolution", compute="_compute_sla_calculation", store=True)
    #the fields with sla_START are only saved for calculations, for now, for later, it might be put into SLA details, because in sigmarectrix excel report for helpdesk support, these variable exists
    sla_duration_helpdesk_start = fields.Datetime(string="Helpdesk Response Time Start: ", compute="_compute_sla_calculation" , store=True)
    sla_duration_onsite_start = fields.Datetime(string="Onsite Response Time Start: ", compute="_compute_sla_calculation", store=True )
    sla_duration_resolution_start = fields.Datetime(string="Resolution Response Time Start: ", compute="_compute_sla_calculation" , store=True)
    #this is for ticket timeline information, technician check-in, check-out for tickets.
    check_in = fields.Datetime('Technician Check-in', help="Time on which technician check-in for the job")
    check_out = fields.Datetime('Technician Check-out', help="Time on which technician check-out for the job")
    check_in_address = fields.Char(string="Check-in address")
    check_out_address = fields.Char(string="Check-out address")
    check_in_lat = fields.Float(string="Check-in latitude", digits = (12,15),help="Floating Precision is set to 15 (maximum for longitude and latitude)")
    check_in_long = fields.Float(string="Check-in longitude", digits = (12,15),help="Floating Precision is set to 15 (maximum for longitude and latitude)")
    check_out_lat = fields.Float(string="Check-out latitude", digits = (12,15),help="Floating Precision is set to 15 (maximum for longitude and latitude)")
    check_out_long = fields.Float(string="Check-out longitude", digits = (12,15),help="Floating Precision is set to 15 (maximum for longitude and latitude)")

    #@api.multi
    #def _check_sla_group_supportzayd(self):
    #    for team in self:
    #        if team.use_sla and not self.user_has_groups('helpdesk.group_use_sla'):
    #            self.env.ref('helpdesk.group_helpdesk_user').write({'implied_ids': [(4, self.env.ref('helpdesk.group_use_sla').id)]})
    #        if team.use_sla:
    #            self.env['helpdesk.sla'].with_context(active_test=False).search([('team_id', '=', team.id), ('active', '=', False)]).write({'active': True})
    #        else:
    #            self.env['helpdesk.sla'].search([('team_id', '=', team.id)]).write({'active': False})
    #            if not self.search_count([('use_sla', '=', True)]):
    #                self.env.ref('helpdesk.group_helpdesk_user').write({'implied_ids': [(3, self.env.ref('helpdesk.group_use_sla').id)]})
    #                self.env.ref('helpdesk.group_use_sla').write({'users': [(5, 0, 0)]})

    def find_difference_in_time_YminusX(self, varX, varY):
        data1 = datetime.datetime.strptime(varX, '%Y-%m-%d %H:%M:%S')
        data2 = datetime.datetime.strptime(varY, '%Y-%m-%d %H:%M:%S')
        diff = data2 - data1
        days, seconds = diff.days, diff.seconds
        hours = (seconds / 3600) + (days*24)
        return hours


    @api.one
    @api.depends('sla_policies_id.SLA_helpdesk_response_time', 'sla_policies_id.SLA_onsite_response_time',
                 'sla_policies_id.SLA_resolution_response_time', 'create_date', 'open_case','check_in','check_out')
    def _compute_sla_calculation(self):
        self.sla_timer = self.sla_policies_id.SLA_tot_allocated #set sla timer to total allocated first, then minus later in the conditional ifs

        if self.sla_policies_id.SLA_helpdesk_response_time > 0.0 and self.create_date and self.open_case:
            helpdesk_timer = self.find_difference_in_time_YminusX(self.open_case, self.create_date)
            self.sla_duration_helpdesk = helpdesk_timer
            self.sla_duration_helpdesk_start = self.open_case

            if 0.0 < self.sla_duration_helpdesk <= self.sla_policies_id.SLA_helpdesk_response_time:  # let say helpdesk response duration does not exist sla_heldpesk_Reponse_time in sla_policies_id
                #self.sla_timer = self.sla_timer - self.sla_policies_id.SLA_helpdesk_response_time
                #check if this(helpdesk) is the last point in sla calculation, by checking for future point exist or not
                if not self.sla_policies_id.SLA_onsite_response_time > 0.0 and not self.sla_policies_id.SLA_resolution_response_time > 0.0:
                    self.sla_timer = self.sla_timer - self.sla_duration_helpdesk
                else:
                    self.sla_timer = self.sla_timer - self.sla_policies_id.SLA_helpdesk_response_time

            elif self.sla_duration_helpdesk > 0.0 and self.sla_duration_helpdesk > self.sla_policies_id.SLA_helpdesk_response_time:  # if the helpdesk response duration exceed the allocated given time
                self.sla_timer_violation_helpdesk = self.sla_policies_id.SLA_helpdesk_response_time -  self.sla_duration_helpdesk
                self.sla_timer = self.sla_timer - self.sla_duration_helpdesk

        if self.sla_policies_id.SLA_onsite_response_time > 0.0 and self.create_date and self.check_in:
            hours = self.find_difference_in_time_YminusX(self.create_date, self.check_in)
            self.sla_duration_onsite = hours  # do casting(float) on 'diff' variable
            self.sla_duration_onsite_start = self.create_date
            if 0.0 < self.sla_duration_onsite <= self.sla_policies_id.SLA_onsite_response_time:
                #self.sla_timer = self.sla_timer - self.sla_policies_id.SLA_onsite_response_time
                if not self.sla_policies_id.SLA_resolution_response_time > 0.0:
                    self.sla_timer = self.sla_timer - self.sla_duration_onsite
                else:
                    self.sla_timer = self.sla_timer - self.sla_policies_id.SLA_onsite_response_time
            elif self.sla_duration_onsite > 0.0 and self.sla_duration_onsite > self.sla_policies_id.SLA_onsite_response_time:  # if the helpdesk response duration exceed the allocated given time
                self.sla_timer_violation_onsite = self.sla_policies_id.SLA_onsite_response_time - self.sla_duration_onsite
                self.sla_timer = self.sla_timer - self.sla_duration_onsite

        #actually we dont need if in below statement because resolution is required field, but incase it will be change later to not required i prepared this if @hafizalwi jun 2022
        if self.sla_policies_id.SLA_resolution_response_time > 0.0 and self.check_in and self.check_out:
            hours = self.find_difference_in_time_YminusX(self.check_in, self.check_out)
            self.sla_duration_resolution = hours  # do casting(float) on 'diff' variable
            self.sla_duration_resolution_start = self.check_in
            if 0.0 < self.sla_duration_resolution <= self.sla_policies_id.SLA_resolution_response_time:
                #by default this is the last point because we only have 3 sla for now, resolution is the last point, if other exist or not exist, this is the last point.
                self.sla_timer = self.sla_timer - self.sla_duration_resolution

            elif self.sla_duration_resolution > 0.0 and self.sla_duration_resolution > self.sla_policies_id.SLA_resolution_response_time:  # if the helpdesk response duration exceed the allocated given time
                self.sla_timer_violation_resolution = self.sla_policies_id.SLA_resolution_response_time - self.sla_duration_resolution
                self.sla_timer = self.sla_timer - self.sla_duration_resolution

    sla_active = fields.Boolean(string="SLA Active")
    item = fields.Many2one('website.supportzayd.ticket.item', string='Equipment (Serial Number)', help="To search, use serial number as referrence")
    sla_alert_ids = fields.Many2many('website.supportzayd.sla.alert', string="SLA Alerts", help="Keep record of SLA alerts sent so we do not resend them")
    assign_date = fields.Date(string='Assigned Date')
    open_case = fields.Datetime(string='Open Case Time', required=True)
    address = fields.Char(string='Address')
    department = fields.Char(string='Department') #removed department @hafizalwi10dec
    prob_solve_time = fields.Datetime(string='Date of Completion')
    sla_time_solve = fields.Float(string='SLA Total Time')
    #model = fields.Many2one('website.supportzayd.ticket.item', string='Model')#TO-DO Tested uncomment this on 17 nov 2021, it was commented before.
    compute_field = fields.Boolean(string="check field", compute='get_user') #This is a compute variable to filter data according to groups_id @hafizalwi16nov
    helpdesk_response_time = fields.Datetime(string="Helpdesk response time: ")
    problem_resolution_time = fields.Datetime(string="Problem resolution time: ")
    is_paused = fields.Boolean(string="SLA is paused/has been paused", default=False)


    @api.depends ('time_to_close')
    def conv_time_to_close(self):
        vals = self.time_to_close.split(':')
        t, hours = divmod(float(vals[0]), 24)
        t, minutes = divmod(float(vals[1]), 60)
        minutes = minutes / 60.0
        return hours + minutes

    @api.model
    def get_closedticket_today_count(self):
        total_closed = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.close_time:
                date1 = datetime.datetime.strptime(record.close_time, DEFAULT_SERVER_DATETIME_FORMAT ) # need to convert "record.create_date" which is in str format in python, into datetime to be able to make conditional if
                date2 = datetime.datetime.today()
                new_date2 = date2.replace(hour=0, minute=0, second=0)#change it so that the comparison will start from today at oo:oo which means midnight
                if record.state.name in ['Customer Closed', 'Staff Closed'] and date1 > new_date2: #check later if this code includes the date from yesterday\
                    total_closed = total_closed + 1
        return total_closed

    @api.model
    def get_closedticket_week_count(self):
        total_closed = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.close_time:
                date1 = datetime.datetime.strptime(record.close_time, DEFAULT_SERVER_DATETIME_FORMAT) # need to convert "record.create_date" which is in str format in python, into datetime to be able to make conditional if
                date2 = datetime.datetime.now()
                new_date2= date2.replace(hour=23, minute=59, second=59) #convert datetime to today at end of day (11:59pm), and then minus 7 days from the date, eg: it will show data from last sunday to this saturday
                if record.state.name in ['Customer Closed', 'Staff Closed'] and date1 > (new_date2-timedelta(days=7)): #according to this logic, it will start from 12am last 7 days, notice the operator show > means not including 23:59pm from last week
                    total_closed = total_closed + 1

        return total_closed

    @api.model
    def get_closedticket_month_count(self):
        total_closed = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.close_time:
                datetime1 = datetime.datetime.strptime(record.close_time, DEFAULT_SERVER_DATETIME_FORMAT) # need to convert "record.create_date" which is in str format in python, into datetime to be able to make conditional if
                date1 = datetime1.date()
                d = datetime.datetime.now().date()
                last_day_of_month = datetime.date(d.year + (d.month == 12),(d.month + 1 if d.month < 12 else 1), 1) - datetime.timedelta(1) #this is in date() format not datetime()
                d2 = datetime.datetime.now().date()
                first_day_of_month =d2.replace(day=1)
                if record.state.name in ['Customer Closed', 'Staff Closed'] and date1 <= last_day_of_month and date1>=first_day_of_month : #according to this logic, it will start from 12am last 7 days, notice the operator show > means not including 23:59pm from last week
                    total_closed = total_closed + 1
        return total_closed

    @api.model
    def get_openticket_count(self):
        total_open = 0
        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied']: #later ask Helpdesk if they want the open to include other state such as "awaiting approval", "approval accepted", etc except "closed" state.
                total_open = total_open + 1

        return total_open


    @api.one
    def get_priority_star_string(self):
        string_priority = dict(self._fields['priority_star'].selection).get(self.priority_star)
        return string_priority

    @api.model
    def get_highpriorityticket_count(self):
        total_highpriority = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.priority_star == '2':
                total_highpriority = total_highpriority + 1

        return total_highpriority

    @api.model
    def get_urgentticket_count(self):
        total_urgent = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.priority_star == '3':
                total_urgent = total_urgent + 1

        return total_urgent

    @api.model
    def get_failedSLA_count(self):
        total_failed = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.sla_timer < 0:
                total_failed = total_failed + 1

        return total_failed

    @api.model
    def get_failedSLA_highpriority_count(self):
        total_failed = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.sla_timer < 0 and record.priority_star == '2':  # if the sla_timer is finished and priority is 4(High Prio), then count it as failed SLA with high priority ticket
                total_failed = total_failed + 1

        return total_failed

    @api.model
    def get_failedSLA_urgent_count(self):
        total_failed = 0
        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.sla_timer < 0 and record.priority_star == '3':  # if the sla_timer is finished and priority is 4(High Prio), then count it as failed SLA with high priority ticket
                total_failed = total_failed + 1
        return total_failed

    @api.model
    def get_average_openhours(self):
        #average = 0
        count=0
        total=0
        diff_format_string="00:00"
        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied']:
                # conceptually the logic is => total = total + (datenow - record.create_date)/count
                data1 = datetime.datetime.now()
                data2 = datetime.datetime.strptime(record.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
                diff = data1 - data2
                days, seconds = diff.days, diff.seconds
                hours = seconds / 3600 + (days*24)
                diff_float = float(str(hours))  # do casting(float) on 'diff' variable
                total = total + diff_float  # return total value in float format
                count += 1  # return value of count to be used in average

            if count: #so that it wont throw exception when total is divided by zero(incase no tickets for this section are opened) in javascript console browser.
                average = total / count
                diff_format = (str(datetime.timedelta(hours=average))[:-3])  # convert float to HH:MM format

                #to remove 'display' of microseconds, such as 1day,01:20:30.123123 apply the code below,
                diff_format_string = str(diff_format).split(".")[0]

        return diff_format_string

    @api.model
    def get_average_openhours_highpriority(self):
        #average = 0
        count=0
        total=0
        diff_format_string = "00:00"
        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.priority_star == '2':
                 #average = average + record.time_to_close_seconds

                # conceptually the logic is => total = total + (datenow - record.create_date)/count
                data1 = datetime.datetime.now()
                data2 = datetime.datetime.strptime(record.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
                diff = data1 - data2

                days, seconds = diff.days, diff.seconds
                hours = seconds / 3600 + (days*24)
                #minutes = (seconds % 3600) // 60
                diff_float = float(str(hours))  # do casting(float) on 'diff' variable

                total = total + diff_float  # return total value in float format
                count += 1  # return value of count to be used in average

            if count: #so that it wont throw exception when total is divided by zero(incase no tickets for this section are opened) in javascript console browser.
                average = total / count
                diff_format = (str(datetime.timedelta(hours=average))[:-3])  # convert float to HH:MM format
                diff_format_string = str(diff_format).split(".")[0]

        return diff_format_string

    @api.model
    def get_average_openhours_urgent(self):
        #average = 0
        count=0
        total=0
        diff_format_string = "00:00"
        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.state.name in ['Open', 'Customer Replied'] and record.priority_star == '3':
                 #average = average + record.time_to_close_seconds

                # conceptually the logic is => total = total + (datenow - record.create_date)/count
                data1 = datetime.datetime.now()
                data2 =  datetime.datetime.strptime(record.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
                diff = data1 - data2

                days, seconds = diff.days, diff.seconds
                hours = seconds / 3600 + (days*24)

                #minutes = (seconds % 3600) // 60
                #diff_float = float(str(hours) + "." + str(minutes))  # do casting(float) on 'diff' variable
                diff_float = float(str(hours))  # do casting(float) on 'diff' variable

                total = total + diff_float  # return total value in float format
                count += 1  # return value of count to be used in average


            if count: #so that it wont throw exception when total is divided by zero(incase no tickets for this section are opened) in javascript console browser.
                average = total / count
                diff_format = (str(datetime.timedelta(hours=average))[:-3])  # convert float to HH:MM format
                diff_format_string = str(diff_format).split(".")[0]

        return diff_format_string

    @api.model
    def get_success_rate_today(self):
        countClosed = 0
        countSLAfailed = 0
        success_rate = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.close_time:
                date1 = datetime.datetime.strptime(record.close_time, DEFAULT_SERVER_DATETIME_FORMAT)  # need to convert "record.create_date" which is in str format in python, into datetime to be able to make conditional if
                date2 = datetime.datetime.today()
                start_date = date2.replace(hour=0, minute=0, second=0)
                date3 = datetime.datetime.today()
                end_date = date3.replace(hour=23, minute=59, second=59)

                if record.state.name in ['Staff Closed', 'Customer Closed'] and date1>=start_date and date1 <= end_date :
                    countClosed += 1
                    if record.sla_timer < 0:
                        countSLAfailed += 1
        if countSLAfailed > 0 and countClosed > countSLAfailed:
            success_rate = countSLAfailed/countClosed * 100 #imagine countclosed is 2 today, and slafailed is 1 today. 1/2 = 50% successrate
        elif countSLAfailed == countClosed:
            success_rate = 0 #imagine if 0 count closed and 0 sla failed today. success rate =0,if 2 countclosed and 2sla failed, success rate = 0%
        return int(success_rate)

    @api.model
    def get_success_rate_week(self):
        countClosed = 0
        countSLAfailed = 0
        success_rate = 0

        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.close_time:
                date1 = datetime.datetime.strptime(record.close_time, DEFAULT_SERVER_DATETIME_FORMAT)  # need to convert "record.create_date" which is in str format in python, into datetime to be able to make conditional if
                date2 = datetime.datetime.today()
                start_date = date2.replace(hour=23, minute=59, second=59)

                if record.state.name in ['Staff Closed', 'Customer Closed'] and date1 >= (start_date-timedelta(days=7)):
                    countClosed += 1
                    if record.sla_timer < 0:
                        countSLAfailed += 1
        if countSLAfailed > 0 and countClosed>countSLAfailed:
            success_rate = countSLAfailed/countClosed * 100 #imagine countclosed is 2 today, and slafailed is 1 today. 1/2 = 50% successrate

        elif countSLAfailed == countClosed:
            success_rate = 0 #imagine if 0 count closed and 0 sla failed today. success rate =0,if 2 countclosed and 2sla failed, success rate = 0%
        return int(success_rate)

    @api.model
    def get_success_rate_month(self):
        countClosed = 0
        countSLAfailed = 0
        success_rate = 0
        for record in self.env['website.supportzayd.ticket'].search([]):
            if record.close_time:
                datetime1 = datetime.datetime.strptime(record.close_time, DEFAULT_SERVER_DATETIME_FORMAT)  # need to convert "record.create_date" which is in str format in python, into datetime to be able to make conditional if
                date1 = datetime1.date() #convert datetime to date
                d = datetime.datetime.now().date()
                last_day_of_month = datetime.date(d.year + (d.month == 12), (d.month + 1 if d.month < 12 else 1),
                                                  1) - datetime.timedelta(1)  # this is in date() format not datetime()
                d2 = datetime.datetime.now().date()
                first_day_of_month = d2.replace(day=1)
                if record.state.name in ['Staff Closed', 'Customer Closed'] and (
                        first_day_of_month <= date1 <= last_day_of_month) :
                    countClosed += 1
                    if record.sla_timer < 0:
                        countSLAfailed += 1

        if countSLAfailed > 0 and countClosed>countSLAfailed:
            success_rate = countSLAfailed/countClosed * 100 #imagine countclosed is 2 today, and slafailed is 1 today. 1/2 = 50% successrate
        elif countSLAfailed == countClosed:
            success_rate= 0 #imagilne if 0 count closed and 0 sla failed today. success rate =0,if 2 countclosed and 2sla failed, success rate = 0%
        return int(success_rate)



    @api.onchange('category')
    @api.multi
    def _onchange_category(self):
        #deactivate sla based on conditions, because check_out is the last things done for resolution sla
        #for record in self:
        #    record.sub_category_id.parent_category_id.id = record.category.id
        self.ensure_one()
        #_category_ids = []
        for record in self:
            record.write({ 'sub_category_id.parent_category_id.id': [6,0, record.category.id] })


    @api.onchange('check_out')
    def _onchange_check_out(self):
        #deactivate sla based on conditions, because check_out is the last things done for resolution sla
        if self.sla_policies_id.SLA_resolution_response_time > 0.0 and self.check_in and self.check_out:
            self.sla_active = False

    @api.onchange('sla_policies_id')
    def _onchange_sla_policies_id(self):
        if self.open_case and self.sla_active is True:
            self.sla_time_solve = self.sla_policies_id.SLA_tot_allocated
            self.sla_timer = self.sla_policies_id.SLA_tot_allocated
            #if condition below, if helpesk response time is assigned, then
            #if self.sla_policies_id.SLA_helpdesk_response_time > 0 :
            #    self.sla_timer = self.sla_policies_id.SLA_tot_allocated
            #else:
            #    self.sla_timer = self.sla_policies_id.SLA_tot_allocated

        elif self.sla_active is False and self.open_case:
            self.sla_time_solve = self.sla_policies_id.SLA_tot_allocated
            self.sla_timer = 0 #set to 0 if ticket is not active and sla_policies_id triggers onchanged

    @api.onchange('sla_active') #this means if we literally clicks on the sla_active (not pause resume sla), because pause resume sla can check or not check the checkbox too
    #create a new fucntion here, so that the timer wont reset(because remember we are using datetime now, so each time we click on the sla_Active datetime now will triggers, this is not ideal for pausing sla, because we want the timer to reset from the time it pauses, not fetching new one from datetime.now
    def _onchange_sla_active(self):

        #check if sla_active is active or not, if it is not active, set the is paused to true
        #this is important for the auto sla features not to misunderstand and reactivated paused SLA which might be done on purpose.
        if self.sla_active is False:
            self.is_paused = True

        if self.sla_active is True:
            self.is_paused = False

        # @hafizalwi jun2022
        # check if the sla_active is false, and then the sla_timesolve if is not 0.0, because if sla_timesolve is 0 means nothing have been done yet on sla and sla policies id
        if self.open_case and self.sla_policies_id and self.sla_active is True and self.sla_timer == 0.0:
            #check if sla helpdesk response time is true, if is true we will show that the difference between time is opencase and now
            self.sla_timer = self.sla_policies_id.SLA_tot_allocated
        elif self.sla_policies_id and self.sla_active is True and self.open_case:# means if we have sla_policeis id selected, just dont recalculate it anymore. but do pause resume action
            self.sla_active = True
        elif self.sla_policies_id and self.sla_active is False and self.open_case:
            self.sla_active = False
        else:
            if not self.open_case and self.sla_active:
                self.sla_active = False
                return {'value': {},
                        'warning': {'title': 'Alert', 'message': 'Please fill in "Open Case Time" field first.'}}
            elif not self.sla_policies_id and self.sla_active:
                self.sla_active = False
                return {'value': {}, 'warning': {'title': 'Alert', 'message': 'Please select SLA.'}}
            elif not self.create_date and self.sla_policies_id.SLA_helpdesk_response_time > 0.0 and self.sla_active: # more than 0 means sla response time is set. eg: 00:01 is more than 0
                self.sla_active = False
                return {'value': {}, 'warning': {'title': 'Alert', 'message': 'The selected SLA ID have SLA response time. To continue, please create the ticket first!'}}
            elif self.sla_active and self.open_case:
                #clean the helpdesk_response timer if there is no sla_response time for that sla_policies_id
                #if self.sla_policies_id.SLA_helpdesk_response_time == 0.0:
                self.sla_duration_helpdesk = 0

                if self.create_date and self.sla_policies_id.SLA_helpdesk_response_time > 0.0: #if create_date exist, this situation is happens if the sla is editted after created
                    data1 = datetime.datetime.strptime(self.create_date, '%Y-%m-%d %H:%M:%S')
                    data2 = datetime.datetime.strptime(self.open_case, '%Y-%m-%d %H:%M:%S')
                    diff = data1 - data2
                    days, seconds = diff.days, diff.seconds
                    hours = (seconds / 3600) + (days * 24)
                    self.sla_duration_helpdesk = (float(str(hours)))  # do casting(float) on 'diff' variable
                    self.sla_duration_helpdesk_start = self.open_case
                    self.sla_timer = self.sla_policies_id.SLA_tot_allocated


    def compute_sla_timer_formula(self):
        #this function should only be used if heldpesk response exist, because it calculates time based on open_case and datetime.now
        data1 = datetime.datetime.now()  # here we get datetime.now to calculatec the sla timer
        data2 = datetime.datetime.strptime(self.open_case, '%Y-%m-%d %H:%M:%S')
        diff = data1 - data2  # difference between datetime.now and opencase
        days, seconds = diff.days, diff.seconds
        hours = (seconds / 3600) + (days * 24)
        self.sla_timer = self.sla_policies_id.SLA_tot_allocated - (float(
            str(hours)))
        return self.sla_timer

    @api.multi
    @api.depends('check_in', 'check_out', 'open_case', 'create_date')
    def deactivate_sla(self):
        for rec in self:
            #now shut off SLA if all fields required for SLA calculation have been filled, either do this approach or onchange, difference will be on the runtime and application
            if rec.check_in and rec.check_out and rec.open_case:
                #set sla_active to false
                rec.sla_active = False

    @api.one
    @api.depends('ticket_number')
    def _compute_ticket_number_display(self):
        if self.ticket_number:
            self.ticket_number_display = str("TN") + str(self.id) + "-" + datetime.datetime.today().strftime(
                '%Y%m%d') + "-" + "{:,}".format(self.ticket_number)
        else:
            self.ticket_number_display = self.id

    @api.model
    def create(self, vals):
        new_id = super(WebsiteSupportTicket, self).create(vals)
        new_id.ticket_number = new_id.company_id.next_support_ticket_number
        # Add one to the next ticket number
        new_id.company_id.next_support_ticket_number += 1

        return new_id

    @api.multi
    @api.depends('subject', 'ticket_number')
    def name_get(self):
        res = []
        for record in self:
            if record.subject and record.ticket_number:
                name = record.subject + " (#" + record.ticket_number_display + ")"
            else:
                name = record.subject
            res.append((record.id, name))
        return res

    @api.one
    @api.depends('sla_timer')
    def _compute_sla_timer_format(self):
        # Display negative hours in a positive format
        self.sla_timer_format = '{0:02.0f}:{1:02.0f}'.format(*divmod(abs(self.sla_timer) * 60, 60))

    @api.model
    def update_sla_timer_2(self):


        # Subtract 1 minute from the timer of all active SLA tickets, this includes going into negative
        for active_sla_ticket in self.env['website.supportzayd.ticket'].search([
            ('sla_active', '=', True),
            ('sla_policies_id', '!=', False),
        ]):

            # If we only countdown during business hours
            if active_sla_ticket.sla_policies_id.countdown_condition == 'business_only':
                # Check if the current time aligns with a timeslot in the settings,
                # setting has to be set for business_only or UserError occurs
                setting_business_hours_id = self.env['ir.default'].get('website.supportzayd.settings',
                                                                       'business_hours_id')
                current_hour = datetime.datetime.now().hour
                current_minute = datetime.datetime.now().minute / 60
                current_hour_float = current_hour + current_minute
                day_of_week = datetime.datetime.now().weekday()
                during_work_hours = self.env['resource.calendar.attendance'].search(
                    [('calendar_id', '=', setting_business_hours_id), ('dayofweek', '=', day_of_week),
                     ('hour_from', '<', current_hour_float), ('hour_to', '>', current_hour_float)])

                # If holiday module is installed take into consideration
                holiday_module = self.env['ir.module.module'].search(
                    [('name', '=', 'hr_public_holidays'), ('state', '=', 'installed')])
                if holiday_module:
                    holiday_today = self.env['hr.holidays.public.line'].search(
                        [('date', '=', datetime.datetime.now().date())])
                    if holiday_today:
                        during_work_hours = False

                if during_work_hours:
                    active_sla_ticket.sla_timer -= 1 / 60
            elif active_sla_ticket.sla_policies_id.countdown_condition == '24_hour':

                active_sla_ticket.sla_timer -= 1 / 60


    def pause_sla(self):
        self.sla_active = False
        self.is_paused = True

    def resume_sla(self):
        self.sla_active = True
        self.is_paused = False
    @api.one
    @api.depends('planned_time')
    def _compute_planned_time_format(self):

        # If it is assigned to the partner, use the partners timezone and date formatting
        if self.planned_time and self.partner_id and self.partner_id.lang:
            partner_language = self.env['res.lang'].search([('code', '=', self.partner_id.lang)])[0]

            my_planned_time = datetime.datetime.strptime(self.planned_time, DEFAULT_SERVER_DATETIME_FORMAT)

            # If we have timezone information translate the planned date to local time otherwise UTC
            if self.partner_id.tz:
                my_planned_time = my_planned_time.replace(tzinfo=tz.gettz('UTC'))
                local_time = my_planned_time.astimezone(tz.gettz(self.partner_id.tz))
                self.planned_time_format = local_time.strftime(
                    partner_language.date_format + " " + partner_language.time_format) + " " + self.partner_id.tz
            else:
                self.planned_time_format = my_planned_time.strftime(
                    partner_language.date_format + " " + partner_language.time_format) + " UTC"

        else:
            self.planned_time_format = self.planned_time

    @api.one
    def _compute_approve_url(self):
        self.approve_url = "/supportzayd/approve/" + str(self.id)

    @api.one
    def _compute_disapprove_url(self):
        self.disapprove_url = "/supportzayd/disapprove/" + str(self.id)

    #@api.onchange('sub_category_id')#9dec! commented out as per new user requirements testing @hafizalwi9dec
    #def _onchange_sub_category_id(self):
    #    self.item = False
    #    if self.sub_category_id:
    #
    #        add_extra_fields = []
    #
    #        for extra_field in self.sub_category_id.additional_field_ids:
    #            add_extra_fields.append((0, 0, {'name': extra_field.name}))

    #        self.update({
    #            'extra_field_ids': add_extra_fields,
    #        })

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.zip or self.partner_id.country_id.name or self.partner_id.street or self.partner_id.street2 or self.partner_id.city or self.partner_id.state_id.name:
                if self.partner_id.zip:
                    zip = self.partner_id.zip + ", "
                else:
                    zip = ""
                if self.partner_id.country_id:
                    country = self.partner_id.country_id.name + ", "
                else:
                    country = ""
                if self.partner_id.street:
                    street = self.partner_id.street + ", "
                else:
                    street = ""
                if self.partner_id.street2:
                    street2 = self.partner_id.street2 + ", "
                else:
                    street2 = ""
                if self.partner_id.city:
                    city = self.partner_id.city + ", "
                else:
                    city = ""
                if self.partner_id.state_id:
                    state = self.partner_id.state_id.name
                else:
                    state = ""


                address = "{street}{street2}{city}{zip}{state}".format(
                    zip=zip,
                    country=country,
                    street=street,
                    street2=street2,
                    city=city,
                    state=state)

            else:
                address = ""
        else:
            address = ""
        # self.person_name = self.partner_id.name
        self.email = self.partner_id.email
        if self.partner_id.mobile:
            self.contact_num = self.partner_id.mobile
        elif self.partner_id.phone:
            self.contact_num = self.partner_id.phone
        self.address = address
        self.department = self.item.location_id.name

    @api.onchange('item') #this is to autofill other important field, upon filling model.item @hafizalwi9Dec
    def _onchange_item(self):
        self.partner_id = ""
        self.equipment_user = ""
        self.contact_num= ""
        self.email= ""
        self.department= ""
        self.address= ""
        self.person_name= ""
        self.equipment_location = ""


        if self.item:
            #check if data for location exist, fill the data
            if self.item.customer:
                self.equipment_location = self.item.customer.name
                self.partner_id = self.item.customer
                self.equipment_user = self.item.user


            #below is boilerplate as in onchange ('partner_id'), if have free time, change it to function.
            if self.partner_id.zip or self.partner_id.country_id.name or self.partner_id.street or self.partner_id.street2 or self.partner_id.city or self.partner_id.state_id.name:
                if self.partner_id.zip:
                    zip = self.partner_id.zip + ", "
                else:
                    zip = ""
                if self.partner_id.country_id:
                    country = self.partner_id.country_id.name + ", "
                else:
                    country = ""
                if self.partner_id.street:
                    street = self.partner_id.street + ", "
                else:
                    street = ""
                if self.partner_id.street2:
                    street2 = self.partner_id.street2 + ", "
                else:
                    street2 = ""
                if self.partner_id.city:
                    city = self.partner_id.city + ", "
                else:
                    city = ""
                if self.partner_id.state_id:
                    state = self.partner_id.state_id.name
                else:
                    state = ""


                address = "{street}{street2}{city}{zip}{state}".format(
                    zip=zip,
                    country=country,
                    street=street,
                    street2=street2,
                    city=city,
                    state=state)

            else:
                address = ""


            self.email = self.partner_id.email
            if self.partner_id.mobile:
                self.contact_num = self.partner_id.mobile
            elif self.partner_id.phone:
                self.contact_num = self.partner_id.phone
            self.department = self.item.location_id.name
            self.address = address



    def message_new(self, msg, custom_values=None):
        """ Create new support ticket upon receiving new email"""

        defaults = {'support_email': msg.get('to'), 'subject': msg.get('subject')}

        # Extract the name from the from email if you can
        if "<" in msg.get('from') and ">" in msg.get('from'):
            start = msg.get('from').rindex("<") + 1
            end = msg.get('from').rindex(">", start)
            from_email = msg.get('from')[start:end]
            from_name = msg.get('from').split("<")[0].strip()
            defaults['person_name'] = from_name
        else:
            from_email = msg.get('from')

        defaults['email'] = from_email
        defaults['channel'] = "Email"

        # Try to find the partner using the from email
        search_partner = self.env['res.partner'].sudo().search([('email', '=', from_email)])
        if len(search_partner) > 0:
            defaults['partner_id'] = search_partner[0].id
            defaults['person_name'] = search_partner[0].name

        defaults['description'] = tools.html_sanitize(msg.get('body'))

        # Assign to default category
        setting_email_default_category_id = self.env['ir.default'].get('website.supportzayd.settings',
                                                                       'email_default_category_id')

        if setting_email_default_category_id:
            defaults['category'] = setting_email_default_category_id

        return super(WebsiteSupportTicket, self).message_new(msg, custom_values=defaults)

    def message_update(self, msg_dict, update_vals=None):
        """ Override to update the support ticket according to the email. """

        if self.close_lock:
            # Send lock email
            setting_ticket_lock_email_template_id = self.env['ir.default'].get('website.supportzayd.settings',
                                                                               'ticket_lock_email_template_id')
            if setting_ticket_lock_email_template_id:
                mail_template = self.env['mail.template'].browse(setting_ticket_lock_email_template_id)
            else:
                # BACK COMPATABLITY FAIL SAFE
                mail_template = self.env['ir.model'].get_object('website_supportzayd', 'support_ticket_close_lock')

            mail_template.send_mail(self.id, True)

            return False

        body_short = tools.html_sanitize(msg_dict['body'])
        # body_short = tools.html_email_clean(msg_dict['body'], shorten=True, remove=True)

        # Add to message history to keep HTML clean
        self.conversation_history.create({'ticket_id': self.id, 'by': 'customer', 'content': body_short})

        # If the to email address is to the customer then it must be a staff member
        if msg_dict.get('to') == self.email:
            change_state = self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_staff_replied')
        else:
            change_state = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                'website_ticket_state_customer_replied')

        self.state = change_state.id

        return super(WebsiteSupportTicket, self).message_update(msg_dict, update_vals=update_vals)

    @api.one
    @api.depends('state')
    def _compute_unattend(self):
        # BACK COMPATABLITY Use open and customer reply as default unattended states
        opened_state = self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_open')
        customer_replied_state = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                      'website_ticket_state_customer_replied')

        if self.state == opened_state or self.state == customer_replied_state or self.state.unattended == True:
            self.unattended = True

    @api.multi
    def request_approval(self):

        approval_email = self.env['ir.model.data'].get_object('website_supportzayd', 'support_ticket_approval')

        values = self.env['mail.compose.message'].generate_email_for_composer(approval_email.id, [self.id])[self.id]

        request_message = values['body']

        return {
            'name': "Request Approval",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.supportzayd.ticket.compose',
            'context': {'default_ticket_id': self.id, 'default_email': self.email, 'default_subject': self.subject,
                        'default_approval': True, 'default_body': request_message},
            'target': 'new'
        }

    @api.multi
    def open_reply_ticket_wizard(self):

        context = {'default_ticket_id': self.id, 'default_partner_id': self.partner_id.id, 'default_email': self.email,
                   'default_subject': self.subject}

        if self.partner_id.ticket_default_email_cc:
            context['default_email_cc'] = self.partner_id.ticket_default_email_cc
        if self.partner_id.ticket_default_email_body:
            context['default_body'] = self.partner_id.ticket_default_email_body

        return {
            'name': "Support Ticket Compose",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.supportzayd.ticket.compose',
            'context': context,
            'target': 'new'
        }

    @api.multi
    def open_close_ticket_wizard(self):
        return {
            'name': "Close Support Ticket",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.supportzayd.ticket.close',
            'context': {'default_ticket_id': self.id},
            'target': 'new'
        }

    @api.multi
    def merge_ticket(self):
        return {
            'name': "Merge Support Ticket",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.supportzayd.ticket.merge',
            'context': {'default_ticket_id': self.id},
            'target': 'new'
        }


    @api.model
    def _needaction_domain_get(self):
        open_state = self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_open')
        custom_replied_state = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                    'website_ticket_state_customer_replied')
        return ['|', ('state', '=', open_state.id), ('state', '=', custom_replied_state.id)]

    @api.depends('priority_star', 'partner_id', 'sla_policies_id', 'sla_active', 'create_date')
    @api.multi
    def _check_auto_sla_policies(self):

        setting_allow_auto_sla_criteria = self.env['ir.default'].get('website.supportzayd.settings', 'allow_auto_sla_criteria')
        print("does this get printed? debug check auto sla policies function")

        for ticket in self:
            if setting_allow_auto_sla_criteria:
                # Check if fields in create ticket met the conditions in criteria of website.supportzayd.sla.policies
                #dom domain is to search for the current ticket SLA's whether the criteria is met or not in the sla.policies

                dom = [ '&', ('minimum_priority', '<=', ticket.priority_star),'&', '|', ('category_id', '=', ticket.category.id), ('category_id', '=', False),
                        '|', ('partner_ids', 'child_of', ticket.partner_id.id),
                        '|', ('partner_ids', 'parent_of', ticket.partner_id.id), ('partner_ids', '=', False)]

                #for whatever the fuck reason, it is hard to get it done with nested domain, so i will just fucking make multiple call which will reduce performance, but we dont have much time to waste on this. so just go with it
                sla = ticket.env['website.supportzayd.sla.policies'].search(dom, limit=1) #search(dom, limit=1)

                #now lets apply the changes on tickets and automatically assign SLA infos based on criteria met
                if sla and ticket.sla_policies_id.id != sla.id:
                    ticket.sla_policies_id = sla.id
                    ticket.sla_active = True
                    ticket.sla_time_solve = sla.SLA_tot_allocated
                #else if conditions are not met, just empty the fucking sla.
                elif sla and ticket.sla_policies_id.id == sla.id:
                    ticket.sla_policies_id = sla.id
                    ticket.sla_active = True
                    ticket.sla_time_solve = sla.SLA_tot_allocated
                else:
                    ticket.sla_policies_id = False
                    ticket.sla_active = False
                    ticket.sla_time_solve = False

    @api.model
    def create(self, vals):
        # Get next ticket number from the sequence
        vals['ticket_number'] = self.env['ir.sequence'].next_by_code('website.supportzayd.ticket')

        new_id = super(WebsiteSupportTicket, self).create(vals)
        new_id.portal_access_key = randint(1000000000, 2000000000)
        ticket_open_email_template = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                          'website_ticket_state_open').mail_template_id
        ticket_open_email_template.send_mail(new_id.id, True)
        setting_auto_create_contact = self.env['ir.default'].get('website.supportzayd.settings', 'auto_create_contact')

        if setting_auto_create_contact and new_id.person_name and new_id.email and not new_id.partner_id:
            new_partner = self.env['res.partner'].sudo().create({'name': new_id.person_name, 'email': new_id.email})
            new_id.partner_id = new_partner.id

        # SLA business
        # Update sla status as long as it is state is not 'staff_closed', or 'customer_closed'
        new_id._check_auto_sla_policies()

        # If the customer has a dedicated support user then automatically assign them
        if new_id.partner_id.dedicated_support_user_id:
            new_id.user_id = new_id.partner_id.dedicated_support_user_id.id

    #    # Check if this contact has a SLA assigned
    #    if new_id.partner_id.sla_id:
    #
    #        # Go through all rules starting from the lowest response time
    #        for sla_rule in new_id.partner_id.sla_id.rule_ids:
    #            # All conditions have to match
    #            all_true = True
    #            for sla_rule_con in sla_rule.condition_ids:
    #                if sla_rule_con.type == "category" and new_id.category.id != sla_rule_con.category_id.id:
    #                    all_true = False
    #                elif sla_rule_con.type == "subcategory" and new_id.sub_category_id.id != sla_rule_con.subcategory_id.id:
    #                    all_true = False
    #                elif sla_rule_con.type == "priority" and new_id.priority_id.id != sla_rule_con.priority_id.id:
    #                    all_true = False
    #
    #            if all_true:
    #                new_id.sla_id = new_id.partner_id.sla_id.id
    #                new_id.sla_active = True
    #                new_id.sla_timer = sla_rule.response_time
    #                new_id.sla_rule_id = sla_rule.id
    #                break

            # (DEPRICATED) Check if this category has a SLA response time
    #        category_response = self.env['website.supportzayd.sla.response'].search(
    #            [('vsa_id', '=', new_id.partner_id.sla_id.id), ('category_id', '=', new_id.category.id)])
    #        if category_response:
    #            new_id.sla_id = new_id.partner_id.sla_id.id
    #            new_id.sla_active = True
    #            new_id.sla_timer = category_response.response_time
    #            new_id.sla_response_category_id = category_response.id

        # Send an email out to everyone in the category
        notification_template = self.env['ir.model.data'].sudo().get_object('website_supportzayd',
                                                                            'new_support_ticket_category')
        support_ticket_menu = self.env['ir.model.data'].sudo().get_object('website_supportzayd',
                                                                          'website_supportzayd_ticket_menu')
        support_ticket_action = self.env['ir.model.data'].sudo().get_object('website_supportzayd',
                                                                            'website_supportzayd_ticket_action')

        # Add them as a follower to the ticket so they are aware of any internal notes
        new_id.message_subscribe_users(user_ids=new_id.category.cat_user_ids.ids)

        for my_user in new_id.category.cat_user_ids:
            values = notification_template.generate_email(new_id.id)
            values['body_html'] = values['body_html'].replace("_ticket_url_", "web#id=" + str(
                new_id.id) + "&view_type=form&model=website.supportzayd.ticket&menu_id=" + str(
                support_ticket_menu.id) + "&action=" + str(support_ticket_action.id)).replace("_user_name_",
                                                                                              my_user.partner_id.name)
            values['email_to'] = my_user.partner_id.email

            send_mail = self.env['mail.mail'].create(values)
            send_mail.send()

            # Remove the message from the chatter since this would bloat the communication history by a lot
            send_mail.mail_message_id.res_id = 0

        return new_id

    @api.model
    def _sla_reset_trigger(self):
        """ Get the list of field for which we have to reset the SLAs (regenerate) """
        return ['priority_star', 'category', 'sub_category_id', 'partner_id']

    @api.multi
    def write(self, values, context=None):

        update_rec = super(WebsiteSupportTicket, self).write(values)

        # SLA business
        # Update sla status as long as it is state is not 'staff_closed', or 'customer_closed'

        sla_triggers = self._sla_reset_trigger()

        if any(field_name in sla_triggers for field_name in values.keys()):
            # filter tickets according to state

            if self.state.name not in ['Staff Closed','Customer Closed']:
                self._check_auto_sla_policies()

        if 'state' in values:

            if self.state.mail_template_id:
                self.state.mail_template_id.send_mail(self.id, True)

            if self.state.name in ['Staff Closed', 'Customer Closed']: #call the def closed_ticket function from model website.supportzayd.ticket.close
                self.close_time = datetime.datetime.now()

                # Also set the date for gamification
                self.close_date = datetime.date.today()
                diff_time = datetime.datetime.strptime(self.close_time,
                                                       DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(self.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
                diff_time_days = diff_time.days
                diff_time_seconds = diff_time.seconds
                #diff_time_minutes = (diff_time_seconds % 3600) // 60
                #diff_time_hours = diff_time_days * 24 + diff_time_seconds / 3600
                diff_time_hours = diff_time_seconds / 3600 + (diff_time_days*24)

                self.time_to_close_hhmm = (float(str(diff_time_hours)))
                self.time_to_close = diff_time.seconds
                self.sla_active = False
                #in case its closed, set some fields to certain values such as in def close_ticket function, but if possible, advice helpdesk to AVOID at ALL cost closing tickets through selection of state, as it does not sends enough information (eg:cm form, date of completion)

        if 'category' in values:
            change_category_email = self.env['ir.model.data'].sudo().get_object('website_supportzayd',
                                                                                'new_support_ticket_category_change')
            change_category_email.send_mail(self.id, True)

        if 'user_id' in values:
            setting_change_user_email_template_id = self.env['ir.default'].get('website.supportzayd.settings',
                                                                               'change_user_email_template_id')

            if setting_change_user_email_template_id:
                email_template = self.env['mail.template'].browse(setting_change_user_email_template_id)
            else:
                # Default email template
                email_template = self.env['ir.model.data'].get_object('website_supportzayd', 'support_ticket_user_change')

            email_values = email_template.generate_email([self.id])[self.id]
            email_values['model'] = "website.supportzayd.ticket"
            email_values['res_id'] = self.id
            assigned_user = self.env['res.users'].browse(int(values['user_id']))
            email_values['email_to'] = assigned_user.partner_id.email
            email_values['body_html'] = email_values['body_html'].replace("_user_name_", assigned_user.name)
            email_values['body'] = email_values['body'].replace("_user_name_", assigned_user.name)
            email_values['reply_to'] = email_values['reply_to']
            send_mail = self.env['mail.mail'].create(email_values)
            send_mail.send()

        return update_rec

    def send_survey(self):
        notification_template = self.env['ir.model.data'].sudo().get_object('website_supportzayd', 'support_ticket_survey')
        values = notification_template.generate_email(self.id)
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send(True)

    # by Cooby tec
    @api.multi
    def toggle_reopen_ticket(self):
        self.close_time = False

    #Also reset the date for gamification
        self.close_date = False
        open_state = self.env['ir.model.data'].get_object('website_supportzayd', 'website_ticket_state_open')
        self.state = open_state.id


    #i dont know what is the function of toggle_shift_prio as it is develoepd by previous dev. it seems that there seems to be a function about priority here.
    #@api.multi
    #def toggle_shift_priority(self):
    #    priority_obj = self.env['website.supportzayd.ticket.priority']
    #    for ticket in self:
    #        if ticket.priority_id and ticket.priority_id.sequence:
    #            next_priority = priority_obj.search([('sequence', '>', ticket.priority_id.sequence)], order='sequence',
    #                                                limit=1)
    #            if next_priority:  # if there's next priority, assign it that one
    #                ticket.priority_id = next_priority.id
    #            else:
    #                first_priority = priority_obj.search([], order='sequence', limit=1)
    #                if first_priority:  # if there isn't, assign the lowest priority (since the button is a toggle)
    #                    ticket.priority_id = first_priority.id

    @api.multi
    def action_assign_me(self):
        # Assign current user
        self.user_id = self._uid

    #function below is to filter data according to groups @hafizalwi16dec
    #@api.depends('compute_field')
    @api.one
    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('website_supportzayd.support_technician'): #and not res_user.has_group('sale.group_sale_salesman_all_leads'):
            self.compute_field = True
        else:
            self.compute_field = False

class WebsiteSupportTicketEquipment(models.Model): #The purpose of creating this is to create dropdown suggestion when inserting data for  Equipment name
    _name = "website.supportzayd.ticket.equipment"

    name = fields.Char(String="Name", placeholder="Eg: Acer Aspire 2470" ) #this is to store model char ?? @hafizalwi1dec2021

class WebsiteSupportTicketApproval(models.Model):
    _name = "website.supportzayd.ticket.approval"

    wst_id = fields.Many2one('website.supportzayd.ticket', string="Support Ticket")
    name = fields.Char(string="Name", translate=True)


class WebsiteSupportTicketMerge(models.TransientModel):
    _name = "website.supportzayd.ticket.merge"

    ticket_id = fields.Many2one('website.supportzayd.ticket', ondelete="cascade", string="Support Ticket")
    merge_ticket_id = fields.Many2one('website.supportzayd.ticket', ondelete="cascade", required="True",
                                      string="Merge With")

    @api.multi
    def merge_tickets(self):

        self.ticket_id.close_time = datetime.datetime.now()

        # Also set the date for gamification
        self.ticket_id.close_date = datetime.date.today()

        diff_time = datetime.datetime.strptime(self.ticket_id.close_time,
                                               DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(
            self.ticket_id.create_date, DEFAULT_SERVER_DATETIME_FORMAT)

        self.ticket_id.time_to_close = diff_time.seconds

        closed_state = self.env['ir.model.data'].sudo().get_object('website_supportzayd','website_ticket_state_staff_closed')
        self.ticket_id.state = closed_state.id

        # Lock the ticket to prevent reopening
        self.ticket_id.ticket= True

        # Send merge email
        setting_ticket_merge_email_template_id = self.env['ir.default'].get('website.supportzayd.settings',
                                                                            'ticket_merge_email_template_id')
        if setting_ticket_merge_email_template_id:
            mail_template = self.env['mail.template'].browse(setting_ticket_merge_email_template_id)
        else:
            # BACK COMPATABLITY FAIL SAFE
            mail_template = self.env['ir.model'].get_object('website_supportzayd', 'support_ticket_merge')

        mail_template.send_mail(self.id, True)

        # Add as follower to new ticket
        if self.ticket_id.partner_id:
            self.merge_ticket_id.message_subscribe([self.ticket_id.partner_id.id])

        return {
            'name': "Support Ticket",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.supportzayd.ticket',
            'res_id': self.merge_ticket_id.id
        }


class WebsiteSupportTicketField(models.Model):
    _name = "website.supportzayd.ticket.field"

    wst_id = fields.Many2one('website.supportzayd.ticket', string="Support Ticket")
    name = fields.Char(string="Label")
    value = fields.Char(string="Value")


class WebsiteSupportTicketMessage(models.Model):
    _name = "website.supportzayd.ticket.message"

    ticket_id = fields.Many2one('website.supportzayd.ticket', string='Ticket ID')
    by = fields.Selection([('staff', 'Staff'), ('customer', 'Customer')], string="By")
    content = fields.Html(string="Content")


class WebsiteSupportTicketCategories(models.Model):
    _name = "website.supportzayd.ticket.categories"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, translate=True, string='Category Name')
    cat_user_ids = fields.Many2many('res.users', string="Category Users", help="Restrict which uesrs can view and get email for this category")
    access_group_ids = fields.Many2many('res.groups', string="Access Groups", help="Please do not fill anything here if you not an advanced user!!!\nRestrict which users can select the category on the website application form, none = everyone")
    #commented out to solve creating user by admin issues@hafizalwi2Dec
    @api.multi
    @api.constrains('name')
    def _check_duplicate(self):
        for record in self:
            category_tags = self.env['website.supportzayd.ticket.categories'].search_read(
                    [('name', 'in', [record.name])])
            if len(category_tags) > 1:
                raise ValidationError(_("You can't create 2 category with the same name!\n Please try creating with a different category name."))

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('website.supportzayd.ticket.categories')
        values['sequence'] = sequence
        return super(WebsiteSupportTicketCategories, self).create(values)


class WebsiteSupportTicketSubCategories(models.Model):
    _name = "website.supportzayd.ticket.subcategory"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, translate=True, string='Sub Category Name')
    parent_category_id = fields.Many2one('website.supportzayd.ticket.categories',required=True,  string="Category") #default=lambda self: self.env['website.supportzayd.ticket'].search(['category.id','=',self.sub_category_id.id]).category.id) #default=lambda self: self.env['website.supportzayd.ticket'].search(['category.id','=',self.category.id]).category.id)


    @api.multi
    @api.constrains('name', 'parent_category_id',)
    def _check_duplicate(self):
        for record in self:
            subcategory_tags = self.env['website.supportzayd.ticket.subcategory'].search_read(
                    [('name', 'in', [record.name]), ('parent_category_id', '=', record.parent_category_id.id)])
            if len(subcategory_tags) > 1:
                raise ValidationError(_("You can't create 2 subcategory with the same name for each category!\n Please try creating with a different subcategory name or a different category name."))

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('website.supportzayd.ticket.subcategory')
        values['sequence'] = sequence
        return super(WebsiteSupportTicketSubCategories, self).create(values)


#class WebsiteSupportTicketSubCategoryField(models.Model):
#    _name = "website.supportzayd.ticket.subcategory.field"
#
#    wsts_id = fields.Many2one('website.supportzayd.ticket.subcategory', string="Sub Category")
#    name = fields.Char(string="Label", required="True")
#    type = fields.Selection([('textbox', 'Textbox'), ('many2one', 'Dropdown(m2o)')], default="textbox", required="True",
#                            string="Type")
#    model_id = fields.Many2one('ir.model', string="Model")
#    model_name = fields.Char(related="model_id.model", string="Model Name")
#    filter = fields.Char(string="Filter", default="[]", required="True")


class WebsiteSupportTicketProblem(models.Model):
    _name = "problem_many2many_tags"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, string="Problem Name")
    parent_subcategory_id = fields.Many2one('website.supportzayd.ticket.subcategory', required=True, string="Sub Category", context="{'default_abc_vendor_id': id}")

    @api.multi
    @api.constrains('name', 'parent_subcategory_id',)
    def _check_duplicate(self):
        for record in self:
            problem_tags = self.env['problem_many2many_tags'].search_read(
                    [('name', 'in', [record.name]), ('parent_subcategory_id', '=', record.parent_subcategory_id.id)])
            if len(problem_tags) > 1:
                raise ValidationError(_("You can't create 2 problem tags with the same problem_name and subcategory!\n Please try creating with a different subcategory or a different problem name."))

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('problem_many2many_tags')
        values['sequence'] = sequence
        return super(WebsiteSupportTicketProblem, self).create(values)


class WebsiteSupportTicketItemHistory(models.Model):
    _name = "website.supportzayd.ticket.item.history"
    location_id = fields.Many2one('website.supportzayd.ticket.item.location', translate=True, string="Current Location")
    date = fields.Date(string='Date',default=fields.Datetime.now)
    item_id = fields.Many2one('website.supportzayd.ticket.item')

class WebsiteSupportTicketItemLocation(models.Model):
    _name = "website.supportzayd.ticket.item.location"
    name = fields.Char(translate=True, string="Current Location")

class WebsiteSupportTicketItemType(models.Model):
    _name = "website.supportzayd.ticket.item.type"
    name = fields.Char(translate=True, string="Type of Equipment")

# class for item
class WebsiteSupportTicketItem(models.Model):
    _name = "website.supportzayd.ticket.item"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    EquipmentName = fields.Many2one('website.supportzayd.ticket.equipment', required=True, string="Models name")
    equipment_type = fields.Many2one('website.supportzayd.ticket.item.type', string="Type of Equipment", help="eg: Personal Computer, Printer")
    startingdate = fields.Date(string='Warranty Start date')
    deadlinegar = fields.Date(string='Warranty End date')
    warranty_func = fields.Boolean(string='Under warranty', compute='_days_warranty_')
    customer = fields.Many2one('res.partner', required=True, string='Customer') # changed String from 'Company location' to 'Customer' 13dec
    user = fields.Char(string='Equipment User')# changed String from 'Company location' to 'Customer' 13dec

    location_id = fields.Many2one('website.supportzayd.ticket.item.location',string="Current Location", placeholder="Bahagian Perolehan")
    location_history = fields.One2many('website.supportzayd.ticket.item.history','item_id',string="Location History")
    note = fields.Text(string='Description')
    safety = fields.Text(string='Safety')
    partner_id = fields.Many2one('res.partner', string="Vendor", help="Vendor are sometimes referenced to as suppliers")
    partner_reference = fields.Many2many('website.supportzayd.tags', string="Tender Reference", help="Tender's unique initial code, eg:'DAAS1'" , placeholder="Eg:DAAS1")
    serial_no = fields.Char(string='Serial Number', required=True)
    trademark = fields.Char(string='Brand')
    color_kanban = fields.Integer(string="Color") #color for usage of kanban view @hafizalwi

    @api.one
    def _days_warranty_(self):
        for record in self:
            if record.deadlinegar:
                fmt = '%Y-%m-%d'
                d1 = date.today().strftime('%Y-%m-%d')
                d2 = datetime.datetime.strptime(record.deadlinegar, fmt)
                if d1 < d2.isoformat():
                    record.warranty_func = True
                else:
                    record.warranty_func = False
            else:
                record.warranty_func = False
        return record.warranty_func

    #@api.onchange('item')
    def name_get(self):
        item_list = []

        for item in self:
            #name = item.EquipmentName #here we initialize value of equipmentName into name?
            name = item.EquipmentName.name
            if item.serial_no:
                name = name + " (S/N:{}) ".format(item.serial_no)
                item_list.append((item.id, name))
        return item_list

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('id', operator, name), ('serial_no', operator, name)]
        return super(WebsiteSupportTicketItem, self).search(domain, limit=limit).name_get()


    @api.multi
    def write(self, values):
        update_rec = super(WebsiteSupportTicketItem, self).write(values)

        print("selfid",self.id)

        if 'location_id' in values:
            location_id = values.get('location_id')
            date=datetime.datetime.now()
            self.write({"location_history": [[0,0,{'location_id':location_id, 'date':date,'item_id':self.id}]]}) #notice that in def create for this model i dont do this[0,0,vals], this brings the equivalent meaning like normal logic but this is a special command syntax for odoo

        return update_rec
    #    if values.get('location_id'):
    #            lines_dict  # here get the lines that you want in a dict formatted for creating record in model b lines
    #    self.env['website.supportzayd.ticket.item.history'].create(lines_dict)  # here you pass the dict with vals that you want
    #    return super(WebsiteSupportTicketItem, self).write(valuess)
    @api.model
    def create(self, vals):
        res = super(WebsiteSupportTicketItem, self).create(vals)

        if vals.get('location_id'):
            location_id = vals.get('location_id')
            date = datetime.datetime.now()

            item_obj = self.env['website.supportzayd.ticket.item.history']
            item_obj.create({'date': date, 'location_id': location_id, 'item_id': res['id']})

        return res


class WebsiteSupportTicketStates(models.Model):
    _name = "website.supportzayd.ticket.states"

    name = fields.Char(required=True, translate=True, string='Status Name')
    mail_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.supportzayd.ticket')]",
                                       string="Mail Template",
                                       help="The mail message that the customer gets when the state changes")
    unattended = fields.Boolean(string="Unattended", help="If ticked, tickets in this state will appear by default")

#hafizalwi, might need to remove this function below to clean the code, as we are going to use 'priority_star' to replace 'priorioty'


class WebsiteSupportTicketUsers(models.Model):
    _inherit = "res.users"

    cat_user_ids = fields.Many2many('website.supportzayd.ticket.categories', string="Category Users")

class WebsiteSupportTicketLevel(models.Model):
    _name ="website.supportzayd.ticket.level"

    name = fields.Char(String="Support Level") #this is to store model char ?? @hafizalwi1dec2021

class WebsiteSupportTicketClose(models.TransientModel):
    _name = "website.supportzayd.ticket.close"

    ticket_id = fields.Many2one('website.supportzayd.ticket', string="Ticket ID")
    message = fields.Text(string="Close Message")
    cm_form = fields.Char(string="CM Form")
    case_done = fields.Datetime(string="Date of completion")
    template_id = fields.Many2one('mail.template', string="Mail Template",
                                  domain="[('model_id','=','website.supportzayd.ticket'), ('built_in','=',False)]")
    support_level_id = fields.Many2one('website.supportzayd.ticket.level', string="Support Level") #hafiz 18 feb 2022
    attachment_ids = fields.Many2many('ir.attachment', 'sms_close_attachment_rel', 'sms_close_id', 'attachment_id',
                                      'Attachments')


    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            values = \
                self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, [self.ticket_id.id])[
                    self.ticket_id.id]
            self.message = values['body']

    def close_ticket(self): #@hafiz15dec

        self.ticket_id.close_time = datetime.datetime.now()

        # Also set the date for gamification
        self.ticket_id.close_date = datetime.date.today()

        diff_time = datetime.datetime.strptime(self.ticket_id.close_time,
                                               DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(
            self.ticket_id.create_date, DEFAULT_SERVER_DATETIME_FORMAT)

        diff_time_days = diff_time.days
        diff_time_seconds = diff_time.seconds
        #diff_time_minutes = (diff_time_seconds % 3600) // 60
        #diff_time_hours = diff_time_days * 24 + diff_time_seconds / 3600
        diff_time_hours = diff_time_seconds / 3600 + (diff_time_days *24)


        self.ticket_id.time_to_close_hhmm = (float(str(diff_time_hours)))

        self.ticket_id.time_to_close = diff_time.seconds

        closed_state = self.env['ir.model.data'].sudo().get_object('website_supportzayd','website_ticket_state_staff_closed')

        # We record state change manually since it would spam the chatter if every 'Staff Replied' and 'Customer Replied' gets recorded
        message = "<ul class=\"o_mail_thread_message_tracking\">\n<li>State:<span> " + self.ticket_id.state.name + " </span><b>-></b> " + closed_state.name + " </span></li></ul>"
        self.ticket_id.message_post(body=message, subject="Ticket Closed by Staff")

        email_wrapper = self.env['ir.model.data'].sudo().get_object('website_supportzayd', 'support_ticket_close_wrapper')# @hafizalwi17dec tested to put 'sudo()' so that data can be imported in mail template without having to give read permission to for certain fields such as 'problem' to group 'Technician', which is not good for security

        values = email_wrapper.generate_email([self.id])[self.id]
        values['model'] = "website.supportzayd.ticket"
        values['res_id'] = self.ticket_id.id

        for attachment in self.attachment_ids:
            values['attachment_ids'].append((4, attachment.id))

        send_mail = self.env['mail.mail'].create(values)
        send_mail.send()

        cleanbreak = re.compile('<br\s*?>')
        cleanedbreak = re.sub(cleanbreak, '\n', self.message)
        cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

        self.ticket_id.close_comment = re.sub(cleanr, '', cleanedbreak)
        self.ticket_id.cmform = self.cm_form
        self.ticket_id.prob_solve_time = self.case_done
        self.ticket_id.closed_by_id = self.env.user.id
        self.ticket_id.state = closed_state.id

        self.ticket_id.sla_active = False

        # Auto send out survey
        setting_auto_send_survey = self.env['ir.default'].get('website.supportzayd.settings', 'auto_send_survey')
        if setting_auto_send_survey:
            self.ticket_id.send_survey()


class WebsiteSupportTicketCompose(models.Model):
    _name = "website.supportzayd.ticket.compose"

    ticket_id = fields.Many2one('website.supportzayd.ticket', string='Ticket ID')
    partner_id = fields.Many2one('res.partner', string="Partner", readonly="True")
    email = fields.Char(string="Email", readonly="True")
    email_cc = fields.Char(string="Cc")
    subject = fields.Char(string="Subject", readonly="True")
    body = fields.Text(string="Message Body")
    template_id = fields.Many2one('mail.template', string="Mail Template",
                                  domain="[('model_id','=','website.supportzayd.ticket'), ('built_in','=',False)]")
    approval = fields.Boolean(string="Approval")
    planned_time = fields.Datetime(string="Planned Time")
    attachment_ids = fields.Many2many('ir.attachment', 'sms_compose_attachment_rel', 'sms_compose_id', 'attachment_id',
                                      'Attachments')

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            values = \
                self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, [self.ticket_id.id])[
                    self.ticket_id.id]
            self.body = values['body']

    @api.one
    def send_reply(self):

        # Change the approval state before we send the mail
        if self.approval:
            # Change the ticket state to awaiting approval
            awaiting_approval_state = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                           'website_ticket_state_awaiting_approval')
            self.ticket_id.state = awaiting_approval_state.id

            # One support request per ticket...
            self.ticket_id.planned_time = self.planned_time
            self.ticket_id.approval_message = self.body
            self.ticket_id.sla_active = False

        # Send email
        values = {}

        setting_staff_reply_email_template_id = self.env['ir.default'].get('website.supportzayd.settings',
                                                                           'staff_reply_email_template_id')

        if setting_staff_reply_email_template_id:
            email_wrapper = self.env['mail.template'].browse(setting_staff_reply_email_template_id)

        values = email_wrapper.generate_email([self.id])[self.id]
        values['model'] = "website.supportzayd.ticket"
        values['res_id'] = self.ticket_id.id
        values['reply_to'] = email_wrapper.reply_to

        if self.email_cc:
            values['email_cc'] = self.email_cc

        for attachment in self.attachment_ids:
            values['attachment_ids'].append((4, attachment.id))

        send_mail = self.env['mail.mail'].create(values)
        send_mail.send()

        # Add to the message history to keep the data clean from the rest HTML
        self.env['website.supportzayd.ticket.message'].create({'ticket_id': self.ticket_id.id, 'by': 'staff',
                                                           'content': self.body.replace("<p>", "").replace("</p>", "")})

        # Post in message history
        # self.ticket_id.message_post(body=self.body, subject=self.subject, message_type='comment', subtype='mt_comment')

        if self.approval:
            # Also change the approval
            awaiting_approval = self.env['ir.model.data'].get_object('website_supportzayd', 'awaiting_approval')
            self.ticket_id.approval_id = awaiting_approval.id
        else:
            # Change the ticket state to staff replied
            staff_replied = self.env['ir.model.data'].get_object('website_supportzayd',
                                                                 'website_ticket_state_staff_replied')
            self.ticket_id.state = staff_replied.id



class WebsiteSupportTags(models.Model):
    _name = "website.supportzayd.tags"

    def _get_default_color(self):
        return randint(1, 11)


    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string="Color", default=_get_default_color, widget="many2many_tags")

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'name already exist!')
    ]




