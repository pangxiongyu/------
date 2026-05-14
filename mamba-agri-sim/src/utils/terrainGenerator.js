class SimplexNoise {
  constructor(seed = 42) {
    this.grad3 = [[1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
                  [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
                  [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]]
    this.perm = this.buildPerm(seed)
  }

  buildPerm(seed) {
    let p = []
    for (let i = 0; i < 256; i++) p[i] = i
    for (let i = 255; i > 0; i--) {
      seed = (seed * 16807 + 0) % 2147483647
      let j = seed % (i + 1)
      ;[p[i], p[j]] = [p[j], p[i]]
    }
    return [...p, ...p]
  }

  dot(g, x, y) { return g[0] * x + g[1] * y }

  noise2D(xin, yin) {
    let s = (xin + yin) * 0.3660254037844386
    let i = Math.floor(xin + s), j = Math.floor(yin + s)
    let t = (i + j) * 0.21132486540518713
    let X0 = i - t, Y0 = j - t
    let x0 = xin - X0, y0 = yin - Y0
    let i1 = x0 > y0 ? 1 : 0, j1 = x0 > y0 ? 0 : 1
    let x1 = x0 - i1 + 0.21132486540518713
    let y1 = y0 - j1 + 0.21132486540518713
    let x2 = x0 - 1 + 2 * 0.21132486540518713
    let y2 = y0 - 1 + 2 * 0.21132486540518713
    let ii = i & 255, jj = j & 255
    let n0 = this.dot(this.grad3[this.perm[ii + this.perm[jj]] % 12], x0, y0)
    let n1 = this.dot(this.grad3[this.perm[ii + i1 + this.perm[jj + j1]] % 12], x1, y1)
    let n2 = this.dot(this.grad3[this.perm[ii + 1 + this.perm[jj + 1]] % 12], x2, y2)
    return 70 * (n0 + n1 + n2)
  }

  fbm(x, y, octaves = 4, lacunarity = 2.0, gain = 0.5) {
    let value = 0, amplitude = 1, frequency = 1, maxValue = 0
    for (let i = 0; i < octaves; i++) {
      value += amplitude * this.noise2D(x * frequency, y * frequency)
      maxValue += amplitude
      amplitude *= gain
      frequency *= lacunarity
    }
    return value / maxValue
  }
}

const noise = new SimplexNoise(137)

export function generateHeightmap(width, depth, resolution, scale = 0.04) {
  const heights = new Float32Array(resolution * resolution)
  for (let iz = 0; iz < resolution; iz++) {
    for (let ix = 0; ix < resolution; ix++) {
      const x = (ix / (resolution - 1) - 0.5) * width
      const z = (iz / (resolution - 1) - 0.5) * depth
      let h = noise.fbm(x * scale, z * scale, 4, 2.0, 0.5)
      h = h * 0.5 + 0.5
      h = Math.pow(h, 1.5)
      h *= 15
      heights[iz * resolution + ix] = h
    }
  }
  return heights
}

export function getHeightAt(heights, resolution, ix, iz) {
  ix = Math.max(0, Math.min(resolution - 1, Math.round(ix)))
  iz = Math.max(0, Math.min(resolution - 1, Math.round(iz)))
  return heights[iz * resolution + ix]
}

export function getTerrainColor(height, maxHeight = 15) {
  const t = height / maxHeight
  if (t < 0.15) return [0.18, 0.55, 0.2]   // dark green (valley/grass)
  if (t < 0.35) return [0.25, 0.6, 0.18]    // green (grassland)
  if (t < 0.55) return [0.35, 0.5, 0.15]    // olive (hillside)
  if (t < 0.70) return [0.45, 0.4, 0.2]     // brown (rocky)
  if (t < 0.85) return [0.55, 0.5, 0.4]     // gray-brown
  return [0.75, 0.75, 0.8]                   // gray-white (peak)
}
