from vials import Vial, VialSet, StateGraph

if __name__ == '__main__':
    nc = int(input("Enter a number of colors: "))
    nb = nc + 2
    print("Fill vials, 0 is empty-vial")
    vial_set = VialSet()
    for i in range(nb):
        vial_set.add(Vial(*map(int, input().split())))

    graph = StateGraph(vial_set)
    path = graph.build_graph()
    for op in path:
        print(vial_set.transfer_str(op[0], op[1]))
