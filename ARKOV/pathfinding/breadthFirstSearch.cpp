#include <iostream>
#include <vector>
#include <tuple>
#include <set>
#include <map>
#include <algorithm>
#include <thread>
#include <chrono>

int curx = 0;
int cury = 0;
size_t idx = 0;

std::vector<std::tuple<int, int>> que = {std::make_tuple(curx, cury)};
std::set<std::tuple<int, int>> queued = {std::make_tuple(curx, cury)};

// Format is { (target_x, target_y) : (source_x, source_y) }
// Using (-1, -1) to represent 'None'
std::map<std::tuple<int, int>, std::tuple<int, int>> came_from = {
    {std::make_tuple(curx, cury), std::make_tuple(-1, -1)}
};

/*
0 = not checked
1 = checked
2 = obstacle
3 = endpoint
4 = path 
*/

int map[10][10] = {
    {1,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {2,2,2,2,2,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,0},
    {0,0,0,0,0,0,0,0,0,3}
};

void check_neihbors() {
    // check right
    if (curx + 1 <= 9 && map[curx + 1][cury] != 2 && map[curx + 1][cury] != 1 && queued.find(std::make_tuple(curx + 1, cury)) == queued.end()) {
        que.push_back(std::make_tuple(curx + 1, cury));
        queued.insert(std::make_tuple(curx + 1, cury));
        came_from[std::make_tuple(curx + 1, cury)] = std::make_tuple(curx, cury);
    }
    // check down
    if (cury + 1 <= 9 && map[curx][cury + 1] != 2 && map[curx][cury + 1] != 1 && queued.find(std::make_tuple(curx, cury + 1)) == queued.end()) {
        que.push_back(std::make_tuple(curx, cury + 1));
        queued.insert(std::make_tuple(curx, cury + 1));
        came_from[std::make_tuple(curx, cury + 1)] = std::make_tuple(curx, cury);
    }
    // check left
    if (curx - 1 >= 0 && map[curx - 1][cury] != 2 && map[curx - 1][cury] != 1 && queued.find(std::make_tuple(curx - 1, cury)) == queued.end()) {
        que.push_back(std::make_tuple(curx - 1, cury));
        queued.insert(std::make_tuple(curx - 1, cury));
        came_from[std::make_tuple(curx - 1, cury)] = std::make_tuple(curx, cury);
    }
    // check up
    if (cury - 1 >= 0 && map[curx][cury - 1] != 2 && map[curx][cury - 1] != 1 && queued.find(std::make_tuple(curx, cury - 1)) == queued.end()) {
        que.push_back(std::make_tuple(curx, cury - 1));
        queued.insert(std::make_tuple(curx, cury - 1));
        came_from[std::make_tuple(curx, cury - 1)] = std::make_tuple(curx, cury);
    }
}

int main() {
    bool target_found = false;

    while (map[curx][cury] != 3) {
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 10; j++) {
                std::cout << map[i][j] << " ";
            }
            std::cout << "\n";
        }
        std::cout << "\n";

        // std::this_thread::sleep_for(std::chrono::milliseconds(100)); 

        if (map[curx][cury] == 0) {
            map[curx][cury] = 1;
        }

        check_neihbors();

        idx++;

        if (idx >= que.size()) {
            std::cout << "Queue empty: No path found!\n";
            break;
        }

        curx = std::get<0>(que[idx]);
        cury = std::get<1>(que[idx]);

        if (map[curx][cury] == 3) {
            target_found = true;
        }
    }
    
    // PATH RECONSTRUCTION 
    if (target_found) {
        std::cout << "Target Found! Reconstructing path...\n\n";
        std::vector<std::tuple<int, int>> path;
        std::tuple<int, int> current = std::make_tuple(curx, cury);
        std::tuple<int, int> start_marker = std::make_tuple(-1, -1);

        // Loop backwards through the dictionary until we hit (-1, -1) (the start)
        while (current != start_marker) {
            path.push_back(current);
            current = came_from[current];
        }

        // Reverse the list so it goes from Start -> End
        std::reverse(path.begin(), path.end());

        std::cout << "Final Path Coordinates:\n";
        for (auto step : path) {
            map[std::get<0>(step)][std::get<1>(step)] = 4;
            std::cout << "(" << std::get<0>(step) << ", " << std::get<1>(step) << ")\n";
        }
        
        std::cout << "\nFinal Map:\n";
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 10; j++) {
                std::cout << map[i][j] << " ";
            }
            std::cout << "\n";
        }
    }

    return 0;
}