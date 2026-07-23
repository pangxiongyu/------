const agricultureapps = [{
  id: 0,
  name: '作物生长监测',
  icon: '🌱',
  description: '利用无人机多光谱相机采集作物冠层影像，通过 NDVI、EVI 等植被指数实时评估作物生长状况与营养水平。',
  features: ['多光谱影像自动拼接与几何校正', '植被指数（NDVI/EVI/SAVI）实时计算', '生长异常区域智能检测与标记', '时序对比分析追踪作物生长趋势'],
  image: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=800&q=80'
}, {
  id: 1,
  name: '病虫害监测预警',
  icon: '🐛',
  description: '基于深度学习的病虫害自动识别系统，融合高光谱成像与气象数据实现精准预警与分级防控建议。',
  features: ['YOLO/Transformer 双模病虫害检测', '病斑面积自动量化与严重度分级', '气象耦合的虫害爆发概率预测', '靶向施药处方图自动生成'],
  image: 'https://images.unsplash.com/photo-1598987963696-b121c9b76e74?w=800&q=80'
}, {
  id: 2,
  name: '精准施肥喷药',
  icon: '💊',
  description: '变量喷洒控制系统，结合处方图实现按需施肥与靶向喷药，减少化学品用量同时提升作业效率。',
  features: ['基于处方图的变量喷洒控制', 'RTK 厘米级定位确保作业精度', '流量自动调节与断点续喷', '作业质量实时评估与回溯报告'],
  image: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=800&q=80'
}, {
  id: 3,
  name: '产量预测',
  icon: '📊',
  description: '融合无人机遥感数据与气象土壤信息，利用机器学习模型预测作物产量，辅助精准农业管理决策。',
  features: ['多源数据融合的产量预测模型', 'LSTM/Transformer 时序预测', '地块级产量空间分布制图', '不确定性量化与置信区间估计'],
  image: 'https://images.unsplash.com/photo-1592983867441-8588844e29f1?w=800&q=80'
}, {
  id: 4,
  name: '杂草分布识别',
  icon: '🌿',
  description: '高分辨率 RGB 和多光谱图像中的杂草自动识别与分类，生成杂草分布密度图辅助精准除草作业。',
  features: ['语义分割模型区分作物与杂草', '杂草种类自动分类（禾本/阔叶等）', '杂草密度热力图生成', '除草优先级排序与路径规划'],
  image: 'https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=800&q=80'
}, {
  id: 5,
  name: '土壤墒情监测',
  icon: '💧',
  description: '利用热红外与微波遥感反演土壤水分含量，实现大范围土壤墒情空间分布制图与旱情预警。',
  features: ['热红外-微波协同土壤水分反演', '高分辨率墒情空间分布图', '灌溉需求分区与建议', '旱情趋势监测与预警'],
  image: 'https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=800&q=80'
}, {
  id: 6,
  name: '农田生态感知',
  icon: '🌍',
  description: '综合评估农田生态系统健康状况，监测生物多样性、碳汇量、水体质量等多维度生态指标。',
  features: ['植被覆盖度与生物量估算', '农田碳汇遥感定量评估', '水体富营养化遥感监测', '生态红线区变化检测'],
  image: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80'
}, {
  id: 7,
  name: '灾害损失评估',
  icon: '⚠️',
  description: '灾后快速遥感评估系统，自动对比灾前灾后影像量化受灾面积与损失程度，支持保险理赔决策。',
  features: ['灾前灾后影像自动配准对比', '受灾面积与程度自动量化', '多灾种（洪涝/冰雹/倒伏）识别', '损失评估报告自动生成'],
  image: 'https://images.unsplash.com/photo-1472141521881-95d0e87e2e39?w=800&q=80'
}];
export { agricultureapps };
