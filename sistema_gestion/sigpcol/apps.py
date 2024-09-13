from django.apps import AppConfig
#from .run_task import update_exchange_rate_task



class SigpcolConfig(AppConfig):    
    name = 'sigpcol'

    def ready(self):
        
       # update_exchange_rate_task(repeat=60)
       pass