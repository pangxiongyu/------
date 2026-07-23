import { forwardRef } from 'react';
const GlassCard = forwardRef(function GlassCard({
  children,
  className: classname = '',
  hover = true,
  variant = 'default',
  glow = false,
  shimmer = false
}, ref) {
  const base = variant === 'premium' ? 'glass-card-premium' : 'bg-white/80 backdrop-blur-md border border-white/40 shadow-lg rounded-2xl';
  const hoverclass = hover && variant !== 'premium' ? 'transition-all duration-300 hover:shadow-xl hover:-translate-y-1' : '';
  const glowclass = glow ? 'glow-border' : '';
  const shimmerclass = shimmer ? 'shimmer-overlay' : '';
  return <div ref={ref} className={`${base} ${hoverclass} ${glowclass} ${shimmerclass} ${classname}`}>
      {children}
    </div>;
});
export default GlassCard;
