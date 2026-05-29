const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

const runtimeRequire = createRequire(
  "C:/Users/sjw/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/pptxgenjs@4.0.1/node_modules/pptxgenjs/"
);
const pptxgen = runtimeRequire("pptxgenjs");

const ROOT = __dirname;
const OUT = path.join(ROOT, "UAV_MARL_MPC_DEFENSE_DECK.pptx");
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "UAV MARL MPC Project";
pptx.subject = "MARL and Robust MPC UAV path planning";
pptx.title = "基于 MARL 与 Robust MPC 的无人机联合路径规划与管控平台";
pptx.company = "Path Planning Handoff";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";

const C = {
  ink: "172033",
  navy: "1D3557",
  teal: "1B998B",
  cyan: "8BD3E6",
  amber: "F2B84B",
  red: "D95D5D",
  cream: "F7F4EA",
  pale: "EEF6F5",
  gray: "667085",
  light: "FFFFFF",
};

function addFooter(slide, n) {
  slide.addText(`UAV MARL + Robust MPC | ${n}`, {
    x: 0.55,
    y: 7.08,
    w: 4.4,
    h: 0.22,
    fontFace: "Microsoft YaHei",
    fontSize: 7.5,
    color: "7A869A",
    margin: 0,
  });
}

function title(slide, text, sub) {
  slide.addText(text, {
    x: 0.55,
    y: 0.34,
    w: 9.4,
    h: 0.45,
    fontFace: "Microsoft YaHei",
    fontSize: 22,
    bold: true,
    color: C.ink,
    margin: 0,
    breakLine: false,
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.56,
      y: 0.86,
      w: 10.8,
      h: 0.28,
      fontFace: "Microsoft YaHei",
      fontSize: 10.5,
      color: C.gray,
      margin: 0,
    });
  }
}

function bullet(slide, items, x, y, w, fontSize = 15, color = C.ink) {
  slide.addText(
    items.map((t) => ({ text: t, options: { bullet: { type: "ul" }, breakLine: true } })),
    {
      x,
      y,
      w,
      h: Math.min(5.8, items.length * 0.42 + 0.2),
      fontFace: "Microsoft YaHei",
      fontSize,
      color,
      margin: 0,
      fit: "shrink",
      breakLine: false,
      paraSpaceAfterPt: 6,
    }
  );
}

function label(slide, text, x, y, w, color = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.34,
    rectRadius: 0.08,
    fill: { color },
    line: { color },
  });
  slide.addText(text, {
    x: x + 0.08,
    y: y + 0.075,
    w: w - 0.16,
    h: 0.16,
    fontFace: "Microsoft YaHei",
    fontSize: 8.5,
    bold: true,
    color: C.light,
    align: "center",
    margin: 0,
    fit: "shrink",
  });
}

function metric(slide, value, caption, x, y, color = C.teal) {
  slide.addText(value, {
    x,
    y,
    w: 1.9,
    h: 0.46,
    fontFace: "Microsoft YaHei",
    fontSize: 25,
    bold: true,
    color,
    margin: 0,
    align: "center",
  });
  slide.addText(caption, {
    x,
    y: y + 0.54,
    w: 1.9,
    h: 0.28,
    fontFace: "Microsoft YaHei",
    fontSize: 9,
    color: C.gray,
    margin: 0,
    align: "center",
    fit: "shrink",
  });
}

function table(slide, rows, x, y, w, rowH = 0.38, headColor = C.navy) {
  const colCount = rows[0].length;
  const colW = w / colCount;
  rows.forEach((row, r) => {
    row.forEach((cell, c) => {
      const fill = r === 0 ? headColor : r % 2 === 0 ? "F7FBFA" : "FFFFFF";
      const color = r === 0 ? C.light : C.ink;
      slide.addShape(pptx.ShapeType.rect, {
        x: x + c * colW,
        y: y + r * rowH,
        w: colW,
        h: rowH,
        fill: { color: fill },
        line: { color: "D9E2E5", transparency: 15 },
      });
      slide.addText(String(cell), {
        x: x + c * colW + 0.04,
        y: y + r * rowH + 0.08,
        w: colW - 0.08,
        h: rowH - 0.12,
        fontFace: "Microsoft YaHei",
        fontSize: r === 0 ? 8.2 : 8.0,
        bold: r === 0,
        color,
        align: c === 0 ? "left" : "center",
        margin: 0,
        fit: "shrink",
      });
    });
  });
}

function addImageIfExists(slide, rel, x, y, w, h) {
  const file = path.join(ROOT, rel);
  if (fs.existsSync(file)) {
    slide.addImage({ path: file, x, y, w, h });
    return true;
  }
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w,
    h,
    fill: { color: C.pale },
    line: { color: "D9E2E5" },
  });
  slide.addText(rel, {
    x: x + 0.15,
    y: y + h / 2 - 0.15,
    w: w - 0.3,
    h: 0.3,
    fontSize: 10,
    color: C.gray,
    align: "center",
    margin: 0,
  });
  return false;
}

