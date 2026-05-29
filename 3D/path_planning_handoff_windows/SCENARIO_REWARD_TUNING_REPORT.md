# 多场景验证与 Reward 调参报告

本文档记录“扩大验证场景”和“调 reward 权重”两项工作的当前结果。

## 1. 多场景验证

配置文件：

```text
configs/validation_scenarios.yaml
```

运行命令：

```bash
python examples/run_batch_experiments.py --suite configs/validation_scenarios.yaml
```

输出目录：

```text
outputs/validation_scenarios/
```

当前验证集覆盖：

```text
default_t0_h10_3u5tasks
midday_t12_h10_3u5tasks
default_t0_h100_3u5tasks
evening_t18_h100_3u5tasks
generated_t0_h10_4u8tasks
generated_t12_h100_4u8tasks
```

覆盖维度：

```text
time_index: 0 / 12 / 18
height_m: 10 / 100
uav_count: 3 / 4
task_count: 5 / 8
task source: CSV 固定任务 / 气象网格生成任务
```

关键输出：

```text
outputs/validation_scenarios/batch_summary.md
outputs/validation_scenarios/batch_summary.csv
outputs/validation_scenarios/batch_metrics_long.csv
```

## 2. 多场景验证结论

在 6 个验证场景中：

```text
one_shot 只能完成 3/5 或 4/8 个任务
sequential / weather_grid / marl_greedy 均能完成全部任务
```

`weather_grid` baseline 在路径代价上仍然是强基线，尤其在生成任务场景中明显优于 greedy：

```text
generated_t0_h10_4u8tasks:
weather_grid total_path_cost = 7782.0996
marl_greedy total_path_cost = 14091.0338

generated_t12_h100_4u8tasks:
weather_grid total_path_cost = 9192.2378
marl_greedy total_path_cost = 14217.0254
```

这说明后续 MAPPO 不能只在默认 5 任务场景上优化，必须在多任务生成场景中验证泛化能力。

## 3. Reward 权重配置化

现在 MARL / MAPPO 环境已经支持从配置读取 reward 权重：

```yaml
marl:
  reward:
    task_complete_reward: 100.0
    distance_weight: 10.0
    weather_weight: 20.0
    energy_weight: 5.0
    risk_weight: 1.0
    max_distance_km: 1500.0
```

相关代码：

```text
src/marl/env.py
src/marl/scenario_env.py
src/marl/reward.py
```

测试覆盖：

```text
tests/test_reward_config.py
```

## 4. Reward Sweep

配置文件：

```text
configs/mappo_reward_sweep.yaml
```

运行命令：

```bash
python examples/run_mappo_experiments.py --suite configs/mappo_reward_sweep.yaml
```

输出目录：

```text
outputs/mappo_reward_sweep/
```

当前 sweep 组：

```text
balanced_e20
path_focused_e20
weather_focused_e20
cost_focused_e20
```

跨 reward 配置比较时，`total_reward` 不可直接比较，因此该 suite 使用：

```yaml
selection_mode: path_cost
```

即优先按任务完成数，再按路径代价选择最佳实验。

## 5. Reward Sweep 当前结论

20 episode reward sweep 的结果显示：

```text
balanced_e20       total_path_cost = 7038.4607
path_focused_e20   total_path_cost = 7038.4607
weather_focused_e20 total_path_cost = 7038.4607
cost_focused_e20   total_path_cost = 7038.4607
```

同时 reward 数值明显不同：

```text
balanced_e20 mean_total_reward = 415.5912
path_focused_e20 mean_total_reward = 365.1560
weather_focused_e20 mean_total_reward = 353.3596
cost_focused_e20 mean_total_reward = 252.9244
```

结论：

```text
reward 权重已经生效，但 20 episode 训练还不足以让策略产生明显分叉。
```

这意味着下一轮调参不应该只改权重，还要同时增加训练长度或扩大场景。

## 6. 下一轮建议

优先做以下实验：

```text
1. 在 mappo_reward_sweep 基础上把 episodes 提高到 50 或 100。
2. 使用 validation_scenarios 中的生成任务场景做验证，而不是只看默认 5 任务场景。
3. 将模型选择指标改为多场景平均 path cost，而不是单场景 path cost。
4. 单独增加 path_cost 归一化项，让 reward 与最终 total_path_cost 更一致。
```

当前阶段结论：

```text
第一步“扩大验证场景”已完成。
第二步“reward 权重配置化与初步 sweep”已完成。
下一步应进入“多场景 MAPPO 训练/验证集选模”。
```
