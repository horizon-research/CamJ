
'''
	This class is used to record which HW compute unit is currently occupied by a SW stage.
	Basic assumption is that when a SW stage occupies a HW unit, it won't release the HW unit
	until it finishes all its computation.

	How to ReservationBoard class:
	* check_reservation: to check whether a HW unit is being occupied.
	* reserve_hw_unit: to reserve the HW unit. 
	* reserve_by: to check if a HW unit is reserved by a certain SW stage.
	* release_hw_unit: to release the HW unit for other SW stage use.
'''
class ReservationBoard(object):
	"""docstring for ReservationBoard"""
	def __init__(self, hw_compute_units):
		super(ReservationBoard, self).__init__()
		self.occupation_board = {}
		self.reservation_board = {}
		for hw_unit in hw_compute_units:
			self.reservation_board[hw_unit] = False

	def check_reservation(self, hw_unit):
		if hw_unit in self.reservation_board:
			return self.reservation_board[hw_unit]
		else:
			raise Exception("%s is not in the reservation board" % hw_unit.name)
		
	def reserve_hw_unit(self, sw_stage, hw_unit):
		if self.reservation_board[hw_unit]:
			raise Exception("%s has already been reserved." % hw_unit.name)
		else:
			self.reservation_board[hw_unit] = True
			self.occupation_board[hw_unit] = sw_stage

	def reserve_by(self, sw_stage, hw_unit):
		# check if the hw_unit is reserved or not
		if not self.reservation_board[hw_unit]:
			return False
		# check if the occupied sw stage is the query sw stage
		if self.occupation_board[hw_unit] == sw_stage:
			return True
		else:
			return False

	def release_hw_unit(self, sw_stage, hw_unit):
		self.reservation_board[hw_unit] = False
		self.occupation_board.pop(hw_unit, None)
