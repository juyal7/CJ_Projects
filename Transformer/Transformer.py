import math
class InputEmbeddings(nn.module)
def __init__(self,de_model,de_vocab):
    super().__init__()
    self.de_model=de_model
    self.de_vocab=de_vocab
    self.embeddings=nn.Embedding(len(de_vocab), de_model)
    
def forward(self, x):
    return self.embeddings(x)*math.sqrt(self.de_model)


