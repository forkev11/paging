from textual.widget import Widget
from textual.app import App
from rich.table import Table
from rich.text import Text
from collections import deque
from typing import Tuple
from process import Process
from math import isclose
from random_data import data_gen
from textual.reactive import Reactive
from typing import List
from textual.widgets import ScrollView
from math import ceil
from random import randint
from time import sleep

FRAME_SIZE = 4

class Frame:
    def __init__(self, value=False) -> None:
        self.container = [value for _ in range(FRAME_SIZE)]
        self.process_id = None
        self.status = "free"

    def is_free(self) -> bool:
        return self.container.count(False) == FRAME_SIZE

    def allocate(self, spaces: int) -> None:
        self.container = [True for _ in range(spaces)]
        self.container.extend([False for _ in range(FRAME_SIZE - spaces)])

    def deallocate(self) -> None:
        self.container = [False for _ in range(FRAME_SIZE)]
        self.process_id = None

    def color(self) -> str:

        match self.status:
            case "free":
                return "white"
            case "ready":
                return "yellow"
            case "execution":
                return "green"
            case "blocked":
                return "red"
            case _:
                return "blue"

    def __str__(self) -> str:
        return f"{self.container.count(True)}/{FRAME_SIZE}"

class Memory:
    def __init__(self) -> None:
        self.frames = ([Frame() for i in range(46)])
        self.frames.extend([Frame(True) for i in range(4)])
        for i in range(4):
            self.frames[46+i].status = "os"

    def free_frames(self) -> List[Frame]:
        f = []
        for frame in self.frames:
            if frame.is_free():
                f.append(frame)
        return f

    def get_next(self) -> Frame:
        for frame in self.frames:
            if frame.is_free():
                return frame

class RR(Widget):
    _run = True
    _error = False
    _interruption = False
    _execution = Process()
    _new = deque()
    _finished = deque()
    _ready = deque()
    _blocked = deque()
    _memory = Memory()
    
    def __init__(self, title: str="", cols: Tuple[str, ...]=("",), name: str="None") -> None:
        super().__init__(name=name)
        self._title = Text(title, style="#5E81AC")
        self._cols = cols

    def refresh(self, repaint: bool=False , layout: bool = True) -> None:
        super().refresh(repaint, layout)

    def on_mount(self) -> None:
        self.set_interval(0.1, self.refresh)

class ReadyProcessesTable(RR):
    
    def __init__(self, title: str = "", cols: Tuple[str, ...] = ("", ), name: str="None") -> None:
        super().__init__(title, cols, name)
        self.first = True

    def render(self) -> Table:
        if not MyApp._clock._stop:
            while RR._new and len(RR._memory.free_frames()) >= ceil(RR._new[0].size / FRAME_SIZE):
                p = RR._new.popleft()
                n1 = p.size // FRAME_SIZE
                n2 = p.size % FRAME_SIZE
                for i in range(n1):
                    frame = RR._memory.get_next()
                    frame.process_id = p.id
                    frame.allocate(FRAME_SIZE)
                    frame.status = "ready"
                
                if n2 != 0:
                    frame = RR._memory.get_next()
                    frame.process_id = p.id
                    frame.allocate(n2)
                    frame.status = "ready"

                p.arrival_time = 0.0 if self.first else MyApp._clock._elapsed

                RR._ready.append(p)
            
            if (not RR._execution and RR._ready) or self.first:
                RR._execution = RR._ready.popleft()
                frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                for frame in frames:
                    frame.status = "execution"
                RR._execution.response_time = 0.0 if self.first else MyApp._clock._elapsed
                self.first = False
                RR._execution.flag = True
                
            self._table = Table(title=self._title, expand=True, show_lines=True, style="#D8DEE9") 
            
            for col in self._cols:
                self._table.add_column(Text(col, justify="center", style="#88C0D0"))
            
            for process in RR._ready:
                self._table.add_row(Text(str(process.id), justify="center"),
                                    Text(f"{process.maximum_estimated_time:.2f}", justify="center"),
                                    Text(f"{process.elapsed_time:.2f}", justify="center"))
            
        return self._table

