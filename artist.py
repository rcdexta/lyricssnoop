class Artist:
    def __init__(self,id,name):
        self.id = id
        self.name = name
        
    def alias(self):
        return self.name.lower().replace(' ', '_').replace('\n','')