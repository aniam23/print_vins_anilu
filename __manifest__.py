# -*- coding: utf-8 -*-
{
    'name': "Print vin labels",

    'summary': """
        Print Vin Labels""", 

    'description': """
        Print Labels  Vin Of Trailers
    """,

    'author': "Anilu Amado Aguero",
    'website': "http://www.horizontrailers.com",
    'sequence': 3,
    'category': 'All',

    'version': '1.0',

    'depends': ['base','sale','vin_generator'],

    'external_dependencies': {
        'python': ['zebra_day'], },

    'data': [
        'security/ir.model.access.csv',
        'views/gawr_view.xml',
        'views/manual_print_view.xml',
        'views/gawr_related_view.xml',
        'views/print_vin_view.xml',
        'views/printer_conf_view.xml',
    ],
    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    
}