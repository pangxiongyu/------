import { motion } from 'framer-motion';
export default function SectionTitle({
  title,
  subtitle,
  light = false,
  badge
}) {
  return <motion.div initial={{
    opacity: 0,
    y: 24
  }} whileInView={{
    opacity: 1,
    y: 0
  }} viewport={{
    once: true,
    margin: '-60px'
  }} transition={{
    duration: 0.5,
    ease: 'easeOut'
  }} className="text-center mb-14">
      {badge && <span className="inline-block mb-4 px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide uppercase bg-agri-100 text-agri-700 border border-agri-200/50">
          {badge}
        </span>}

      <div className="flex items-center justify-center gap-3 mb-4">
        <span className="hidden sm:block w-8 h-[2px] rounded-full bg-gradient-to-r from-transparent to-agri-400" />
        <h2 className={`text-3xl md:text-4xl font-black ${light ? 'text-white' : 'text-dark'}`}>
          {title}
        </h2>
        <span className="hidden sm:block w-8 h-[2px] rounded-full bg-gradient-to-l from-transparent to-agri-400" />
      </div>

      {subtitle && <p className={`text-lg max-w-2xl mx-auto leading-relaxed ${light ? 'text-white/70' : 'text-gray-500'}`}>
          {subtitle}
        </p>}
    </motion.div>;
}
