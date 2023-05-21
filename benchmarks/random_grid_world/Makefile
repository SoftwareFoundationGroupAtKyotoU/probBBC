NUM := $(shell seq 1 20)
SIZES := 4x4 6x6 8x8 10x10 12x12 14x14 16x16 18x18 20x20 22x22 24x24 26x26 28x28 30x30
PRISM := ~/prism-4.7-osx64/bin/prism

all: $(foreach size,$(SIZES),$(foreach num,$(NUM),$(size)/grid_world-$(size)-$(num).dot $(size)/grid_world-$(size)-$(num).prism))


# Pattern rule for generating prism files
# It uses grid_world.py script, so this is a prerequisite
# It runs the grid_world.py with appropriate --x_size, --y_size
%.prism: ./grid_world/grid_world.py
	mkdir -p $(dir $@)
	python3 $< --x_size $(word 1, $(subst x, ,$(dir $*))) --y_size $(word 2, $(subst /, ,$(subst x, ,$(dir $*)))) > $@
	@if [ "$$($(PRISM) $@ ./grid_world-25.props | awk '/Result:/{print int($$2 * 2)}')" -lt 1 ]; then \
		rm $@; \
	elif [ "$$($(PRISM) $@ ./hole_reachable.props | awk '/Result:/{print $$2}')" != true ]; then \
		rm $@; \
	fi

%.lab: %.prism
	$(PRISM) $< -exportlabels $@

# Pattern rule for generating sta files
%.sta: %.prism
	$(PRISM) $< -exportstates $@

# Pattern rule for generating tra files
%.tra: %.prism
	$(PRISM) $< -exporttrans $@

%.dot: ../../src/prism_export_to_dot_model.py %.prism %.lab %.sta %.tra
	python3 $< $(basename $@)

clean:
	$(RM) */*.dot */*.prism */*.lab */*.sta */*.tra

.PHONY: all clean
