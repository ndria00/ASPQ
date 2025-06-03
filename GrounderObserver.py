
from typing import List
from clingo import Observer


class GrounderObserver(Observer):
    def rule(self, choice: bool, head: List[int], body: List[int]) -> None:
        print(f"Got rule {head} :- {body}")
        for h in head:
            print(f"{h}, ")
 
        for b in body:
            print(f"{b}, ")