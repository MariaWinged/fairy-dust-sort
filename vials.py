from typing import Optional, Self

COLOR_DIMENSION = 4
VIAL_HEIGHT = 4


class Vial:
    def __init__(self, *segments: int):
        self._value = 0
        l = 0
        for s in reversed(segments):
            self._value <<= COLOR_DIMENSION
            self._value += s
            l += 1
        if l == 1 and self._value >= 1 << COLOR_DIMENSION:
            return
        for i in range(VIAL_HEIGHT - l):
            self._value <<= COLOR_DIMENSION

    @classmethod
    def from_string(cls, string: str):
        return cls(*map(int, string.split("/")))

    def __len__(self) -> int:
        l = 0
        while 1 << (COLOR_DIMENSION * l) < self._value:
            l += 1
        return l

    def __str__(self) -> str:
        vial_str = ""
        value = self._value
        it_first = True
        while value:
            color = value & ((1 << COLOR_DIMENSION) - 1)
            vial_str += "/" + str(color) if not it_first else str(color)
            value >>= COLOR_DIMENSION
            it_first = False
        return vial_str

    @property
    def list(self) -> list[int]:
        vial_list = []
        value = self._value
        while value:
            color = value & ((1 << COLOR_DIMENSION) - 1)
            vial_list.append(color) if color else None
            value >>= COLOR_DIMENSION
        return vial_list

    def pop(self) -> int:
        color = self._value >> (COLOR_DIMENSION * (VIAL_HEIGHT - 1))
        self._value <<= COLOR_DIMENSION
        self._value &= (1 << (COLOR_DIMENSION * VIAL_HEIGHT)) - 1
        return color

    def append(self, color: int) -> None:
        self._value >>= COLOR_DIMENSION
        self._value |= color << (COLOR_DIMENSION * (VIAL_HEIGHT - 1))

    @property
    def is_empty(self) -> bool:
        return not self._value

    @property
    def last(self) -> int:
        return self._value >> (COLOR_DIMENSION * (VIAL_HEIGHT - 1))

    @property
    def is_free(self) -> bool:
        return not self._value & ((1 << COLOR_DIMENSION) - 1)

    @property
    def value(self) -> int:
        return self._value

    @property
    def is_fill_single_colored(self) -> bool:
        color = self.last
        fill_colored = 0
        for i in range(VIAL_HEIGHT):
            fill_colored <<= COLOR_DIMENSION
            fill_colored += color
        return self._value == fill_colored


class VialSet:
    def __init__(self, vials: Optional[list[Vial]] = None):
        self._vials = vials if vials else []

    @classmethod
    def from_str(cls, hash_str: str) -> Self:
        vial_set = cls()
        for vial_value in map(int, hash_str.split("/")):
            vial_set.add(Vial(vial_value))
        return vial_set

    def __str__(self):
        sorted_vials = [vial.value for vial in self._vials]
        sorted_vials.sort()
        return "/".join(str(vial) for vial in sorted_vials)

    def __len__(self):
        return len(self._vials)

    def add(self, vial: Vial):
        self._vials.append(vial)

    @property
    def is_sorted(self) -> bool:
        for vial in self._vials:
            if not vial.is_fill_single_colored:
                return False
        return True

    def can_transfer(self, index_from: int, index_to: int) -> bool:
        if index_from == index_to:
            return False
        vial_from = self._vials[index_from]
        vial_to = self._vials[index_to]
        if vial_from.is_empty:
            return False
        return vial_to.is_empty or vial_from.last == vial_to.last and vial_to.is_free

    @staticmethod
    def _transfer(vial_from: Vial, vial_to: Vial) -> int:
        transfers_count = 0
        while not vial_from.is_empty and (vial_from.last == vial_to.last or vial_to.is_empty) and vial_to.is_free:
            vial_to.append(vial_from.pop())
            transfers_count += 1
        return transfers_count

    def transfer(self, index_from: int, index_to: int) -> int:
        if index_from == index_to:
            return 0
        vial_from = self._vials[index_from]
        vial_to = self._vials[index_to]
        return self._transfer(vial_from, vial_to)

    def transfer_str(self, str_from: str, str_to: str) -> tuple[int, int]:
        vial_from, vial_to = None, None
        index_from, index_to = None, None
        for i, vial in enumerate(self._vials):
            if str(vial) == str_from and not vial_from:
                vial_from = vial
                index_from = i
            elif str(vial) == str_to and not vial_to:
                vial_to = vial
                index_to = i
            if vial_from is not None and vial_to is not None:
                break
        self._transfer(vial_from, vial_to)
        return index_from, index_to

    def cancel_transfer(self, index_from: int, index_to: int, count: int):
        vial_from = self._vials[index_from]
        vial_to = self._vials[index_to]
        for _ in range(count):
            vial_from.append(vial_to.pop())

    def get_vial(self, index):
        return self._vials[index]

    def validate(self):
        colors = [0] * (len(self._vials) - 1)
        for vial in self._vials:
            for color in vial.list:
                colors[color] += 1
        for i in range(1, len(colors)):
            if colors[i] != VIAL_HEIGHT:
                raise ValueError


class StateGraph:
    def __init__(self, vial_set: VialSet):
        vial_set.validate()
        initial_state = str(vial_set)
        self._current_state = 0
        self._states_queue = [initial_state]
        self._states_set = set()
        self._states_set.add(initial_state)
        self._is_solution_found = vial_set.is_sorted
        self._operations = [(("", ""), -1)]
        self._solution_state = -1

    def _calculate_state(self, vial_set: VialSet, index_from: int, index_to: int):
        count = vial_set.transfer(index_from, index_to)
        state = str(vial_set)
        if count and state not in self._states_set:
            self._states_queue.append(state)
            self._states_set.add(state)
            if vial_set.is_sorted and not self._is_solution_found:
                self._is_solution_found = True
                self._solution_state = len(self._states_queue) - 1
            vial_set.cancel_transfer(index_from, index_to, count)
            self._operations.append(
                ((str(vial_set.get_vial(index_from)), str(vial_set.get_vial(index_to))), self._current_state)
            )
        else:
            vial_set.cancel_transfer(index_from, index_to, count)

    def _step(self):
        vial_set = VialSet.from_str(self._states_queue[self._current_state])
        for v1 in range(len(vial_set) - 1):
            v2 = v1 + 1
            while v2 < len(vial_set) and (vial_set.can_transfer(v2, v1) or vial_set.can_transfer(v1, v2)):
                self._calculate_state(vial_set, v2, v1)
                self._calculate_state(vial_set, v1, v2)
                v2 += 1
        self._current_state += 1

    def build_graph(self) -> list[tuple[str, str]]:
        while self._current_state < len(self._states_queue):
            self._step()
        path = [self._operations[self._solution_state][0]]
        state = self._operations[self._solution_state][1]
        while state != 0:
            path.append(self._operations[state][0])
            state = self._operations[state][1]
        path.reverse()
        return path
