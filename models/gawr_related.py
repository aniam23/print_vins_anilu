from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    gawr_related = fields.Many2one('print.gawr', string='GAWR')
    dry_weight = fields.Integer(
        string="DRY WEIGHT",
        help="Peso del remolque sin carga (en kg o lbs)",
        # digits=(10, 2) 
    )
    tire_typ = fields.Selection(
        selection=[
            ("SINGLE","SINGLE"),
            ("SUPER SINGLE","SUPER SINGLE"),
            ("DUAL","DUAL")
        ],
        string="Tire Type",
        default="SINGLE"
    )
    @api.model
    def year_selection(self):
        """
        Generates a selection list of years from 2021 to 2039.
        :return: List of tuples in the format [('2021', '2021'), ...] for Selection fields
        """
        year = 2021
        #lista para almacenar los años
        year_list = []
        while year != 2040:
            year_list.append((str(year), str(year)))  
            year += 1
        return year_list

class ProductProduct(models.Model):
    _inherit = 'product.product'
    gawr_child = fields.Many2one('print.gawr', string='GAWR Child')
    @api.model_create_multi
    def create(self, vals_list):
        """
        Extension of the product.product model to add:
        GAWR field specific to variants
    """
        products = super(ProductProduct, self).create(vals_list)
        for product in products:
            product.gawr_child = product.product_tmpl_id.gawr_related
        return products