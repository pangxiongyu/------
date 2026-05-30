import { Link } from 'react-router-dom'
import { HiArrowRight, HiPlay, HiShieldCheck, HiLightningBolt, HiCursorClick } from 'react-icons/hi'

export default function HeroBanner() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 hero-gradient" />

      {/* Particle grid overlay */}
      <div className="particle-bg absolute inset-0" />

      {/* Large floating blur orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-white/8 rounded-full blur-[100px] animate-float" />
        <div className="absolute top-1/3 -right-32 w-[400px] h-[400px] bg-agri-300/15 rounded-full blur-[100px] animate-float" style={{ animationDelay: '1.2s' }} />
        <div className="absolute -bottom-20 left-1/4 w-[350px] h-[350px] bg-emerald-200/10 rounded-full blur-[80px] animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/3 w-[600px] h-[600px] bg-agri-100/10 rounded-full blur-[120px] animate-breathe" />
      </div>

      {/* Subtle dot grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,1) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 w-full">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left text */}
          <div>
            {/* Status badge */}
            <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-md rounded-full px-4 py-1.5 mb-8 border border-white/25 shadow-lg">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-300 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-300" />
              </span>
              <span className="text-white/90 text-sm font-semibold tracking-wide">MambaAgriSim v2.0 已发布</span>
              <HiCursorClick className="w-3.5 h-3.5 text-white/60" />
            </div>

            {/* Main title */}
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-black text-white leading-[1.05] mb-6">
              <span className="gradient-text-warm bg-gradient-to-r from-white via-agri-100 to-agri-200 bg-clip-text">
                智慧农业
              </span>
              <br />
              <span className="text-white">
                无人机协同
              </span>
              <span className="relative inline-block ml-2">
                <span className="relative z-10 text-white">系统</span>
                <span className="absolute -bottom-1 left-0 right-0 h-2 bg-agri-400/30 rounded-full -z-0 blur-sm" />
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-white/75 text-lg md:text-xl max-w-xl mb-10 leading-relaxed font-medium">
              基于 <span className="text-white font-semibold">GAT 图注意力网络</span> 与{' '}
              <span className="text-white font-semibold">Mamba-MPSO 优化算法</span> 的三维可视化平台，
              实现多无人机协同路径规划、实时状态监控与智能农业应用集成。
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4 mb-12">
              <Link to="/flight-params" className="btn-glow text-lg px-9 py-4 group">
                <HiPlay className="w-5 h-5 text-agri-500" />
                <span>进入系统</span>
                <HiArrowRight className="w-5 h-5 text-agri-400 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
              <Link to="/scene-detail" className="btn-outline-light group">
                了解更多
                <HiArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>
            </div>

            {/* Feature highlights */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { icon: HiLightningBolt, title: '智能规划', desc: 'Mamba-MPSO 路径优化' },
                { icon: HiShieldCheck, title: '精准作业', desc: '厘米级 RTK 定位' },
                { icon: HiCursorClick, title: '协同控制', desc: '8 机编队协同' },
              ].map((f, i) => (
                <div
                  key={f.title}
                  className="group relative bg-white/8 backdrop-blur-md rounded-2xl p-4 border border-white/15 hover:bg-white/15 transition-all duration-300 hover:scale-[1.03] hover:border-white/25 cursor-default"
                >
                  <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center mb-2.5 group-hover:bg-white/25 transition-colors">
                    <f.icon className="w-4 h-4 text-agri-200" />
                  </div>
                  <div className="text-white font-bold text-sm mb-0.5">{f.title}</div>
                  <div className="text-white/55 text-xs">{f.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right - 3D visualization */}
          <div className="hidden lg:flex items-center justify-center">
            <div className="relative">
              {/* Outer glow ring */}
              <div className="absolute inset-0 rounded-full bg-agri-400/10 blur-3xl animate-breathe" />

              {/* Main orbit container */}
              <div className="relative w-[440px] h-[440px]">
                {/* Orbit rings */}
                <svg className="absolute inset-0 w-full h-full animate-orbit" viewBox="0 0 440 440">
                  <ellipse cx="220" cy="220" rx="190" ry="70" fill="none" stroke="white" strokeWidth="0.6" opacity="0.15" transform="rotate(-18 220 220)" />
                  <ellipse cx="220" cy="220" rx="190" ry="70" fill="none" stroke="white" strokeWidth="0.4" opacity="0.1" transform="rotate(12 220 220)" />
                </svg>
                <svg className="absolute inset-0 w-full h-full animate-orbit-reverse" viewBox="0 0 440 440">
                  <ellipse cx="220" cy="220" rx="160" ry="55" fill="none" stroke="white" strokeWidth="0.5" opacity="0.2" transform="rotate(0 220 220)" />
                  <ellipse cx="220" cy="220" rx="125" ry="42" fill="none" stroke="white" strokeWidth="0.4" opacity="0.12" transform="rotate(45 220 220)" />
                </svg>

                {/* Center glass circle */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-52 h-52 rounded-full bg-gradient-to-br from-white/15 to-white/5 border border-white/20 backdrop-blur-sm flex items-center justify-center shadow-2xl">
                  {/* Central drone icon */}
                  <svg className="w-24 h-24 text-white/90 animate-drone-hover" viewBox="0 0 100 100" fill="none">
                    {/* Central body */}
                    <circle cx="50" cy="50" r="10" fill="white" opacity="0.95" />
                    <circle cx="50" cy="50" r="6" fill="#10B981" opacity="0.7" />
                    {/* Arms */}
                    <line x1="20" y1="50" x2="40" y2="50" stroke="white" strokeWidth="1.5" opacity="0.8" />
                    <line x1="60" y1="50" x2="80" y2="50" stroke="white" strokeWidth="1.5" opacity="0.8" />
                    <line x1="50" y1="20" x2="50" y2="40" stroke="white" strokeWidth="1.5" opacity="0.8" />
                    <line x1="50" y1="60" x2="50" y2="80" stroke="white" strokeWidth="1.5" opacity="0.8" />
                    {/* Rotors */}
                    <circle cx="20" cy="50" r="8" fill="none" stroke="white" strokeWidth="1" opacity="0.5" />
                    <circle cx="80" cy="50" r="8" fill="none" stroke="white" strokeWidth="1" opacity="0.5" />
                    <circle cx="50" cy="20" r="8" fill="none" stroke="white" strokeWidth="1" opacity="0.5" />
                    <circle cx="50" cy="80" r="8" fill="none" stroke="white" strokeWidth="1" opacity="0.5" />
                  </svg>
                </div>

                {/* Orbiting small elements */}
                <div className="absolute top-[15%] left-[18%] w-10 h-10 bg-white/15 rounded-2xl backdrop-blur-md border border-white/25 flex items-center justify-center animate-float shadow-lg" style={{ animationDelay: '0.4s' }}>
                  <div className="w-3 h-3 rounded-full bg-white/80" />
                </div>
                <div className="absolute top-[10%] right-[20%] w-8 h-8 bg-white/12 rounded-xl backdrop-blur-md border border-white/20 flex items-center justify-center animate-float shadow-lg" style={{ animationDelay: '1.8s' }}>
                  <div className="w-2.5 h-2.5 rounded-full bg-agri-200/80" />
                </div>
                <div className="absolute bottom-[20%] right-[16%] w-12 h-12 bg-white/15 rounded-2xl backdrop-blur-md border border-white/25 flex items-center justify-center animate-float shadow-lg" style={{ animationDelay: '0.9s' }}>
                  <div className="w-3.5 h-3.5 rounded-full bg-white/70" />
                </div>
                <div className="absolute bottom-[22%] left-[20%] w-9 h-9 bg-white/12 rounded-xl backdrop-blur-md border border-white/20 flex items-center justify-center animate-float shadow-lg" style={{ animationDelay: '2.3s' }}>
                  <div className="w-2 h-2 rounded-full bg-emerald-300/80" />
                </div>

                {/* Drone dots along orbit paths */}
                <div className="absolute top-[28%] right-[6%] w-2 h-2 rounded-full bg-white/70 shadow-glow-sm" />
                <div className="absolute bottom-[32%] left-[5%] w-1.5 h-1.5 rounded-full bg-white/50" />
                <div className="absolute top-[14%] left-[35%] w-2 h-2 rounded-full bg-agri-200/60" />
                <div className="absolute bottom-[16%] right-[32%] w-1.5 h-1.5 rounded-full bg-white/60" />

                {/* Pulse rings */}
                <div className="absolute top-[28%] right-[6%] w-4 h-4 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/30 animate-ring-expand" />
                <div className="absolute bottom-[32%] left-[5%] w-3 h-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/20 animate-ring-expand" style={{ animationDelay: '1s' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2.5">
        <span className="text-white/40 text-xs tracking-widest uppercase">Scroll</span>
        <svg className="w-5 h-5 text-white/40 animate-soft-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  )
}
