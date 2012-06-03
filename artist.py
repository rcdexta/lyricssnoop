class Artist:
    def __init__(self,id,name):
        self.id = id
        self.name = name
        self.image_url = None
        self.bio = None
        self.tags = []
        
    def alias(self):
        return self.name.lower().replace(' ', '_').replace('\n','')