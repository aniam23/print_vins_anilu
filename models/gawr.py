from odoo import models, fields, api

class gawr(models.Model):
    """
    Model for managing GAWRs that are linked to products.
    """
    _name = 'print.gawr' 
    _description = 'Manages the GAWR that are linked to products'  
    name = fields.Char(compute="calculate_name")
    weight_lb = fields.Integer(string="Pounds GAWR")
    weight_kg = fields.Integer(
        string="Kilogram PNBV",
        compute="calculate_kg_from_pounds" 
    )
    products_relation = fields.One2many(
        'product.template', 
        'gawr_related'  
    )

    @api.depends("weight_lb")
    def calculate_kg_from_pounds(self):
        """
        Automatically calculates weight in kilograms from pounds.
        """
        for record in self:
            # Convierte a float  luego a entero
            record.weight_kg = int(float(record.weight_lb) / 2.205)

    @api.depends("weight_lb")
    def calculate_name(self):
        """
        Generates an automatic descriptive name in the format "GAWR"
        """
        for record in self:
            record.name = "GAWR " + str(record.weight_lb) + " lb"
