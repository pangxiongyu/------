# 项目开发运行手册

本文档给后续编写程序和协作使用。完整任务拆解见 `MARL_MPC_TASK_GUIDE.md`，这里专注于怎么搭环境、怎么跑代码、怎么改任务场景。

## 1. 环境

推荐使用已有的 conda 环境：

```bash
conda activate torch_env
```

检查关键依赖：

```bash
python --version
python -c "import pandas, numpy, torch, yaml; print('ok'); print(torch.cuda.is_available())"
```

如果队友需要从零创建环境，使用：

```bash
conda env create -f environment.yml
conda activate torch_env
```

如果环境已存在但需要同步依赖：

```bash
conda env update -f environment.yml --prune
```

## 2. 场景配置

默认配置文件：

```text
configs/default.yaml
```

默认任务文件：

```text
data/tasks/demo_tasks.csv
```

任务 CSV 字段：

```text
task_id,target_lat,target_lon,target_height_m,payload_g,deadline_s,priority
```

新增真实任务点时，优先复制 `data/tasks/demo_tasks.csv` 为新文件，例如：

```text
data/tasks/experiment_tasks.csv
```

然后在 `configs/default.yaml` 或新的配置文件里修改：

```yaml
paths:
  tasks: data/tasks/experiment_tasks.csv
```

## 3. 常用运行命令

读取原始交接数据示例：

```bash
python examples/read_handoff_data.py
```

运行规则 baseline：

```bash
python examples/run_baseline.py
```

运行简化 MARL 环境的贪心策略：

```bash
python examples/run_marl_eval.py
```

运行 MAPPO 原型训练：

```bash
python examples/run_mappo_train.py --episodes 10 --ppo-epochs 2 --output-dir outputs/mappo_train
```

当前 MAPPO 原型默认启用 `use_weather_grid_paths`，reward 会先调用气象网格路径搜索，再根据路径距离、平均气象代价和无人机画像风险计算。

训练器默认使用 `reward_scale=0.01` 和 value target 标准化来稳定 Critic。`training_history.csv` 会同时保存原始 `episode_reward` 和学习用的 `scaled_episode_reward`，并导出 `return_mean` / `return_std` 用于检查数值尺度。

如果需要显式设置：

```bash
python examples/run_mappo_train.py --episodes 10 --ppo-epochs 2 --reward-scale 0.01 --output-dir outputs/mappo_train
```

MARL 动作格式已经扩展为：

```text
任务@高度#路径策略
```

示例：

```text
T1@10m#direct
T1@100m#weather_grid
T1@100m#weather_3d
```

其中 `direct` 表示直线航段评估，`weather_grid` 表示固定高度层气象网格路径搜索，`weather_3d` 表示允许跨高度层的三维气象路径搜索。

MAPPO 训练会导出：

```text
outputs/mappo_train/mappo_checkpoint.pt
outputs/mappo_train/training_history.csv
outputs/mappo_train/training_curves.png
outputs/mappo_train/policy_eval.csv
```

加载并评估已保存策略：

```bash
python examples/evaluate_mappo_policy.py --checkpoint outputs/mappo_train/mappo_checkpoint.pt --episodes 5
```

运行 Robust MPC 轨迹跟踪原型：

```bash
python examples/run_mpc_tracking.py
```

运行气象网格路径搜索示例：

```bash
python examples/run_weather_grid_path.py
```

运行三维多高度层气象路径搜索示例：

```bash
python examples/run_weather_3d_path.py
```

运行基于场景分配结果的 MPC 跟踪：

```bash
python examples/run_mpc_from_scenario.py
```

运行 QP 约束版 Robust MPC 示例：

```bash
python examples/run_qp_mpc_tracking.py
```

`configs/default.yaml` 中可以切换 MPC 控制器：

```yaml
mpc:
  controller: qp        # qp 或 prototype
  horizon: 6
  max_acc: 3.0
  max_speed: 20.0
```

运行完整配置场景，并对比 baseline 与 MARL 贪心结果：

```bash
python examples/run_scenario.py --config configs/default.yaml
```

运行批量实验和消融对比：

```bash
python examples/run_batch_experiments.py --suite configs/experiments.yaml
```

批量实验配置：

```text
configs/experiments.yaml
```

批量实验输出：

```text
outputs/batch_experiments/batch_metrics_long.csv
outputs/batch_experiments/<experiment_name>/metrics.csv
outputs/batch_experiments/<experiment_name>/assignments.csv
```

导出场景指标和分配结果：

```bash
python examples/run_scenario.py --config configs/default.yaml --output-dir outputs/default_scenario
```

输出文件：

```text
outputs/default_scenario/metrics.csv
outputs/default_scenario/assignments.csv
outputs/default_scenario/weather_layer.png
outputs/default_scenario/routes_one_shot.png
outputs/default_scenario/routes_sequential.png
outputs/default_scenario/routes_weather_grid.png
```

运行测试：

```bash
python -m pytest -q
```

如果 pytest 缓存目录权限异常，但测试通过，可以临时关闭缓存：

```bash
python -m pytest -q -p no:cacheprovider
```

## 4. 当前模块分工建议

建议两人按目录分工，避免互相覆盖。

同学 A：

```text
src/data_io/
src/core/
src/baseline/
examples/run_scenario.py
```

同学 B：

```text
src/marl/
src/mpc/
src/eval/
src/viz/
```

公共数据结构集中在：

```text
src/core/schemas.py
```

如果要改公共字段，先和队友确认，否则容易导致 baseline、MARL、MPC 接口同时失效。

## 5. Git 协作建议

如果还没有 Git 仓库，在项目根目录初始化：

```bash
git init
git add .gitignore environment.yml MARL_MPC_TASK_GUIDE.md DEVELOPMENT_RUNBOOK.md configs src examples tests data/tasks
git commit -m "Initialize UAV MARL MPC planning scaffold"
```

建议分支：

```bash
git checkout -b feature/data-baseline
git checkout -b feature/marl-mpc
```

不要把大文件随意提交到普通 Git：

```text
data/weather_cost_map/weather_cost_map_prototype.csv
data/uav_profiles/torch_mamba_uav_profile_model.pt
UAV_datas/
```

这些后续应该用 Git LFS、DVC、网盘或共享盘管理。

## 6. 下一步开发重点

短期优先级：

```text
1. 用真实任务点替换 demo_tasks.csv。
2. 调整 configs/default.yaml 中的 UAV 数量和场景时间。
3. 将 weather-grid 路径搜索接入 MARL 的 step 评估，让 MARL 的 reward 使用真实路径代价。
4. 扩展 MARL action，从“任务 + 高度层”升级为“任务 + 高度层 + 航点策略”。
5. 将 Robust MPC 从比例型控制原型升级为 cvxpy/osqp 的约束 QP 控制器。
6. 增加多场景批量实验和消融实验。
```
