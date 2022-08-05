import torch.nn as nn
import torch.optim as optim
import torch

class FunkSVDModel(nn.Module):

	def __init__(self, user_count, film_count ,n_hidden):
		super(FunkSVDModel, self).__init__()

		self.user_matrix = nn.Parameter(torch.normal(0, 0.02, size=(user_count, n_hidden)))
		self.film_matrix = nn.Parameter(torch.normal(0, 0.02, size=(n_hidden, film_count)))
		self.user_bias = nn.Parameter(torch.zeros(size=(user_count, 1)))
		self.film_bias = nn.Parameter(torch.zeros(size=(1, film_count)))

	def get_uv(self):
		u = torch.cat([self.user_matrix, self.user_bias], dim=1)
		v = torch.cat([self.film_matrix, self.film_bias], dim=0)
		return u.detach().numpy(), v.detach().numpy()

	def final_prediction(self):
		return self.forward().detach().numpy()

	def regularize(self):
		return torch.mean(torch.sqrt((self.user_matrix ** 2).sum(dim=1))) +  torch.mean(torch.sqrt((self.film_matrix ** 2).sum(dim=0)))

	def forward(self):
		x = self.user_matrix @ self.film_matrix + self.user_bias + self.film_bias

		return x



