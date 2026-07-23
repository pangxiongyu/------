import { useState, useEffect, useRef } from 'react';
function usecountup(end, duration = 2000, startonview = true) {
  const [count, setcount] = useState(0);
  const [started, setstarted] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    if (!startonview) {
      setstarted(true);
    }
  }, [startonview]);
  useEffect(() => {
    if (!started) return;
    let starttime = null;
    let animframe;
    const step = timestamp => {
      if (!starttime) starttime = timestamp;
      const progress = Math.min((timestamp - starttime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setcount(Math.floor(eased * end));
      if (progress < 1) {
        animframe = requestAnimationFrame(step);
      }
    };
    animframe = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animframe);
  }, [end, duration, started]);
  return {
    count,
    ref,
    start: () => setstarted(true)
  };
}
export { usecountup };