class ExecutionProcessTable(RR):

    def __init__(self, title: str = "", cols: Tuple[str, ...] = ("", )) -> None:
        super().__init__(title, cols)

    def render(self) -> Table:  
        if not MyApp._clock._stop:
            
            self._table = Table(title=self._title, expand=True, show_lines=True, style="#D8DEE9") 
            
            for col in self._cols:
                self._table.add_column(Text(col, justify="center", style="#88C0D0"))

            if not RR._execution and (RR._interruption or RR._error):
                RR._interruption, RR._error = False, False
            
            if RR._execution:
                if isclose(RR._execution.maximum_estimated_time, RR._execution.elapsed_time, abs_tol=1e-05):
                    RR._execution.completion_time = MyApp._clock._elapsed
                    RR._finished.append(RR._execution)

                    frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                    for frame in frames:
                        frame.deallocate()
                        frame.status = "free"

                    RR._execution = RR._ready.popleft() if RR._ready else None
                    if RR._execution:
                        RR._execution.response_time = MyApp._clock._elapsed if not RR._execution.flag else RR._execution.response_time
                        RR._execution.flag = True
                        frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                        for frame in frames:
                            frame.status = "execution"

            if RR._execution: 
                if RR._execution and isclose(RR._execution.quantum, 0.0, abs_tol=1e-05):
                    RR._execution.quantum = RR._quantum

                    frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                    for frame in frames:
                        frame.status = "ready"

                    RR._ready.append(RR._execution)
                    
                    RR._execution = RR._ready.popleft()
                    RR._execution.response_time = round(MyApp._clock._elapsed) if not RR._execution.flag else RR._execution.response_time
                    frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                    for frame in frames:
                        frame.status = "execution"
                    
                    RR._execution.flag = True

            if RR._execution:                       
                if RR._interruption:
                    
                    frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                    for frame in frames:
                        frame.status = "blocked"

                    RR._blocked.append(RR._execution)
                    RR._execution = RR._ready.popleft() if RR._ready else None  
                    if RR._execution:
                        frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                        for frame in frames:
                            frame.status = "execution"
                        RR._execution.response_time = MyApp._clock._elapsed if not RR._execution.flag else RR._execution.response_time
                        RR._execution.flag = True
                    
                    RR._interruption = False

                if RR._error:
                    RR._execution.result = "Error"
                    RR._execution.completion_time = MyApp._clock._elapsed
                    RR._finished.append(RR._execution)

                    frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                    for frame in frames:
                        frame.deallocate()
                        frame.status = "free"

                    RR._execution = RR._ready.popleft() if RR._ready else None
                    if RR._execution:
                        frames = list(filter(lambda x: x.process_id == RR._execution.id, RR._memory.frames))
                        for frame in frames:
                            frame.status = "execution"
                        RR._execution.response_time = MyApp._clock._elapsed if not RR._execution.flag else RR._execution.response_time
                        RR._execution.flag = True
                        
                    RR._error = False
            
            if RR._execution:
                self._table.add_row(Text(str(RR._execution.id)),
                                    Text(RR._execution.operation, justify="center"),
                                    Text(f"{RR._execution.maximum_estimated_time:.2f}", justify="center"),
                                    Text(f"{RR._execution.elapsed_time:.2f}"),
                                    Text(f"{RR._execution.maximum_estimated_time - RR._execution.elapsed_time:.2f}"))
                                    
                RR._execution.quantum -= 1e-01     
                RR._execution.elapsed_time += 1e-01
            
        return self._table