function cover() {
  const s = pptx.addSlide();
  s.background = { color: C.cream };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.cream }, line: { transparency: 100 } });
  s.addShape(pptx.ShapeType.arc, { x: 7.6, y: -0.7, w: 5.4, h: 5.4, line: { color: C.teal, transparency: 35, width: 2 }, adjustPoint: 0.25 });
  s.addText("MARL + Robust MPC", { x: 0.7, y: 0.72, w: 3.0, h: 0.28, fontSize: 11, bold: true, color: C.teal, margin: 0 });
  s.addText("基于 MARL 与 Robust MPC 的\n无人机联合路径规划与管控平台", {
    x: 0.7,
    y: 1.55,
    w: 8.3,
    h: 1.35,
    fontFace: "Microsoft YaHei",
    fontSize: 28,
    bold: true,
    color: C.ink,
    margin: 0,
    breakLine: false,
    fit: "shrink",
  });
  s.addText("三维气象地图 × 个体画像 × 多智能体强化学习 × 抗扰动航迹跟踪", {
    x: 0.72,
    y: 3.25,
    w: 8.5,
    h: 0.34,
    fontSize: 14,
    color: C.gray,
    margin: 0,
  });
  metric(s, "37", "单元测试通过", 0.7, 4.75, C.teal);
  metric(s, "0", "MPC 约束违反", 2.85, 4.75, C.amber);
  metric(s, "5/5", "任务完成", 5.0, 4.75, C.navy);
  addImageIfExists(s, "outputs/default_scenario/routes_weather_grid.png", 9.3, 0.9, 3.45, 5.6);
  addFooter(s, 1);
}

function slide2() {
  const s = pptx.addSlide();
  s.background = { color: C.light };
  title(s, "为什么这个问题值得做", "多无人机任务分配不是单纯最短路，而是气象、能力和控制可执行性的联合问题");
  bullet(s, [
    "突变气象会改变路径风险，离线规划响应慢",
    "不同 UAV 的健康状态、载荷能力、风险等级不一致",
    "路径规划结果必须能被底层控制器稳定跟踪",
    "因此需要高层智能分配 + 底层 Robust MPC 闭环评估",
  ], 0.8, 1.55, 5.6, 15);
  addImageIfExists(s, "outputs/default_scenario/weather_layer.png", 7.0, 1.35, 5.4, 4.75);
  label(s, "从“能规划”到“能执行”", 0.8, 6.15, 2.4, C.amber);
  addFooter(s, 2);
}

function slide3() {
  const s = pptx.addSlide();
  title(s, "系统闭环", "数据输入、MAPPO 高层规划、Robust MPC 跟踪和统一 benchmark 已贯通");
  const nodes = [
    ["UAV 个体画像", 0.7, 2.0, C.teal],
    ["三维气象地图", 0.7, 3.25, C.navy],
    ["任务需求", 0.7, 4.5, C.amber],
    ["场景构建", 3.4, 3.25, C.teal],
    ["MAPPO / baseline", 5.8, 3.25, C.navy],
    ["Robust MPC", 8.5, 3.25, C.amber],
    ["统一指标报告", 10.9, 3.25, C.teal],
  ];
  nodes.forEach(([txt, x, y, c]) => {
    s.addShape(pptx.ShapeType.roundRect, { x, y, w: 1.75, h: 0.55, rectRadius: 0.08, fill: { color: c }, line: { color: c } });
    s.addText(txt, { x: x + 0.08, y: y + 0.18, w: 1.59, h: 0.15, fontSize: 8.5, bold: true, color: C.light, align: "center", margin: 0, fit: "shrink" });
  });
  [[2.45, 2.28, 3.4, 3.52], [2.45, 3.52, 3.4, 3.52], [2.45, 4.78, 3.4, 3.52], [5.15, 3.52, 5.8, 3.52], [7.55, 3.52, 8.5, 3.52], [10.25, 3.52, 10.9, 3.52]].forEach(([x1, y1, x2, y2]) => {
    s.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color: "9AA8B5", width: 1.6, beginArrowType: "none", endArrowType: "triangle" } });
  });
  bullet(s, ["核心亮点：把 MPC 跟踪误差也纳入 MAPPO 优化目标", "最终输出不止路径代价，还包含控制能耗和约束违反"], 3.6, 5.55, 6.8, 12.5, C.gray);
  addFooter(s, 3);
}

