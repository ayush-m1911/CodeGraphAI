/**
 * Purpose:
 * Implements a layout calculation utility to position nodes on the canvas.
 *
 * Responsibilities:
 * - Position nodes dynamically using tree hierarchy depth levels.
 * - Group child nodes under their parent paths to minimize overlapping edge crossings.
 *
 * Inputs:
 * - nodes (array): Collected list of node elements.
 * - edges (array): List of relation links.
 *
 * Outputs:
 * - array: Array of nodes populated with { position: { x, y } } coordinate sets.
 */

export function layoutGraphNodes(nodes, edges) {
  if (!nodes || nodes.length === 0) return [];

  const depthGroups = {};
  
  // Group nodes by hierarchy depth
  nodes.forEach(node => {
    // Read hierarchy_depth (defaulting to 3 for standard symbols if missing)
    const depth = node.hierarchy_depth !== undefined ? node.hierarchy_depth : 3;
    depthGroups[depth] = depthGroups[depth] || [];
    depthGroups[depth].push(node);
  });
  
  const arrangedNodes = [];
  const levelYGap = 180; // Vertical distance between layers
  const nodeXGap = 260;  // Horizontal distance between sibling nodes
  
  Object.keys(depthGroups).forEach(depthStr => {
    const depth = parseInt(depthStr, 10);
    const levelNodes = depthGroups[depth];
    
    // Sort nodes by parent ID to group child entities below parent nodes
    levelNodes.sort((a, b) => {
      const parentA = a.parent || '';
      const parentB = b.parent || '';
      return parentA.localeCompare(parentB);
    });
    
    const totalWidth = (levelNodes.length - 1) * nodeXGap;
    const startX = -totalWidth / 2;
    
    levelNodes.forEach((node, idx) => {
      arrangedNodes.push({
        id: node.id,
        type: node.node_type || node.type || 'file',
        // Pass complete node attributes to node.data for custom React Flow rendering
        data: { ...node },
        position: {
          x: startX + idx * nodeXGap,
          y: depth * levelYGap
        }
      });
    });
  });
  
  return arrangedNodes;
}