class BlockedProcessesTable(RR):
    
    def __init__(self, title: str = "", cols: Tuple[str, ...] = ("", )) -> None:
        super().__init__(title, cols)
        self._count = 8.0
        self._free = True
        self._first = None 
        self.helper = deque()    

    def render(self) -> Table:
        if not MyApp._clock._stop:
            self._table = Table(title=self._title, expand=True, show_lines=True, style="#D8DEE9") 
            
            for col in self._cols:
                self._table.add_column(Text(col, justify="center", style="#88C0D0"))
            
            if not RR._blocked and self._free:
                    self._first = None
            
            finished = deque()
            
            for v in RR._blocked:
                v.temp_time -= 0.1
                if isclose(v.temp_time, 0.0, abs_tol=1e-03):
                    v.temp_time = 8.0
                    
                    frames = list(filter(lambda x: x.process_id == v.id, RR._memory.frames))
                    for frame in frames:
                        frame.status = "ready"

                    RR._ready.append(v)
                    finished.append(v)
                
            for v in finished:
                RR._blocked.remove(v)
            
                MyApp._blocked_processes_table.refresh(repaint=False, layout=True)
            for v in RR._blocked:
                self._table.add_row(Text(str(v.id), justify="center"),
                                    Text(f"{v.temp_time:05.2f}", justify="center"))
                
        return self._table

class SummaryProcessTable(RR):

    def __init__(self, title: str = "", cols: Tuple[str, ...] = ("", )) -> None:
        super().__init__(title, cols)

    def render(self) -> Table:
        if not MyApp._clock._stop:
            self._table = Table(title=self._title, expand=True, show_lines=True, style="#D8DEE9") 
            
            for col in self._cols:
                self._table.add_column(Text(col, justify="center", style="#88C0D0"))

            for process in RR._finished:
                self._table.add_row(Text(str(process.id), justify="center"),
                                    Text(str(process.operation), justify="center"),
                                    Text(f"{process.result:05.2f}" if isinstance(process.result, float) else process.result, justify="center", style="#BF616A" if process.result == "Error" else "#A3BE8C"),
                                    Text(f"{process.maximum_estimated_time:05.2f}", justify="center"),
                                    Text(f"{process.completion_time:05.2f}", justify="center"),
                                    Text(f"{process.arrival_time:05.2f}", justify="center"),
                                    Text(f"{float(process.completion_time) - float(process.arrival_time):05.2f}", justify="center"),
                                    Text(f"{float(process.response_time) - float(process.arrival_time):05.2f}", justify="center"),
                                    Text(f"{process.elapsed_time:05.2f}", justify="center"),
                                    Text(f"{float(process.completion_time) - float(process.arrival_time) - process.elapsed_time:05.2f}", justify="center"))
        return self._table

class MemoryTable(RR):
    def __init__(self, title: str = "", cols: Tuple[str, ...] = ("", )) -> None:
        super().__init__(title, cols)
        self.frame_size = 4

    def render(self) -> Table:
        if not MyApp._clock._stop:
            self._table = Table(title=self._title, expand=True, show_lines=True, style="#D8DEE9")
            
            for col in self._cols:
                self._table.add_column(Text(col, justify="center", style="bold #88C0D0"))

            for i in range(25):
                self._table.add_row(Text(f"{i}", style="italic"), Text(f"{RR._memory.frames[i]}", style=f"bold {RR._memory.frames[i].color()}"), Text(f"{RR._memory.frames[i].process_id}"),
                                    Text(f"{i+25}", style="italic"), Text(f"{RR._memory.frames[i+25]}", style=f"bold {RR._memory.frames[i+25].color()}"), Text(f"{RR._memory.frames[i+25].process_id}"))

        return self._table

class Clock(Widget):

    _stop = False
    _elapsed = 0.0
    _delayed = True

    def __init__(self, name: str="Clock") -> None:
        super().__init__(name=name)

    def on_mount(self) -> None:
        self.set_interval(0.1, self.refresh)

    def refresh(self, repaint: bool=False , layout: bool = True) -> None:
        super().refresh(repaint, layout)
    
    def render(self) -> Text:
        if not self._stop:
            if RR._len != len(RR._finished):
                self._elapsed += 0.1 if not self._delayed else 0.0
                self._delayed = False
                return Text(f"{self._elapsed//60:02.0f}:{self._elapsed%60:05.2f}")

        return Text(f"{self._elapsed//60:02.0f}:{self._elapsed%60:05.2f}")

class MyText(Widget):
    def render(self) -> Text:
        txt = f"\nSiguiente: ID: {RR._new[0].id if RR._new else '-'}, Tam: {RR._new[0].size if RR._new else '-'}"
        return Text(f"Procesos nuevos: {len(RR._new)}{txt}")
    
    def refresh(self, repaint: bool=False , layout: bool = True) -> None:
        super().refresh(repaint, layout)
    
    def on_mount(self) -> None:
        self.set_interval(0.1, self.refresh)
        
