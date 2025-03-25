import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv

class RGCNModel(nn.Module):
    def __init__(self, input_dim, hid_dim , output_dim, num_relations):
        super(RGCNModel, self).__init__()
        self.conv1 = RGCNConv(input_dim, hid_dim, num_relations)
        self.conv2 = RGCNConv(hid_dim, output_dim, num_relations)

    def forward(self, x, edge_index, edge_type):
        x = self.conv1(x, edge_index, edge_type)
        x = F.relu(x)
        x = self.conv2(x, edge_index, edge_type)
        return x