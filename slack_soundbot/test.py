# class Aap(type):
#     @classmethod
#     def __prepare__(metacls, name, bases):
#         print(dir(metacls))
#         return dict(locals())
#
#     floep = 'floep'
#
# class Banaan(metaclass=Aap):
#     def __init__(self):
#         print('init')
#
#     def talk(self):
#         print(self.floep)

#floep = 'init'

class Aap:
    def __init__(self,floeps):
        global floep
        floep = floeps

class Banaan:
    def talk(self):
        print(floep)

class Global:
    config = None # for all modules
    bot = None # for sending messages
    handlers = None # for subscribing to each other's events
    # rebinding probably not a good idea
    # Futures? deadlock danger