function slide4() {
  const s = pptx.addSlide();
  title(s, "数据和画像", "MAMBA-Lite 画像、任务点和气象代价地图统一进入场景构建");
  table(s, [
    ["数据", "位置", "作用"],
    ["UAV 画像", "data/uav_profiles", "健康、载荷、风险、能耗"],
    ["任务数据", "data/tasks/demo_tasks.csv", "位置、载荷、优先级"],
    ["气象地图", "data/weather_cost_map", "时间、高度、代价、风场"],
    ["配置文件", "configs/*.yaml", "控制场景与 reward"],
  ], 0.8, 1.5, 11.6, 0.52);
  label(s, "当前 MAMBA-Lite 可用，后续可替换正式 MAMBA", 0.9, 5.05, 4.5, C.teal);
  addFooter(s, 4);
}

function slide5() {
  const s = pptx.addSlide();
  title(s, "Baseline 与 MAPPO 设计", "MAPPO 负责选择任务、路径策略和高度动作");
  bullet(s, ["one_shot：每架 UAV 至多一个任务", "sequential：顺序贪心，可连续执行任务", "weather_grid：气象感知网格路径", "marl_greedy：MARL 环境下的贪心对照"], 0.8, 1.45, 4.5, 13);
  table(s, [
    ["MAPPO 动作", "含义"],
    ["direct", "直接连接起点和任务点"],
    ["weather_grid", "二维气象网格路径"],
    ["weather_3d", "三维气象路径"],
    ["height action", "选择目标高度层"],
  ], 6.3, 1.45, 5.8, 0.52);
  addFooter(s, 5);
}

function slide6() {
  const s = pptx.addSlide();
  title(s, "Reward 从路径代价走向可跟踪性", "先解决数值稳定，再让 MAPPO 关注底层可控性");
  bullet(s, ["value loss 数值过大：引入 reward_scale 与 value target normalization", "path-cost reward：降低真实路径代价带来的 critic 不稳定", "trackability reward：惩罚过长 waypoint 间距", "默认配置保持兼容，新实验单独启用可跟踪性权重"], 0.8, 1.45, 6.3, 14);
  s.addText("trackability_penalty = weight × normalized(max_segment_distance_km)", {
    x: 1.0,
    y: 5.15,
    w: 9.8,
    h: 0.38,
    fontFace: "Consolas",
    fontSize: 15,
    bold: true,
    color: C.navy,
    margin: 0,
  });
  addFooter(s, 6);
}

function slide7() {
  const s = pptx.addSlide();
  title(s, "Path-cost MAPPO：高层规划表现", "完成全部任务，并低于 marl_greedy 路径代价");
  table(s, [
    ["方法", "完成任务", "总路径代价", "总奖励"],
    ["sequential", "5", "5848.3320", "0"],
    ["weather_grid", "5", "5463.6228", "0"],
    ["marl_greedy", "5", "7907.5821", "431.4538"],
    ["path-cost MAPPO", "5", "6738.1788", "425.3553"],
  ], 0.8, 1.45, 7.1, 0.52);
  metric(s, "5/5", "任务完成", 8.6, 1.6, C.teal);
  metric(s, "6738", "MAPPO 路径代价", 10.35, 1.6, C.amber);
  bullet(s, ["结论：MAPPO 已具备完整任务分配能力", "不足：仍未超过 weather_grid 强专家基线"], 8.5, 3.55, 3.5, 12.5, C.gray);
  addFooter(s, 7);
}

function slide8() {
  const s = pptx.addSlide();
  title(s, "MPC 暴露出路径可执行性问题", "路径代价可接受，不代表底层控制可稳定跟踪");
  table(s, [
    ["指标", "path-cost MAPPO"],
    ["direct_action_count", "1"],
    ["mpc_mean_tracking_error", "69.3290"],
    ["mpc_max_tracking_error", "2731.1681"],
    ["mpc_constraint_violation_count", "21"],
  ], 0.9, 1.5, 5.9, 0.56, C.red);
  bullet(s, ["长 direct 航段 waypoint 少，单段距离过大", "MPC 需要更密集、更平滑的中间 waypoint", "这推动我们加入 trackability reward"], 7.4, 1.6, 4.8, 14);
  addFooter(s, 8);
}

function slide9() {
  const s = pptx.addSlide();
  title(s, "Trackability MAPPO：MPC 闭环显著改善", "用最长航段惩罚，引导策略选择 weather-grid / weather-3D");
  table(s, [
    ["指标", "path-cost", "trackability"],
    ["完成任务数", "5", "5"],
    ["direct 动作", "1", "0"],
    ["weather-grid 动作", "0", "2"],
    ["weather-3D 动作", "4", "3"],
    ["MPC 平均误差", "69.3290", "0.1204"],
    ["MPC 约束违反", "21", "0"],
  ], 0.75, 1.35, 7.25, 0.48, C.navy);
  metric(s, "0", "约束违反", 8.65, 1.55, C.teal);
  metric(s, "0.1204", "平均跟踪误差", 10.25, 1.55, C.amber);
  bullet(s, ["代价：路径总代价从 6738 升至 7949", "意义：系统能显式权衡规划效率和底层可控性"], 8.5, 3.7, 3.8, 12);
  addFooter(s, 9);
}

