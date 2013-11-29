__version__ = '0.0.2'
__author__ = 'Mingcai SHEN <archsh@gmail.com>'

try:
    from .application import RestletApplication
    from .handler import RestletHandler
    __all__ = ['RestletApplication', 'RestletHandler']
except:
    pass