# plot_graph.pyの使い方
# 第1引数: ProbBBCのデータ, 第2引数: prob-black-reachのデータ, 第3引数: 出力のPDFファイル名
# 第4引数: 真の確率値, 第5引数: 散布図を生成する時の横軸(実行ステップ数)の上限
# 第6引数: 箱髭図を生成するときの実行ステップ数(指定された実行ステップ数付近の60個のデータから箱髭図を作成する)

# # first10
# python3 plot_graph.py ../gcp/stat_first10_20221220.txt ../gcp/stat_first_800_rounds.txt fig_first10.pdf 0.61809 4750000 4600000
# second13
# python3 plot_graph.py ../gcp/stat_second13_20221220.txt ../gcp/stat_second_800_rounds.txt fig_second13.pdf 0.67119477 6000000 5800000

# # mqtt5
# echo 'mqtt5'
# python3 plot_graph.py ../gcp/stat_mqtt5_20221220.txt ../gcp/stat_mqtt5_700_rounds.txt fig_mqtt5.pdf 0.3439 3100000
# # mqtt8
# echo 'mqtt8'
# python3 plot_graph.py ../gcp/stat_mqtt8_20221220.txt ../gcp/stat_mqtt8_700_rounds.txt fig_mqtt8.pdf 0.5217 3300000 3150000
# # mqtt11
# echo 'mqtt11'
# python3 plot_graph.py ../gcp/stat_mqtt11_20221220.txt ../gcp/stat_mqtt11_700_rounds.txt fig_mqtt11.pdf 0.6513 3500000
# # mqtt14
# echo 'mqtt14'
# python3 plot_graph.py ../gcp/stat_mqtt14_20221220.txt ../gcp/stat_mqtt14_700_rounds.txt fig_mqtt14.pdf 0.7458 3700000 3550000
# # mqtt17
# echo 'mqtt17'
# python3 plot_graph.py ../gcp/stat_mqtt17_20221220.txt ../gcp/stat_mqtt17_700_rounds.txt fig_mqtt17.pdf 0.8146 3900000

# # sc14
# echo 'sc14'
# python3 plot_graph.py ../gcp/stat_sc14_20221220.txt ../gcp/stat_sc14_1000_rounds.txt fig_sc14.pdf 0.125 12000000 11500000
# # sc20
# echo 'sc20'
# python3 plot_graph.py ../gcp/stat_sc20_20221220.txt ../gcp/stat_sc20_1000_rounds.txt fig_sc20.pdf 0.25 12000000 11500000

# # slot_v2_5
# echo 'slot_v2_5'
# python plot_graph.py ../gcp/stat_slot_v2-5_20221220.txt ../gcp/stat_slot_v2_5_2500_rounds.txt fig_slot_v2_5.pdf 0.1 9000000 # todo : incorrect true value
# # slot_v2_8
# echo 'slot_v2_8'
# python plot_graph.py ../gcp/stat_slot_v2-8_20221220.txt ../gcp/stat_slot_v2_8_2500_rounds.txt fig_slot_v2_8.pdf 0.33216 13000000 12000000
# # slot_v2_11
# echo 'slot_v2_11'
# python plot_graph.py ../gcp/stat_slot_v2-11_20221220.txt ../gcp/stat_slot_v2_11_2500_rounds.txt fig_slot_v2_11.pdf 0.4 15000000 # todo : incorrect true value
# slot_v2_14
# echo 'slot_v2_14'
# python plot_graph.py ../gcp/stat_slot_v2-14_20221220.txt ../gcp/stat_slot_v2_14_2500_rounds.txt fig_slot_v2_14.pdf 0.4989 17000000 16000000
# # slot_v2_17
# echo 'slot_v2_17'
# python plot_graph.py ../gcp/stat_slot_v2-17_20221220.txt ../gcp/stat_slot_v2_17_2500_rounds.txt fig_slot_v2_17.pdf 0.5 18000000 # todo : incorrect true value

# # slot5
# echo 'slot5'
# python plot_graph.py ../gcp/stat_slot5_20221223.txt ../gcp/stat_slot5_2500_rounds.txt fig_slot5.pdf 0.1 17000000 # todo : incorrect true value
# # slot8
# echo 'slot8'
# python plot_graph.py ../gcp/stat_slot8_20221224.txt ../gcp/stat_slot8_2500_rounds.txt fig_slot8.pdf 0.33216 17000000 15000000
# # slot11
# echo 'slot11'
# python plot_graph.py ../gcp/stat_slot11_20221224.txt ../gcp/stat_slot11_2500_rounds.txt fig_slot11.pdf 0.4 17000000 # todo : incorrect true value
# # slot14
# echo 'slot14'
# python plot_graph.py ../gcp/stat_slot14_20221224.txt ../gcp/stat_slot14_2500_rounds.txt fig_slot14.pdf 0.4989 17000000 15000000
# # slot17
# echo 'slot17'
# python plot_graph.py ../gcp/stat_slot17_20221224.txt ../gcp/stat_slot17_2500_rounds.txt fig_slot17.pdf 0.5 17000000 # todo : incorrect true value

# # tcp5
# echo 'tcp5'
# python plot_graph.py ../gcp/stat_tcp5_20221220.txt ../gcp/stat_tcp5_400_rounds.txt fig_tcp5.pdf 0.19 4500000 4300000
# # tcp8
# echo 'tcp8'
# python plot_graph.py ../gcp/stat_tcp8_20221220.txt ../gcp/stat_tcp8_400_rounds.txt fig_tcp8.pdf 0.4095 4700000 4500000
# # tcp11
# echo 'tcp11'
# python plot_graph.py ../gcp/stat_tcp11_20221220.txt ../gcp/stat_tcp11_400_rounds.txt fig_tcp11.pdf 0.56953 5000000 4800000
# # tcp14
# echo 'tcp14'
# python plot_graph.py ../gcp/stat_tcp14_20221220.txt ../gcp/stat_tcp14_400_rounds.txt fig_tcp14.pdf 0.68618 5300000 5000000
# # tcp17
# echo 'tcp17'
# python plot_graph.py ../gcp/stat_tcp17_20221220.txt ../gcp/stat_tcp17_400_rounds.txt fig_tcp17.pdf 0.77123 5600000 5300000
