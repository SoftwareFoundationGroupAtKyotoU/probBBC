# -*- coding: utf-8 -*-

from abc import ABC
import sys, random
import socket
import pickle
import copy
from py4j.java_gateway import JavaGateway, GatewayParameters, CallbackServerParameters
from aalpy.base import Automaton, AutomatonState
from aalpy.SULs import MdpSUL
from aalpy.utils import load_automaton_from_file
from StrategyBridge import StrategyBridge

socket_path = '/tmp/multivesta.sock'
example = 'shared_coin'

class MyModel(ABC):
	def __init__(self):
		print("MV_python_integrator setup\n")
		mdp = load_automaton_from_file(f'/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot', automaton_type='mdp')
		self.sul = MdpSUL(mdp)
		# == デバッグ用 ==
		self.prism_model_path = f'/Users/bo40/workspace/python/mc_exp.prism'
		self.prism_adv_path = f'/Users/bo40/workspace/python/adv.tra'
		# ====
		self.strategy_bridge = StrategyBridge(self.prism_adv_path, self.prism_model_path)
		self.number_of_steps = 0
		self.current_output = None
		self.exec_trace = []
		self.cex_candidate = []
		self.prob_bbc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.prob_bbc_socket.connect(socket_path)
		self.prob_bbc_socket.send(pickle.dumps("Initialized MyModel (MV_python_integrator.py)\n"))

	def setSimulatorForNewSimulation(self):
		self.number_of_steps = 0
		self.current_output = self.sul.pre()
		self.strategy_bridge.reset()
		self.prob_bbc_socket.send(pickle.dumps({"current_trace" : self.exec_trace}))
		self.exec_trace = []

		# if len(self.cex_candidate) > 0:
		# 	self.prob_bbc_socket.send(pickle.dumps({"cex_candidate" : self.cex_candidate}))
		self.cex_candidate = []

	def one_step(self):
		self.number_of_steps += 1
		"""Next step is determined based on transition probabilities of the current state.
		Args:
				letter: input
		Returns:
				output of the current state
		"""
		# strategyから次のアクションを決め、SULを実行する
		action = self.strategy_bridge.next_action()
		self.current_output = self.sul.step(action)
		# 実行列を保存
		self.exec_trace.append((action, self.current_output))
		ret = self.strategy_bridge.update_state(action, self.current_output)

		if not ret:
				if len(self.cex_candidate) == 0:
					self.cex_candidate = copy.deepcopy(self.exec_trace)
					# ProbBBCのメインプロセスに反例データを送る
					self.prob_bbc_socket.send(pickle.dumps({"cex": self.cex_candidate}))

		return self.current_output

	def get_time(self):
		return self.number_of_steps

	def eval(self, observation):
		if self.current_output == None:
			return 0
		else:
			# MDPの出力は次のような文字列 'agree__six__c1_tails__c2_tails'
			if observation in self.current_output.split('__'):
				return 1
			else:
				return 0



class SimulationWrapper(object):

	# constructor for Python
	def __init__(self, model):
		self.model = model

	# code to let multivesta initialize the simulator for a new simulation
	# that is, re-initialize the model to its initial state, and set the
	# new random seed
	def setSimulatorForNewSimulation(self, random_seed):
		self.model.setSimulatorForNewSimulation()	
			#Here you should replace 'setSimulatorForNewSimulation(random_seed)' 
			# with a method of your model to 
			#- set the new nuovo random seed
			#- reset the status of the model to the initial one
			#

	# code to let multivesta ask the simulator to perform a step of simulation
	def performOneStepOfSimulation(self):
		self.model.one_step()
		#Here you should replace 'one_step()' with
		# your method to perform a step of simulation 

	# code to let multivesta ask the simulator to perform a
	# "whole simulation"
	# (i.e., until a stopping condition is found by the simulator)
	def performWholeSimulation(self):
		print('Not supported\n')

	# code to let multivesta ask the simulator the current simulated time
	def getTime(self):
		return float(self.model.get_time())
		#Here you should replace 'getTime()' with
		# your method to get the current simulation time 
		# (or number of simulation step)


	# code to let multivesta ask the simulator to return the value of the
	# specified observation in the current state of the simulation
	def rval(self, observation):
		return float(self.model.eval(observation))
		#Here you should replace 'eval(observation)' with
		# your method to evaluate an observation in the 
		# current simulation step 

	class Java:
		implements = ['vesta.python.IPythonSimulatorWrapper']


if __name__ == '__main__':
	porta = int(sys.argv[1])
	callback_porta = int(sys.argv[2])
	print('Python engine: expecting connection with java on port: '+str(porta)+' and callback connection on port '+str(callback_porta))
	gateway = JavaGateway(start_callback_server=True,gateway_parameters=GatewayParameters(port=porta),callback_server_parameters=CallbackServerParameters(port=callback_porta))
	
	#Here you should put any initialization code you need to create an instance of
	#your model_file_name class
	
	model=MyModel()

	gateway.entry_point.playWithState(SimulationWrapper(model))