import re

step_bound = 40

module_regex = re.compile(r"module (\w+)")
label_regex = re.compile(r"(\d+\.*\d* : \([\w\d'=]+\))")

def add_step_counter_to_prism_model(prism_model_path, output_file_path):
    with open(prism_model_path) as f:
        with open(output_file_path, mode='w') as o:
            for line in f:
                module_match = module_regex.match(line)
                if module_match:
                    modified_line = module_regex.sub(r"module \1\nsteps : [0..40] init 0;", line)
                    o.write(modified_line)
                else:
                    modified_line = label_regex.sub(r"\1&(steps'=min(40,steps + 1))", line)
                    o.write(modified_line)

# prism_model_path = f'/Users/bo40/workspace/python/mc_exp-slot_machine.prism'

# add_step_counter_to_prism_model(prism_model_path, "converted_model.prism")
