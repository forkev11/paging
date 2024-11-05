from random import randint

class Process:
    def __init__(self, id: int=0, maximum_estimated_time: int=1, operation: str="", result: float=0.0, quantum: float=1.0, size: int=6):
        self.id = id
        self.maximum_estimated_time = maximum_estimated_time
        self.operation = operation
        self.result = result
        self.elapsed_time = 0.0
        
        self._response_time = 0.0
        self._isset = False
        
        self.arrival_time = 0.0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.completion_time = 0.0
        self.burst_time = 0.0
        
        self.temp_time = 8.0
        self.flag = False

        self.quantum = quantum

        self.size = size
        
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def maximum_estimated_time(self):
        return self._maximum_estimated_time

    @maximum_estimated_time.setter
    def maximum_estimated_time(self, value: int):
        self._maximum_estimated_time = value

    @property
    def operation(self):
        return self._operation

    @operation.setter
    def operation(self, value):
        self._operation = value

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value: float):
        self._result = value
        
    @property
    def n_batch(self):
        return self._n_batch

    @n_batch.setter
    def n_batch(self, value: int):
        self._n_batch = value

    @property
    def elapsed_time(self):
        return self._elapsed_time

    @elapsed_time.setter
    def elapsed_time(self, value):
        self._elapsed_time = value

    @property
    def completion_time(self):
        return self._completion_time

    @completion_time.setter
    def completion_time(self, value):
        self._completion_time = value
        
    @property
    def arrival_time(self):
        return self._arrival_time

    @arrival_time.setter
    def arrival_time(self, value):
        self._arrival_time = value
        
    @property
    def response_time(self):
        return self._response_time

    @response_time.setter
    def response_time(self, value):
        if not self._isset:
            self._response_time = value
            self._isset = True

    @property
    def burst_time(self):
        return self._burst_time

    @burst_time.setter
    def burst_time(self, value):
        self._burst_time = value
        
    @property
    def temp_time(self):
        return self._temp_time

    @temp_time.setter
    def temp_time(self, value):
        self._temp_time = value

    @property
    def quantum(self):
        return self._quantum

    @quantum.setter
    def quantum(self, value):
        self._quantum = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value