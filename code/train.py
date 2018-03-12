from __future__ import print_function

import os
import argparse
from ipdb import set_trace as brk
from logger import Logger

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
from torch.autograd import Variable

import torchvision
import torchvision.transforms as transforms
from dataloader import DenseLidarGen

# from DenseLidarNet import DenseLidarNet
from chamfer_loss import *
from vfe_layer import *



class Main(object):

	def __init__(self):

		self.batch_size = 2
		self.max_pts_in_voxel = 20
		self.logger = Logger('./logs')
		#normalize  = transforms.Normalize((0.485,0.456,0.406), (0.229,0.224,0.225)
		self.transform = transforms.Compose([transforms.ToTensor()])
		self.dataset = DenseLidarGen('../../DenseLidarNet_data/all_annt_train.pickle','/home/ishan/images',self.transform)
		self.dataloader = torch.utils.data.DataLoader(self.dataset, batch_size=self.batch_size, shuffle=True, num_workers=1, collate_fn=self.dataset.collate_fn)
		
		# self.load_model()
		self.h = 20
		self.w = 10
		self.load_model()
		self.criterion = ChamferLoss()
		self.optimizer = optim.SGD(self.net.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-4)



	def load_model(self):
		self.net  = DenseLidarNet()
		self.net.load_state_dict(torch.load('./scripts/net.pth'))
		# assert torch.cuda.is_available(), 'Error: CUDA not found!'
		
		# self.net = torch.nn.DataParallel(self.net, device_ids=range(torch.cuda.device_count()))
		# self.net.cuda()


	def train(self):

		train_loss = 0
		for batch_idx,(voxel_features,voxel_mask,voxel_indices, chamfer_gt) in enumerate(self.dataloader):
			voxel_features = Variable(voxel_features)
			voxel_mask = Variable(voxel_mask.squeeze())
			voxel_indices = Variable(voxel_indices.unsqueeze(1).expand(voxel_indices.size()[0],128))
			vfe_output = Variable(torch.zeros(self.batch_size*self.h*self.w,128))

			self.optimizer.zero_grad()
			
			xyz_output= self.net.forward(voxel_features,voxel_mask,voxel_indices,vfe_output)
			print(xyz_output)
			loss = self.criterion(xyz_output, Variable(chamfer_gt))
			train_loss += loss.data[0]
			print('train_loss: %.3f' % (loss.data[0]))
			self.optimizer.zero_grad()
			loss.backward()
			self.optimizer.step()

			torch.save(self.net.state_dict(), '../../model_state.pth')
			torch.save(self.optimizer.state_dict(), '../../opt_state.pth')

			for param in self.net.parameters():
				print(param.data)			
		



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Dense LiDarNet Training')
	parser.add_argument('--lr', default=1e-4, type=float, help='learning rate')
	parser.add_argument('--resume', '-r', default=False, type=bool, help='resume from checkpoint')
	args = parser.parse_args()

	print ("****************************************************************************************")
	print ("Using Learning Rate     ==============> {}".format(args.lr))
	print ("Loading from checkpoint ==============> {}".format(args.resume))
	print ("****************************************************************************************")


	net = Main()
	net.train()
	
			

