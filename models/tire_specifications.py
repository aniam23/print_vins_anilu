from odoo import models, fields

class TireSpecifications(models.Model):
    _name = 'tire.specifications'
    _description = 'Especificaciones técnicas de llantas'
    
    def get_ratings_map(self):
        """
        Return the complete dictionary of tire specifications
        Return:
            Organized tire specification map
        """
        return {
            '17.5': {
                'DUAL': {
                    '18PLY': ('862 KPA/125 PSI', '5675 LBS'),
                    '18PR': ('862 KPA/125 PSI', '5675 LBS'),
                    '14PLY': ('758 KPA/110 PSI', '4400 LBS'),
                    '14PR': ('758 KPA/110 PSI', '4400 LBS'),
                    '10PLY': ('550 KPA/80 PSI', '3520 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3520 LBS')
                },
                'SS': {
                    '18PLY': ('862 KPA/125 PSI', '6005 LBS'),
                    '18PR': ('862 KPA/125 PSI', '6005 LBS'),
                    '14PLY': ('758 KPA/110 PSI', '4400 LBS'),
                    '14PR': ('758 KPA/110 PSI', '4400 LBS')
                }
            },
            '16': {
                'DUAL': {
                    '14PLY': ('758 KPA/110 PSI', '3860 LBS'),
                    '14PR': ('758 KPA/110 PSI', '3860 LBS'),
                    '10PLY': ('550 KPA/80 PSI', '3080 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3080 LBS')
                },
                'SS': {
                    '14PLY': ('758 KPA/110 PSI', '3860 LBS'),
                    '14PR': ('758 KPA/110 PSI', '3860 LBS')
                },
                '': {
                    '10PLY': ('550 KPA/80 PSI', '3520 LBS'),
                    '10PR': ('550 KPA/80 PSI', '3520 LBS'),
                    '14PLY': ('758 KPA/110 PSI', '4400 LBS'),
                    '14PR': ('758 KPA/110 PSI', '4400 LBS')
                }
            },
            '15': {
                '': {
                    '10PLY': ('550 KPA/80 PSI', '2830 LBS'),
                    '10PR': ('550 KPA/80 PSI', '2830 LBS'),
                    '8PLY': ('448 KPA/65 PSI', '2150 LBS'),
                    '8PR': ('448 KPA/65 PSI', '2150 LBS'),
                    '6PLY': ('334 KPA/50 PSI', '1820 LBS'),
                    '6PR': ('334 KPA/50 PSI', '1820 LBS')
                }
            }
        }