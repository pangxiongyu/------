import { motion } from 'framer-motion';
export default function PageContainer({
  children,
  className: classname = ''
}) {
  return <motion.div initial={{
    opacity: 0,
    y: 16
  }} animate={{
    opacity: 1,
    y: 0
  }} exit={{
    opacity: 0,
    y: -16
  }} transition={{
    duration: 0.35,
    ease: 'easeOut'
  }} className={`min-h-screen pt-16 relative ${classname}`}>
      {/* 顶部渐变条 */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-agri-300/30 to-transparent pointer-events-none" />
      {children}
    </motion.div>;
}
