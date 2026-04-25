import torch
import torch.nn as nn
import torch.nn.functional as F

class GraphConvolution(nn.Module):
    """Simple GCN layer"""
    def __init__(self, in_features, out_features):
        super(GraphConvolution, self).__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight)

    def forward(self, x, adj):
        # x shape: (batch, time, nodes, features)
        batch, time, nodes, features = x.shape
        x = x.view(-1, nodes, features) # (batch*time, nodes, features)
        
        # Graph convolution: A * X * W
        support = torch.matmul(x, self.weight)
        # Ensure adj is on the same device as support
        output = torch.matmul(adj.to(support.device), support)
        
        return output.view(batch, time, nodes, -1)

class STGCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3):
        super(STGCNBlock, self).__init__()
        self.gcn = GraphConvolution(in_channels, out_channels)
        self.tcn = nn.Sequential(
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Conv2d(out_channels, out_channels, (kernel_size, 1), padding=((kernel_size-1)//2, 0)),
            nn.BatchNorm2d(out_channels),
            nn.ReLU()
        )

    def forward(self, x, adj):
        # x: (batch, time, nodes, in_channels)
        x = self.gcn(x, adj)
        # Reshape for TCN (Conv2d expects: batch, channels, time, nodes)
        x = x.permute(0, 3, 1, 2).contiguous()
        x = self.tcn(x)
        # Back to (batch, time, nodes, out_channels)
        return x.permute(0, 2, 3, 1).contiguous()

class SignLanguageSTGCN(nn.Module):
    def __init__(self, num_classes, num_nodes=42, in_channels=3):
        super(SignLanguageSTGCN, self).__init__()
        
        # 1. Define Adjacency Matrix for 2 hands (21 nodes each)
        adj = self._get_adjacency_matrix()
        self.register_buffer('adj', adj)
        
        # 2. Layers
        self.block1 = STGCNBlock(in_channels, 64)
        self.block2 = STGCNBlock(64, 128)
        
        self.fc = nn.Sequential(
            nn.Linear(128 * num_nodes, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def _get_adjacency_matrix(self, num_nodes=42):
        # Connections for one hand (21 nodes)
        connections = [
            (0,1), (1,2), (2,3), (3,4),       # Thumb
            (0,5), (5,6), (6,7), (7,8),       # Index
            (0,9), (9,10), (10,11), (11,12),  # Middle
            (0,13), (13,14), (14,15), (15,16),# Ring
            (0,17), (17,18), (18,19), (19,20) # Pinky
        ]
        
        adj = torch.eye(num_nodes)
        # Hand 1
        for i, j in connections:
            adj[i, j] = 1
            adj[j, i] = 1
        # Hand 2 (shifted by 21)
        for i, j in connections:
            adj[i+21, j+21] = 1
            adj[j+21, i+21] = 1
            
        # Normalize adjacency matrix
        row_sum = adj.sum(1)
        d_inv_sqrt = torch.pow(row_sum, -0.5).flatten()
        d_inv_sqrt[torch.isinf(d_inv_sqrt)] = 0.
        d_mat_inv_sqrt = torch.diag(d_inv_sqrt)
        return torch.mm(torch.mm(d_mat_inv_sqrt, adj), d_mat_inv_sqrt)

    def forward(self, x):
        # Input shape: (batch, 30, 126) -> Reshape to (batch, 30, 42, 3)
        batch_size, seq_len, _ = x.shape
        x = x.view(batch_size, seq_len, 42, 3)
        
        x = self.block1(x, self.adj)
        x = self.block2(x, self.adj)
        
        # Global temporal pooling (take the mean across the 30 frames)
        x = torch.mean(x, dim=1) # (batch, 42, 128)
        x = x.flatten(1) # (batch, 42 * 128)
        
        return self.fc(x)

class SingleHandSTGCN(nn.Module):
    def __init__(self, num_classes):
        super(SingleHandSTGCN, self).__init__()
        # Input: (batch, 30, 63)
        self.layer1 = nn.Sequential(
            nn.Linear(63, 128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        self.lstm = nn.LSTM(128, 256, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.layer1(x)
        x, _ = self.lstm(x)
        x = x[:, -1, :] # Take last frame
        x = self.fc(x)
        return x
