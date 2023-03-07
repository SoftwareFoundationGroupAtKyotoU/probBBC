ePMC := ~/ePMC/epmc-standard.jar
JANI := first_grid/first.jani second_grid/second.jani  slot_r5/slot_machine_r5.jani mqtt/emqtt_two_client.jani  shared_coin/coin2.jani   slot_r5_v2/slot_machine_reduce_v2.jani

all: $(JANI)

%.jani: %.prism $(ePMC) $(wildcard $(dir $<)/*.props)
	java -jar $(ePMC) jani-export --model-input-files $< --property-input-files $(wildcard $(dir $<)/*.props) --jani-exporter-jani-file-name $@

$(dir $(ePMC)):
	cd $(shell dirname $@) && git clone https://github.com/iscas-tis/ePMC.git

$(ePMC): $(dir $(ePMC))
	cd $(shell dirname $@) && ./build.sh

clean:
	$(RM) $(JANI)

.PHONY: all clean