function slide10() {
  const s = pptx.addSlide();
  title(s, "完整 Trackability Sweep", "w25 与 w50 都完成训练，当前按验证集 trackability 选择 w25");
  table(s, [
    ["实验", "完成任务", "路径代价", "peak segment", "grid", "3D"],
    ["w25_e30", "5", "7541.6717", "242.1842", "2", "3"],
    ["w50_e30", "5", "7061.4955", "242.1842", "2", "3"],
  ], 0.8, 1.55, 8.2, 0.58);
  bullet(s, ["w50 在默认场景路径代价更低", "w25 在验证集选择口径下更优", "两者 benchmark 的 MPC 约束违反均为 0"], 9.3, 1.65, 3.0, 12.5);
  addFooter(s, 10);
}

function slide11() {
  const s = pptx.addSlide();
  title(s, "多 seed / 多 episode 稳健性", "3 个 seed × 40 episodes，均能完成 5 个任务");
  table(s, [
    ["实验", "seed", "episode", "完成", "路径代价", "grid", "3D"],
    ["seed7", "7", "40", "5", "6350.1909", "2", "2"],
    ["seed11", "11", "40", "5", "7521.3170", "0", "4"],
    ["seed17", "17", "40", "5", "10874.3804", "1", "3"],
  ], 0.75, 1.45, 8.55, 0.54);
  metric(s, "3/3", "seed 完成任务", 9.75, 1.55, C.teal);
  metric(s, "0", "最优 seed 约束违反", 9.75, 2.55, C.amber);
  bullet(s, ["seed7_e40 是多 seed 最优", "benchmark 平均跟踪误差 0.1533"], 9.55, 4.0, 3.1, 11);
  addFooter(s, 11);
}

function slide12() {
  const s = pptx.addSlide();
  title(s, "核心贡献", "项目从可运行原型推进到了可展示的规划-控制闭环");
  bullet(s, [
    "统一接入 UAV 个体画像、任务数据和三维气象地图",
    "实现 baseline、MARL greedy、MAPPO 的统一对比",
    "将 Robust MPC 指标并入最终 benchmark",
    "提出 trackability reward，显著降低 MPC 跟踪误差",
    "形成完整复现实验命令、交接报告和答辩材料",
  ], 0.9, 1.45, 9.7, 15);
  addFooter(s, 12);
}

function slide13() {
  const s = pptx.addSlide();
  title(s, "局限与下一步", "项目已经可交付，继续提升主要面向论文级实验质量");
  table(s, [
    ["当前局限", "后续方向"],
    ["MAPPO 路径代价仍未超过 weather_grid", "专家模仿学习 / reward shaping"],
    ["trackability 会增加路径代价", "设计路径代价 + 可控性联合目标"],
    ["训练规模仍偏小", "更多 seed、episode、场景规模"],
    ["MAMBA-Lite 非正式版本", "替换正式 MAMBA 画像输出"],
  ], 0.8, 1.45, 11.6, 0.58);
  addFooter(s, 13);
}

function slide14() {
  const s = pptx.addSlide();
  s.background = { color: C.ink };
  s.addText("一句话结论", { x: 0.8, y: 0.78, w: 3.0, h: 0.35, fontSize: 15, bold: true, color: C.amber, margin: 0 });
  s.addText("我们不仅让无人机“规划路径”，\n还让系统判断并优化这条路径\n能否被底层控制器稳定执行。", {
    x: 0.78,
    y: 1.7,
    w: 9.4,
    h: 1.65,
    fontSize: 30,
    bold: true,
    color: C.light,
    margin: 0,
    fit: "shrink",
  });
  s.addText("气象地图 + 个体画像 + MAPPO + Robust MPC，形成完整联合规划与管控闭环。", {
    x: 0.82,
    y: 4.15,
    w: 9.6,
    h: 0.38,
    fontSize: 14,
    color: C.cyan,
    margin: 0,
  });
  label(s, "可运行", 0.85, 5.55, 1.35, C.teal);
  label(s, "可复现", 2.35, 5.55, 1.35, C.amber);
  label(s, "可展示", 3.85, 5.55, 1.35, C.red);
  addFooter(s, 14);
}

[
  cover,
  slide2,
  slide3,
  slide4,
  slide5,
  slide6,
  slide7,
  slide8,
  slide9,
  slide10,
  slide11,
  slide12,
  slide13,
  slide14,
].forEach((fn) => fn());

pptx.writeFile({ fileName: OUT });
