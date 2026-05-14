import { useState, useEffect, useRef } from 'react'

export function useCountUp(end, duration = 2000, startOnView = true) {
  const [count, setCount] = useState(0)
  const [started, setStarted] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!startOnView) {
      setStarted(true)
    }
  }, [startOnView])

  useEffect(() => {
    if (!started) return
    let startTime = null
    let animFrame

    const step = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(eased * end))
      if (progress < 1) {
        animFrame = requestAnimationFrame(step)
      }
    }

    animFrame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animFrame)
  }, [end, duration, started])

  return { count, ref, start: () => setStarted(true) }
}
