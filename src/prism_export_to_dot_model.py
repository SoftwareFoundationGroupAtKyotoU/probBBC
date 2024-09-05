import sys
import re

except_names = ["init", "notEnd"]


def main():
    if len(sys.argv) < 1:
        print("need to set path to prism export files")

    file_path = sys.argv[1]

    states = {}
    states_regex = re.compile("(\d+):(.*)")
    with open(file_path + ".sta", "r") as f_states:
        for line in f_states:
            m = states_regex.match(line)
            if m:
                states[m[1]] = m[2].strip()

    transitions = []
    trans_regex = re.compile("(\d+) (\d+) (\d+) (\d+\.?\d*) (.*)")
    with open(file_path + ".tra", "r") as f_trans:
        for line in f_trans:
            m = trans_regex.match(line)
            if m:
                transitions.append((m[1], m[2], m[3], m[4], m[5]))

    labels = {}
    name_of_labels = {}
    initial_state = None
    label_name_line_regex = re.compile('(\d+="\w+" )*(\d+="\w+")')
    label_name_regex = re.compile('(\d+)="(\w+)"')
    label_regex = re.compile("(\d+): (.*)")
    label_index_regex = re.compile("\d+")
    with open(file_path + ".lab", "r") as f_labels:
        for line in f_labels:
            m = label_name_line_regex.match(line)
            if m:
                m_names = label_name_regex.findall(line)
                for index, name in m_names:
                    name_of_labels[index] = name
            else:
                m = label_regex.match(line)
                if m:
                    m_index = label_index_regex.findall(m[2])
                    label_names = []
                    for idx in m_index:
                        name = name_of_labels[idx]
                        if name == "init":
                            initial_state = m[1]
                        if not name in except_names:
                            label_names.append(name)
                    labels[m[1]] = "__".join(label_names)

    # if initial_state:
    #     print(initial_state)
    #     print(labels)
    #     print(transitions)
    with open(file_path + ".dot", "w+") as f:
        f.write("digraph g {\n")
        f.write('__start0 [label="" shape="none"];\n')
        for state_index in states:
            f.write(state_index)
            f.write(' [shape="circle" label="' + labels[state_index] + '"];\n')
        for current_sta, _, next_sta, probability, action in transitions:
            f.write(
                current_sta
                + " -> "
                + next_sta
                + ' [label="'
                + action
                + ":"
                + probability
                + '"];\n'
            )
        f.write("__start0 -> 0;\n")
        f.write("}\n")


if __name__ == "__main__":
    main()
