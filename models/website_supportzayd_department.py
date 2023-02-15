# -*- coding: utf-8 -*-
import datetime

from openerp import api, fields, models

class WebsiteSupportDepartment(models.Model):

    _name = "website.supportzayd.department"

    name = fields.Char(string="Name", translate=True)
    manager_ids = fields.One2many('website.supportzayd.department.contact', 'wsd_id', string="Managers")
    partner_ids = fields.Many2many('res.partner', string="Contacts")
    sub_category_ids = fields.One2many('website.supportzayd.department.subcategory', 'wsd_id', string="Sub Categories", compute='_compute_sub_category_ids')
    sub_category_month_ids = fields.One2many('website.supportzayd.department.subcategory', 'wsd_month_id', string="Sub Categories Month", compute='_compute_sub_category_month_ids')
    sub_category_week_ids = fields.One2many('website.supportzayd.department.subcategory', 'wsd_week_id', string="Sub Categories Week", compute='_compute_sub_category_week_ids')
    submit_ticket_contact_ids = fields.One2many('website.supportzayd.department.submit', 'wsd_id', string="Contact Submitted Tickets", compute='_compute_submit_ticket_contact_ids')
    submit_ticket_contact_month_ids = fields.One2many('website.supportzayd.department.submit', 'wsd_month_id', string="Contact Submitted Tickets Month", compute='_compute_submit_ticket_contact_month_ids')
    submit_ticket_contact_week_ids = fields.One2many('website.supportzayd.department.submit', 'wsd_week_id', string="Contact Submitted Tickets Week", compute='_compute_submit_ticket_contact_week_ids')

    #-------------- Sub Category Stats --------------------------

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_sub_category_ids(self):

        #Unlink all existing records
        for si in self.env['website.supportzayd.department.subcategory'].search([('wsd_id', '=', self.id)]):
            si.unlink()

        extra_access = []
        for extra_permission in self.partner_ids:
            extra_access.append(extra_permission.id)

        for sub_category in self.env['website.supportzayd.ticket.subcategory'].search([]):
            count = self.env['website.supportzayd.ticket'].search_count(['|', ('partner_id','=', self.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False), ('sub_category_id','=', sub_category.id)])
            if count > 0:
                self.env['website.supportzayd.department.subcategory'].create( {'wsd_id': self.id, 'subcategory_id': sub_category.id, 'count': count} )

        self.sub_category_ids = self.env['website.supportzayd.department.subcategory'].search([('wsd_id', '=', self.id)], limit=5)

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_sub_category_month_ids(self):

        #Unlink all existing records
        for si in self.env['website.supportzayd.department.subcategory'].search([('wsd_month_id', '=', self.id)]):
            si.unlink()

        extra_access = []
        for extra_permission in self.partner_ids:
            extra_access.append(extra_permission.id)

        for sub_category in self.env['website.supportzayd.ticket.subcategory'].search([]):
            month_ago = (datetime.datetime.now() - datetime.timedelta(days=30) ).strftime("%Y-%m-%d %H:%M:%S")
            count = self.env['website.supportzayd.ticket'].search_count(['|', ('partner_id','=', self.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False), ('sub_category_id','=', sub_category.id), ('create_date','>', month_ago ) ])
            if count > 0:
                self.env['website.supportzayd.department.subcategory'].create( {'wsd_month_id': self.id, 'subcategory_id': sub_category.id, 'count': count} )

        self.sub_category_month_ids = self.env['website.supportzayd.department.subcategory'].search([('wsd_month_id', '=', self.id)], limit=5)

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_sub_category_week_ids(self):

        #Unlink all existing records
        for si in self.env['website.supportzayd.department.subcategory'].search([('wsd_week_id', '=', self.id)]):
            si.unlink()

        extra_access = []
        for extra_permission in self.partner_ids:
            extra_access.append(extra_permission.id)

        for sub_category in self.env['website.supportzayd.ticket.subcategory'].search([]):
            week_ago = (datetime.datetime.now() - datetime.timedelta(days=7) ).strftime("%Y-%m-%d %H:%M:%S")
            count = self.env['website.supportzayd.ticket'].search_count(['|', ('partner_id','=', self.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False), ('sub_category_id','=', sub_category.id), ('create_date','>', week_ago ) ])
            if count > 0:
                self.env['website.supportzayd.department.subcategory'].create( {'wsd_week_id': self.id, 'subcategory_id': sub_category.id, 'count': count} )

        self.sub_category_week_ids = self.env['website.supportzayd.department.subcategory'].search([('wsd_week_id', '=', self.id)], limit=5)

    #-------------- Ticket Submit Stats --------------------------

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_submit_ticket_contact_ids(self):

        #Unlink all existing records
        for si in self.env['website.supportzayd.department.submit'].search([('wsd_id', '=', self.id)]):
            si.unlink()

        for contact in self.partner_ids:
            count = self.env['website.supportzayd.ticket'].search_count([('partner_id','=', contact.id)])
            if count > 0:
                self.env['website.supportzayd.department.submit'].create( {'wsd_id': self.id, 'partner_id': contact.id, 'count': count} )

        self.submit_ticket_contact_ids = self.env['website.supportzayd.department.submit'].search([('wsd_id', '=', self.id)], limit=5)

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_submit_ticket_contact_month_ids(self):

        #Unlink all existing records
        for si in self.env['website.supportzayd.department.submit'].search([('wsd_month_id', '=', self.id)]):
            si.unlink()

        for contact in self.partner_ids:

            month_ago = (datetime.datetime.now() - datetime.timedelta(days=30) ).strftime("%Y-%m-%d %H:%M:%S")
            count = self.env['website.supportzayd.ticket'].search_count([('partner_id','=', contact.id), ('create_date','>', month_ago ) ])
            if count > 0:
                self.env['website.supportzayd.department.submit'].create( {'wsd_month_id': self.id, 'partner_id': contact.id, 'count': count} )

        self.submit_ticket_contact_month_ids = self.env['website.supportzayd.department.submit'].search([('wsd_month_id', '=', self.id)], limit=5)

    @api.one
    @api.depends('manager_ids', 'partner_ids')
    def _compute_submit_ticket_contact_week_ids(self):

        #Unlink all existing records
        for si in self.env['website.supportzayd.department.submit'].search([('wsd_week_id', '=', self.id)]):
            si.unlink()

        for contact in self.partner_ids:
            week_ago = (datetime.datetime.now() - datetime.timedelta(days=7) ).strftime("%Y-%m-%d %H:%M:%S")
            count = self.env['website.supportzayd.ticket'].search_count([('partner_id','=', contact.id), ('create_date','>', week_ago )])
            if count > 0:
                self.env['website.supportzayd.department.submit'].create( {'wsd_week_id': self.id, 'partner_id': contact.id, 'count': count} )

        self.submit_ticket_contact_week_ids = self.env['website.supportzayd.department.submit'].search([('wsd_week_id', '=', self.id)], limit=5)