class PCBTable(Widget):
    def __init__(self, name=None, title: str = "", cols: Tuple[str, ...] = ("", )) -> None:
        super().__init__(name=name)
        self._title = title
        self._cols = cols
        self._flag = True

    def render(self) -> Table:

        self._table = Table(title=Text(self._title, style="#5E81AC"), expand=True, show_lines=True, style="#D8DEE9") 
        
        for col in self._cols:
            self._table.add_column(Text(str(col), justify="center", style="#88C0D0"))
            
        for process in RR._new:
            self._table.add_row(Text(str(process.id), justify="center"),
                                Text(str(process.operation), justify="center"),
                                Text("-", justify="center"),
                                Text("Nuevo", justify="center"),
                                Text(f"{process.maximum_estimated_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text("-", justify="center"),
                                Text("-", justify="center"),
                                Text("-", justify="center"),
                                Text("-", justify="center"),
                                Text("-", justify="center"),
                                Text("-", justify="center"))
        
        for process in RR._ready:
                self._table.add_row(Text(str(process.id), justify="center"),
                                Text(str(process.operation), justify="center"),
                                Text("-", justify="center"),
                                Text("Listo", justify="center"),
                                Text(f"{process.maximum_estimated_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text(f"{process.arrival_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text(f"{float(process.response_time) - float(process.arrival_time):05.2f}" if process.flag else "-", justify="center"),
                                Text(f"{process.elapsed_time:05.2f}", justify="center"),
                                Text(f"{float(MyApp._clock._elapsed) - float(process.arrival_time) - process.elapsed_time:05.2f}", justify="center"),
                                Text("-", justify="center"))

        if RR._execution:
            self._table.add_row(Text(str(RR._execution.id), justify="center"),
                                Text(str(RR._execution.operation), justify="center"),
                                Text("-", justify="center"),
                                Text(f"Ejecucion", justify="center"),
                                Text(f"{RR._execution.maximum_estimated_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text(f"{RR._execution.arrival_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text(f"{float(RR._execution.response_time) - float(RR._execution.arrival_time):05.2f}", justify="center"),
                                Text(f"{RR._execution.elapsed_time - 0.1:05.2f}", justify="center"),
                                Text(f"{abs(float(MyApp._clock._elapsed) - float(RR._execution.arrival_time) - RR._execution.elapsed_time + 0.1):05.2f}", justify="center"),
                                Text("-", justify="center"))
        
        for process in RR._blocked:
                        self._table.add_row(Text(str(process.id), justify="center"),
                                Text(str(process.operation), justify="center"),
                                Text("-", justify="center"),
                                Text(f"Bloqueado", justify="center"),
                                Text(f"{process.maximum_estimated_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text(f"{process.arrival_time:05.2f}", justify="center"),
                                Text("-", justify="center"),
                                Text(f"{float(process.response_time) - float(process.arrival_time):05.2f}", justify="center"),
                                Text(f"{process.elapsed_time:05.2f}", justify="center"),
                                Text(f"{float(MyApp._clock._elapsed) - float(process.arrival_time) - process.elapsed_time:05.2f}", justify="center"),
                                Text(f"{process.temp_time:05.2f}", justify="center"))
        
        for process in RR._finished:
            self._table.add_row(Text(str(process.id), justify="center"),
                                Text(str(process.operation), justify="center"),
                                Text(f"{process.result:05.2f}" if isinstance(process.result, float) else process.result, justify="center", style="#BF616A" if process.result == "Error" else "#A3BE8C"),
                                Text(f"Finalizado", justify="center"),
                                Text(f"{process.maximum_estimated_time:05.2f}", justify="center"),
                                Text(f"{process.completion_time:05.2f}", justify="center"),
                                Text(f"{process.arrival_time:05.2f}", justify="center"),
                                Text(f"{float(process.completion_time) - float(process.arrival_time):05.2f}", justify="center"),
                                Text(f"{float(process.response_time) - float(process.arrival_time):05.2f}", justify="center"),
                                Text(f"{process.elapsed_time:05.2f}", justify="center"),
                                Text(f"{float(process.completion_time) - float(process.arrival_time) - process.elapsed_time:05.2f}", justify="center"),
                                Text("-", justify="center"))
        
        return self._table

class MyApp(App):

    _clock = Clock()

    _ready_process_table = ReadyProcessesTable(cols=("ID", "TME", "TT"), title="Cola de listos")
    _process_table = ExecutionProcessTable(cols=("ID", "Operación", "TME", "TT", "TR"), title="Proceso en ejecución")
    _blocked_processes_table = BlockedProcessesTable(cols=("ID", "TRB"), title="Cola de bloqueados")
    _memory_table = MemoryTable(cols=("#", "%", "ID", "#", "%", "ID"), title="Memoria")
    _finished_process_table = SummaryProcessTable(cols=("ID", "Operación", "Resultado", "TME", "TF", "TLl", "TRet", "TRes", "TS", "TE"),  title="Procesos terminados")
    _remaining_processes = MyText()
    _bar = PCBTable(cols=("ID", "Operación", "Resultado", "Estado", "TME", "TF", "TLl", "TRet", "TRes", "TS", "TE", "TRB"),  title="Bloque de control de procesos")
    
    show_bar = Reactive(True)

    def watch_show_bar(self, show_bar: bool) -> None:
        self._bar.animate("layout_offset_x", 0 if show_bar else -275, duration=0.01)
    
    async def on_mount(self) -> None:
        
        self._bar.layout_offset_x = -275
        
        self.grid = await self.view.dock_grid(name="main", size=0)
        
        await self.view.dock(self._bar, edge="bottom", size=275, z=1)
    
        self.grid.add_column(fraction=1, name="left", size=45)
        self.grid.add_column(size=40, name="center_left")
        self.grid.add_column(size=50, name="center_right")
        self.grid.add_column(fraction=1, name="right", size=55)
        
        self.grid.add_row(fraction=1, name="top", size=20)
        self.grid.add_row(fraction=1, name="middle", size=5)
        self.grid.add_row(fraction=1, name="bottom")
        
        self.grid.add_areas(
            bar="left-start|right-end, top-start|bottom-end",
            ready="left,top",
            execution="center_left-start|center_right-end,top",
            blocked="right,top",
            memory="left-start|center_left-start, bottom",
            finished="center_right-start|right-end, bottom",
            clock="right,middle",
            processes="left,middle"
        )

        self.grid.set_align("center", "center")
        self.grid.place(ready=ScrollView(self._ready_process_table, auto_width=True, style="white"), execution=self._process_table, finished=ScrollView(self._finished_process_table, auto_width=True), memory=ScrollView(self._memory_table), blocked=ScrollView(self._blocked_processes_table, auto_width=True), clock=self._clock, processes=self._remaining_processes)


    async def on_load(self, event) -> None:
        await self.bind("p", "pause")
        await self.bind("c", "continue")
        await self.bind("e", "error")
        await self.bind("i", "interruption")
        await self.bind("n", "create")
        await self.bind("t", "pcb")
        await self.bind("a", "pause")
    
    async def action_pause(self) -> None:
        self._clock._stop = True

    async def action_continue(self) -> None:
        self._clock._stop = False
        self.show_bar = False

    async def action_error(self) -> None:
        if not self._clock._stop: 
            RR._error = True

    async def action_interruption(self) -> None:
        if not self._clock._stop: 
            RR._interruption = True
            
    async def action_create(self) -> None:
        if not self._clock._stop: 
            data, RR._index = data_gen(1, RR._index)
            RR._new.append(data.popleft())
            RR._len += 1
            
    async def action_pcb(self) -> None:
        self._clock._stop = True
        self.show_bar = True

if __name__ == "__main__":
    
    while (n := int(input("Ingresa el número de procesos: "))) < 1:
        print("Ingresa un número entero mayor a 0")
    
    RR._quantum = int(input("Ingresa el quantum: "))
    RR._new, RR._index = data_gen(n, quantum=RR._quantum)
    RR._len = n
    
    MyApp.run(log="app.log")
