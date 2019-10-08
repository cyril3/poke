import json
import os

class Feeds:
    def __init__(self, file_path):
        self.doc = None
        self.file_path = file_path

    def load(self):
        if not os.path.exists(self.file_path):
            self.doc = {'feeds':[]}
            return
        with open(self.file_path, 'r') as f:
            self.doc = json.load(f)

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.doc, f)

    def get_feeds(self):
        return self.doc['feeds']

    def set_feeds(self, c):
        self.doc['feeds'] = c