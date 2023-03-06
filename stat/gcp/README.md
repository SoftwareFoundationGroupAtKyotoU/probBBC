# GCPの実験データファイル

## ベースライン手法(Aichernig'19)
実験のログファイル一覧 (20回の実行ログが連結されている)

- first_800_rounds.txt
- mqtt11_700_rounds.txt
- mqtt14_700_rounds.txt
- mqtt17_700_rounds.txt
- mqtt5_700_rounds.txt
- mqtt8_700_rounds.txt
- sc14_1000_rounds.txt
- sc20_1000_rounds.txt
- second_800_rounds.txt
- slot11_2500_rounds.txt
- slot14_2500_rounds.txt
- slot17_2500_rounds.txt
- slot5_2500_rounds.txt
- slot8_2500_rounds.txt
- slot_v2_11_2500_rounds.txt
- slot_v2_14_2500_rounds.txt
- slot_v2_17_2500_rounds.txt
- slot_v2_5_2500_rounds.txt
- slot_v2_8_2500_rounds.txt
- tcp11_400_rounds.txt
- tcp14_400_rounds.txt
- tcp17_400_rounds.txt
- tcp5_400_rounds.txt
- tcp8_400_rounds.txt
命名規則は
`(ベンチマークの名前)(仕様のステップ数)_(学習のラウンド数)_rounds.txt`

例: `mqtt17_700_rounds.txt` → MQTTのベンチマークモデルとステップ数17の仕様に対して、ベースライン手法を学習のラウンド数700回で実行


## ProbBBCの実験結果のCSV

各列の値の意味は次の通り

```
実験回数と学習のラウンド数  そのラウンドでの戦略を用いたときの確率値  実験回数と学習のラウンド数(1列目と同じ) システム(SUT)の実行トレース数 システムの実行ステップ数
```

実験のログファイル一覧 (50回の実験データが連結されている)
- stat_first10_20221220.txt
- stat_mqtt11_20221220.txt
- stat_mqtt14_20221220.txt
- stat_mqtt17_20221220.txt
- stat_mqtt5_20221220.txt
- stat_mqtt8_20221220.txt
- stat_sc14_20221220.txt
- stat_sc20_20221220.txt
- stat_second13_20221220.txt
- stat_slot11_20221224.txt
- stat_slot14_20221224.txt
- stat_slot17_20221224.txt
- stat_slot5_20221223.txt
- stat_slot8_20221224.txt
- stat_slot_v2-11_20221220.txt
- stat_slot_v2-14_20221220.txt
- stat_slot_v2-17_20221220.txt
- stat_slot_v2-5_20221220.txt
- stat_slot_v2-8_20221220.txt
- stat_tcp11_20221220.txt
- stat_tcp14_20221220.txt
- stat_tcp17_20221220.txt
- stat_tcp5_20221220.txt
- stat_tcp8_20221220.txt

命名規則は
`stat_(ベンチマークの名前)(仕様のステップ数)_(実験日時).txt`

例: `stat_slot14_20221224.txt` → Slot machineのベンチマークモデルとステップ数14の仕様に対して、ProbBBCを実行

## ProbBBCの実験結果の中間ファイル
`stat_(ベンチマーク, 実験日時)_eval.txt`は学習の各ラウンドでの戦略を用いた時の確率値のデータ
`stat_(ベンチマーク, 実験日時)_step.txt`は学習の各ラウンド時点でのシステムの実行トレース数と実行ステップ数のデータ

ファイル一覧
- stat_first10_20221220_eval.txt
- stat_first10_20221220_step.txt
- stat_mqtt11_20221220_eval.txt
- stat_mqtt11_20221220_step.txt
- stat_mqtt14_20221220_eval.txt
- stat_mqtt14_20221220_step.txt
- stat_mqtt17_20221220_eval.txt
- stat_mqtt17_20221220_step.txt
- stat_mqtt5_20221220_eval.txt
- stat_mqtt5_20221220_step.txt
- stat_mqtt8_20221220_eval.txt
- stat_mqtt8_20221220_step.txt
- stat_sc14_20221220_eval.txt
- stat_sc14_20221220_step.txt
- stat_sc20_20221220_eval.txt
- stat_sc20_20221220_step.txt
- stat_second13_20221220_eval.txt
- stat_second13_20221220_step.txt
- stat_slot11_20221224_eval.txt
- stat_slot11_20221224_step.txt
- stat_slot14_20221224_eval.txt
- stat_slot14_20221224_step.txt
- stat_slot17_20221224_eval.txt
- stat_slot17_20221224_step.txt
- stat_slot5_20221223_eval.txt
- stat_slot5_20221223_step.txt
- stat_slot8_20221224_eval.txt
- stat_slot8_20221224_step.txt
- stat_slot_v2-11_20221220_eval.txt
- stat_slot_v2-11_20221220_step.txt
- stat_slot_v2-14_20221220_eval.txt
- stat_slot_v2-14_20221220_step.txt
- stat_slot_v2-17_20221220_eval.txt
- stat_slot_v2-17_20221220_step.txt
- stat_slot_v2-5_20221220_eval.txt
- stat_slot_v2-5_20221220_step.txt
- stat_slot_v2-8_20221220_eval.txt
- stat_slot_v2-8_20221220_step.txt
- stat_tcp11_20221220_eval.txt
- stat_tcp11_20221220_step.txt
- stat_tcp14_20221220_eval.txt
- stat_tcp14_20221220_step.txt
- stat_tcp17_20221220_eval.txt
- stat_tcp17_20221220_step.txt
- stat_tcp5_20221220_eval.txt
- stat_tcp5_20221220_step.txt
- stat_tcp8_20221220_eval.txt
- stat_tcp8_20221220_step.txt
