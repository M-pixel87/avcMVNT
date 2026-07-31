#include <iostream>
#include <vector>
#include <tuple>
#include <set>
#include <thread>
#include <chrono>

int curx = 0;
int cury = 0;
size_t idx = 0;

std::vector<std::tuple<int, int>> que = {std::make_tuple(curx, cury)};
std::set<std::tuple<int, int>> queued = {std::make_tuple(curx, cury)};

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
    }
    // check down
    if (cury + 1 <= 9 && map[curx][cury + 1] != 2 && map[curx][cury + 1] != 1 && queued.find(std::make_tuple(curx, cury + 1)) == queued.end()) {
        que.push_back(std::make_tuple(curx, cury + 1));
        queued.insert(std::make_tuple(curx, cury + 1));
    }
    // check left
    if (curx - 1 >= 0 && map[curx - 1][cury] != 2 && map[curx - 1][cury] != 1 && queued.find(std::make_tuple(curx - 1, cury)) == queued.end()) {
        que.push_back(std::make_tuple(curx - 1, cury));
        queued.insert(std::make_tuple(curx - 1, cury));
    }
    // check up
    if (cury - 1 >= 0 && map[curx][cury - 1] != 2 && map[curx][cury - 1] != 1 && queued.find(std::make_tuple(curx, cury - 1)) == queued.end()) {
        que.push_back(std::make_tuple(curx, cury - 1));
        queued.insert(std::make_tuple(curx, cury - 1));
    }
}

int main() {
    while (map[curx][cury] != 3) {
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 10; j++) {
                std::cout << map[i][j] << " ";
            }
            std::cout << "\n";
        }
        std::cout << "\n";

        std::this_thread::sleep_for(std::chrono::milliseconds(100));

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
    }
    
    return 0;
}