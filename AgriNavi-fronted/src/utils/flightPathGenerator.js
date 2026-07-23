function generatewaypoints(start, end, numpoints = 8) {
  const points = [];
  for (let i = 0; i <= numpoints; i++) {
    const t = i / numpoints;
    const x = start.x + (end.x - start.x) * t;
    const z = start.z + (end.z - start.z) * t;
    const basey = start.y + (end.y - start.y) * t;
    const arc = Math.sin(t * Math.PI) * 8;
    const y = basey + arc + 3;
    points.push({
      x,
      y,
      z
    });
  }
  return points;
}
export { generatewaypoints };
function interpolatewaypoints(waypoints, numsegments = 100) {
  const result = [];
  for (let i = 0; i < waypoints.length - 1; i++) {
    const p0 = waypoints[i];
    const p1 = waypoints[i + 1];
    for (let j = 0; j < numsegments; j++) {
      const t = j / numsegments;
      result.push({
        x: p0.x + (p1.x - p0.x) * t,
        y: p0.y + (p1.y - p0.y) * t,
        z: p0.z + (p1.z - p0.z) * t
      });
    }
  }
  result.push(waypoints[waypoints.length - 1]);
  return result;
}
export { interpolatewaypoints };