class WebsiteSupportDepartmentContact(models.Model):

    _name = "website.supportzayd.department.contact"

    def _default_role(self):
        return self.env['ir.model.data'].get_object('website_supportzayd','website_supportzayd_department_manager')

    wsd_id = fields.Many2one('website.supportzayd.department', string="Department")
    role = fields.Many2one('website.supportzayd.department.role', string="Role", required="True", default=_default_role)
    user_id = fields.Many2one('res.users', string="User", required="True")

class WebsiteSupportDepartmentRole(models.Model):

    _name = "website.supportzayd.department.role"

    name = fields.Char(string="Name", translate=True)
    view_department_tickets = fields.Boolean(string="View Department Tickets")

class WebsiteSupportDepartmentSubcategory(models.Model):

    _name = "website.supportzayd.department.subcategory"
    _order = "count desc"

    wsd_id = fields.Many2one('website.supportzayd.department', string="Department")
    wsd_month_id = fields.Many2one('website.supportzayd.department', string="Department")
    wsd_week_id = fields.Many2one('website.supportzayd.department', string="Department")
    subcategory_id = fields.Many2one('website.supportzayd.ticket.subcategory', string="Sub Category")
    count = fields.Integer(string="Count")

class WebsiteSupportDepartmentSubmit(models.Model):

    _name = "website.supportzayd.department.submit"
    _order = "count desc"

    wsd_id = fields.Many2one('website.supportzayd.department', string="Department")
    wsd_month_id = fields.Many2one('website.supportzayd.department', string="Department")
    wsd_week_id = fields.Many2one('website.supportzayd.department', string="Department")
    partner_id = fields.Many2one('res.partner', string="Contact")
    count = fields.Integer(string="Count")
