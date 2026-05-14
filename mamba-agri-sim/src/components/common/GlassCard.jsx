import { forwardRef } from 'react'

const GlassCard = forwardRef(function GlassCard({
  children,
  className = '',
  hover = true,
  variant = 'default',
  glow = false,
  shimmer = false,
}, ref) {

  const base = variant === 'premium'
    ? 'glass-card-premium'
    : 'bg-white/80 backdrop-blur-md border border-white/40 shadow-lg rounded-2xl'

  const hoverClass = hover && variant !== 'premium'
    ? 'transition-all duration-300 hover:shadow-xl hover:-translate-y-1'
    : ''

  const glowClass = glow ? 'glow-border' : ''
  const shimmerClass = shimmer ? 'shimmer-overlay' : ''

  return (
    <div
      ref={ref}
      className={`${base} ${hoverClass} ${glowClass} ${shimmerClass} ${className}`}
    >
      {children}
    </div>
  )
})

export default GlassCard
