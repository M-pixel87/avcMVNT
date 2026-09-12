# Pathfinding Algorithms

<br>

## Breadth First Search
### Purpose
breadth first search is one of the most simple pathfinding algorithms we could use.
The reason I have put such a simple algorithm in here is because we need to start with these basic 
algorithms to build to the larger ones and also they arnt so bad sometimes. 

### Explanation
It is as it sounds in the name: It just expands in all directions at every node it parses. Meaning it 
focuses on expanding in breadth. Maybe the only thing more simple is like a drunk man walking? maybe even 
that is more complex.

<br>

## Dijskra's Algorithm
### Purpose
Dijskra's Algorithm is a simple pathfinding algorithm that is the ancestor of many other top pathfinding algoirthms
that will be tested. EX: A* . Dijskra's Algorithm should present a better path aswell as possibly more computationally
efficent vs the breadth search where alot of squares must be checked.

### Explanation
Dijskta's algorithm is beautifully simple. It uses weighted graphs in the form of distance usually as a cost value.
Then as you search towards the endpoint you sum up the total cost to get to the end. For example on point A it may cost
3 to go to b or 5 to go to c, so you search b first which may cost 5 to go to E (your end point). so the total cost of
going the b route is 8 , but then if we checked going c it then may cost only 2 to get to E from there, equating to 7 total
cost. Therefore after evaluating the paths we can trace the path of least resistance like a electrical circuit.

One issue is with our grid based representation all nearby nodes are equally distanced. This means that it will pretty much mimic
the breadth first search but it may come to a more optimal path. 

The algorithm is able to avoid traps because falling into a trap would increase the cost to get to the end point , so it would avoid the trap for the final path.

<br>

## A* algorithm
### Purpose
This is an extention on Dijsktra's algorithm. This can make the algorithm better for your 

### Explanation
This is a beautiful and logical modification to Dijsktra's algorithm where we utelize a heuristic. What is a heuristic? This is just 
a function that we can make whatever we want to add score or take away score, a modification usuallty done for A* is scoreing
based on distances from target, so then the scores will favor closer nodes , or something like that, it can be anything you 
want.
