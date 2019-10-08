import os
import json
import inspect

class Config:
    config_path = os.path.join(os.path.expanduser('~'), '.poke')
    def __init__(self):
        self.feed_path = os.path.join(os.path.expanduser('~'), 'podcasts')

    
    def load(self):
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w") as f:
                json.dump(self.__dict__, f)
        else:
            with open(self.config_path, "r") as f:
                try:
                    c = json.load(f)
                except json.decoder.JSONDecodeError:
                    print("Error: \".poke\" file is an invalid json file.")
                    return -1
                for k,v in c.items():
                    self.__dict__[k] = v
        return 0


    def write(self):
        with open(self.config_path, "w") as f:
            json.dump(self.__dict__, f)